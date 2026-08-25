# frozen_string_literal: true

require 'json'
require 'yaml'
require 'pathname'
require 'cgi'
require 'date'

module CurriculumLib
  ROOT = Pathname.new(__dir__).join('..').expand_path
  BOOKS_DIR = ROOT.join('_books')

  DEGERLER_LABEL = 'Değerler'
  EGILIMLER_LABEL = 'Eğilimler'
  BECERI_LABELS = [
    'Alan Becerileri',
    'Okuryazarlık Becerileri',
    'Sosyal-Duygusal Öğrenme Becerileri',
    'Kavramsal Beceriler'
  ].freeze

  KAVRAMSAL_NAMES = {
    1 => 'Olay Örgüsü',
    2 => 'Zaman ve Mekân',
    3 => 'Şahıs ve Varlık Kadrosu',
    4 => 'Dil ve Anlatım'
  }.freeze

  BILISSEL_NAMES = {
    1 => 'Hatırlama Anlama',
    2 => 'Uygulama',
    3 => 'Çözümleme',
    4 => 'Değerlendirme'
  }.freeze

  module_function

  def parse_frontmatter(content)
    match = content.match(/\A---\r?\n(.*?)\r?\n---\r?\n(.*)\z/m)
    raise 'Frontmatter bulunamadı' unless match

    fm = YAML.safe_load(match[1], permitted_classes: [Date, Time], aliases: true) || {}
    [fm.transform_keys(&:to_s), match[2]]
  end

  def strip_labeled_blocks(body)
    text = body.to_s.dup
    %w[TEMALAR KAZANIMLAR ETİKETLER].each do |label|
      text.gsub!(/\*{0,2}#{label}\*{0,2}\s*:.*?(?=\n\*{0,2}[A-ZÇĞİÖŞÜ]|\z)/mi, "\n")
    end
    text.gsub(/\n{3,}/, "\n\n").strip
  end

  def titleize_unite(name)
    name.to_s.strip.gsub(/\s+/, ' ').split.map do |word|
      next word if word.match?(/\A[A-ZÇĞİÖŞÜ0-9]+\z/)

      word[0].upcase + word[1..].to_s.downcase
    end.join(' ')
  end

  def normalize_deger(text)
    text.to_s.sub(/\AD\d+\./, '').strip
  end

  def normalize_egilim(text)
    text.to_s.sub(/\AE\d+\.\d+\./, '').strip
  end

  def normalize_beceri(text)
    cleaned = text.to_s.strip
    cleaned = cleaned.sub(/\AOB\d+\.\s*/, '')
    cleaned = cleaned.sub(/\AKB\d+\.\d+\./, '')
    cleaned = cleaned.sub(/\ASDB\d+\.\d+\.\s*/, '')
    cleaned = cleaned.sub(/\AOB\.\s*/, '')
    cleaned = cleaned.sub(/\AKB\.\s*/, '')
    cleaned = cleaned.sub(/\ASDB\.\s*/, '')
    cleaned = cleaned.sub(/\s*\(TAB\d+\)\s*\z/, '')
    cleaned.gsub(/\s+/, ' ').strip
  end

  def decode_html(html)
    CGI.unescapeHTML(html.to_s)
         .gsub(/<br\s*\/?>/i, "\n")
         .gsub(/<\/p>/i, "\n")
         .gsub(/<\/li>/i, "\n")
         .gsub(/<[^>]+>/, '')
         .gsub("\u00a0", ' ')
         .gsub(/\r\n?/, "\n")
  end

  def parse_themes_from_html(html)
    text = decode_html(html)
    themes = {}
    current = nil
    text.each_line do |line|
      line = line.strip
      next if line.empty?

      if (m = line.match(/\A\d+\.\s*TEMA:\s*(.+)\z/i))
        current = titleize_unite(m[1])
        themes[current] ||= []
        next
      end
      next unless current

      themes[current] << line unless line.match?(/\ATEMA:/i)
    end
    themes.transform_values { |items| items.map(&:strip).reject(&:empty?).uniq }
  end

  def grade_from_chart_name(name)
    m = name.to_s.match(/\A(\d+)\./)
    m ? m[1] : nil
  end

  def load_tymm
    JSON.parse(ROOT.join('_data', 'tymm.json').read)
  end

  def load_degerler_cercevesi
    data = load_tymm
    cerceve = data.dig('cerceveler', 'degerler')
    raise 'cerceveler.degerler bulunamadı — python scripts/fetch_tymm.py --cerceveler && ruby scripts/build_tymm_reference.rb' unless cerceve

    cerceve
  end

  def story_books
    BOOKS_DIR.glob('*.md').sort.filter_map do |path|
      fm, body = parse_frontmatter(path.read)
      next unless fm['genre'] == 'story'

      { path: path, fm: fm, body: body }
    end
  end

  def normalize_tr(text)
    text.to_s.downcase
        .tr('çğıöşü', 'cgiosu')
        .gsub(/[^a-z0-9\s]/, ' ')
        .squeeze(' ')
        .strip
  end

  def token_set(text)
    normalize_tr(text).split.uniq
  end

  def overlap_score(a, b)
    sa = token_set(a)
    sb = token_set(b)
    return 0.0 if sa.empty? || sb.empty?

    (sa & sb).size.to_f / [sa.size, sb.size].min
  end

  def exact_label_match?(value, label)
    norm_v = normalize_tr(value)
    norm_a = normalize_tr(label)
    return true if norm_v == norm_a
    return true if norm_v.include?(norm_a) || norm_a.include?(norm_v)

    false
  end

  def build_story_corpus(book, extra_fields: [])
    fm = book[:fm]
    body = book[:body].to_s
    temalar = body[/\*{0,2}TEMALAR\*{0,2}\s*:.*$/i]
    parts = [
      fm['title'],
      fm['description'],
      Array(fm['tags']).join(' '),
      Array(fm['categories']).join(' '),
      temalar,
      strip_labeled_blocks(body)
    ]
    extra_fields.each do |field|
      parts << Array(fm[field]).join(' ')
    end
    parts.compact.join(' ')
  end

  def load_anatemalar
    data = JSON.parse(ROOT.join('_data', 'anatemalar.json').read)
    list = data['anatemalar']
    raise 'anatemalar.json listesi boş' unless list.is_a?(Array) && list.any?

    list
  end

  def flatten_egilimler(tymm = nil)
    tymm ||= load_tymm
    gruplar = tymm.dig('cerceveler', 'egilimler', 'gruplar') || []
    gruplar.flat_map { |g| (g['alt_kavramlar'] || []).map { |a| a['ad'] } }.compact.uniq
  end

  def flatten_beceriler(tymm = nil)
    tymm ||= load_tymm
    frameworks = tymm.dig('cerceveler', 'beceriler') || {}
    names = []
    frameworks.each_value do |framework|
      (framework['gruplar'] || []).each do |grup|
        (grup['alt_kavramlar'] || []).each do |alt|
          names << alt['ad'] if alt['ad']
        end
      end
    end
    names.uniq
  end

  def load_deger_adlari(tymm = nil)
    tymm ||= load_tymm
    (tymm.dig('cerceveler', 'degerler', 'degerler') || []).map { |d| d['ad'] }
  end

  def merge_grade_unites(tymm, grades)
    unites = []
    Array(grades).map(&:to_s).each do |grade|
      grade_data = tymm.dig('grades', grade)
      next unless grade_data

      unites.concat(grade_data['unites'] || [])
    end
    unites
  end

  def score_candidates(corpus, fm, candidates, keyword_hints:, label_boost: nil)
    scored = candidates.map do |label|
      score = 0.0
      title_tags = [fm['title'], *Array(fm['tags'])].compact.join(' ')

      Array(fm['tags']).each { |v| score += 10 if exact_label_match?(v, label) }
      Array(fm['categories']).each { |v| score += 6 if exact_label_match?(v, label) }
      score += 8 if exact_label_match?(title_tags, label)
      score += overlap_score(corpus, label) * 5

      keyword_hints.each do |pattern, values|
        score += 4 if values.include?(label) && corpus.match?(pattern)
      end

      label_boost&.call(label, score) || score
    end
    candidates.zip(scored).sort_by { |_, s| -s }
  end

  def pick_top_labels(corpus, fm, candidates, keyword_hints:, max:, label_boost: nil, fallback: [])
    ranked = score_candidates(corpus, fm, candidates, keyword_hints: keyword_hints, label_boost: label_boost)
    picked = ranked.select { |_, s| s.positive? }.first(max)&.map(&:first) || []
    return picked if picked.any?

    (fallback & candidates).first(max)
  end

  def write_frontmatter_fields(path, updates)
    content = path.read
    fm, body = parse_frontmatter(content)
    updates.each { |key, value| fm[key] = value }
    yaml = YAML.dump(fm)
    yaml = yaml.sub(/\A---\n/, '')
    path.write("---\n#{yaml}---\n#{body}")
  end
end
