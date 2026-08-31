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

  LEGACY_LABELS = %w[TEMALAR KAZANIMLAR ETİKETLER].freeze
  LEGACY_LABEL_ALT = LEGACY_LABELS.join('|').freeze
  SET_HEADING_PATTERN = /
    (?:
      \*{0,2}Setin\s+İçerdiği\s+(?:Kitaplar|Hikayeler)(?:\*{1,2})?[ \t]*[:;]?(?:\*{1,2})?
      |[^\n]*Setin\s+İçerdiği\s+(?:Kitaplar|Hikayeler)[^\n]*
    )
  /ix.freeze

  def strip_labeled_blocks(body)
    text = body.to_s.dup
    text = strip_legacy_html_comments(text)
    text = strip_inline_metadata_chain(text)

    5.times do
      before = text
      LEGACY_LABELS.each { |label| text = strip_single_label_block(text, label) }
      break if text == before
    end

    normalize_body_whitespace(text)
  end

  def strip_legacy_html_comments(body)
    body.to_s.gsub(/<!--.*?-->/m) do |comment|
      comment.match?(/TEMALAR|KAZANIMLAR|ETİKETLER/i) ? '' : comment
    end
  end

  def strip_inline_metadata_chain(body)
    body.to_s.gsub(
      /\s+\*{0,2}TEMALAR\*{0,2}\s*[:;]?\s*(?:•\s*)?.*?\*{0,2}ETİKETLER\*{0,2}\s*[:;]?\s*(?:•\s*)?.*?(?=\s+(?:\*{0,2})?Setin\s+İçerdiği\b)/mi,
      ''
    )
  end

  def strip_single_label_block(text, label)
    others = (LEGACY_LABELS - [label]).join('|')
    stop_line = /
      \s*\*{0,2}(?:#{others})\*{0,2}\s*[:;]?
      |\s*\*{0,2}Setin\s+İçerdiği\b
      |\s*Setin\s+İçerdiği\b
      |\s*KİTAPLAR\s*;
    /ix

    pattern = /
      (?:^|\n)
      \s*\*{0,2}#{label}\*{0,2}\s*[:;]?\s*
      (?:
        [^\n]*
        (?:
          \n
          (?!#{stop_line})
          (?:
            -\s+[^\n]+
            |[^\n]+
          )
        )*
      )?
    /mix

    text.gsub(pattern, "\n")
  end

  def normalize_body_whitespace(text)
    text.to_s
        .gsub(/[ \t]+\n/, "\n")
        .gsub(/\n{3,}/, "\n\n")
        .strip
  end

  def extract_set_section_items(section_text)
    section_text.to_s
                .gsub(/<br\s*\/?>/i, "\n")
                .scan(/\d+[\-\.]\s*([^\n<]+)/)
                .map { |m| normalize_tr(m[0]) }
                .reject(&:empty?)
  end

  def set_section_quality(section_text)
    score = 0
    score += 10 if section_text.match?(/\*\*Setin\s+İçerdiği/i)
    score -= 8 if section_text.match?(/\A[^\n*]*Setin\s+İçerdiği[^*]*\*\*/i)
    score += section_text.count("\n")
    score -= section_text.scan(/<br>/i).size
    score
  end

  def dedupe_set_sections(body)
    text = dedupe_structured_set_sections(body)
    dedupe_inline_set_lines(text)
  end

  def dedupe_structured_set_sections(body)
    text = body.to_s.dup
    pattern = /
      (?:^|\n)
      #{SET_HEADING_PATTERN.source}
      (?:
        \n\s*
        (?:
          \d+[\-\.]\s*[^\n]+(?:<br>)?
          |-\s+[^\n]+
        )
      )*
    /mix

    sections = []
    text.to_enum(:scan, pattern).each do
      match = Regexp.last_match
      sections << { start: match.begin(0), end: match.end(0), text: match[0], items: extract_set_section_items(match[0]) }
    end
    return text if sections.size < 2

    groups = sections.group_by { |s| s[:items].join('|') }
    remove_ranges = []
    groups.each_value do |group|
      next if group.size < 2
      next if group.first[:items].empty?

      keeper = group.max_by { |s| set_section_quality(s[:text]) }
      group.each do |section|
        next if section.equal?(keeper)

        remove_ranges << [section[:start], section[:end]]
      end
    end

    return text if remove_ranges.empty?

    remove_ranges.sort_by! { |start, _| -start }
    remove_ranges.each do |start, finish|
      text[start...finish] = ''
    end

    normalize_body_whitespace(text)
  end

  def dedupe_inline_set_lines(body)
    text = body.to_s.dup
    fingerprints = {}
    ranges_to_remove = []

    text.to_enum(:scan, /Setin\s+İçerdiği\s+(?:Kitaplar|Hikayeler)[^\n]*/i).each do
      match = Regexp.last_match
      segment = match[0]
      items = extract_set_section_items(segment)
      next if items.empty?

      key = items.join('|')
      range = (match.begin(0)...match.end(0))
      if fingerprints.key?(key)
        prev = fingerprints[key]
        keep_range = better_set_range(prev[:range], prev[:text], range, segment)
        remove_range = keep_range == range ? prev[:range] : range
        ranges_to_remove << remove_range
        next if keep_range == range

        fingerprints[key] = { range: range, text: segment }
      else
        fingerprints[key] = { range: range, text: segment }
      end
    end

    ranges_to_remove.sort_by { |r| -r.begin }.uniq.each do |range|
      text[range] = ''
    end

    normalize_body_whitespace(text)
  end

  def better_set_range(range_a, text_a, range_b, text_b)
    score_a = inline_set_quality(text_a, range_a)
    score_b = inline_set_quality(text_b, range_b)
    score_b > score_a ? range_b : range_a
  end

  def inline_set_quality(segment, range)
    score = set_section_quality(segment)
    score += 5 if segment.match?(/\A\*{2}Setin/i)
    score -= 3 if segment.match?(/\A[^\n*]*Setin[^\n]*\*\*\s*\z/)
    score -= 2 if range && range.begin.positive? && !segment.match?(/\A\n/)
    score
  end

  def clean_book_body(body)
    dedupe_set_sections(strip_labeled_blocks(body))
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

  def write_book_body(path, cleaned_body)
    content = path.read
    match = content.match(/\A(---\r?\n.*?\r?\n---\r?\n)(.*)\z/m)
    raise "Frontmatter bulunamadı: #{path}" unless match

    body = cleaned_body
    body += "\n" unless body.end_with?("\n")
    path.write("#{match[1]}#{body}")
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
