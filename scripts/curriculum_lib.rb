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

  def load_tymm_yml
    YAML.load_file(ROOT.join('_data', 'tymm.yml'))
  end

  def load_oykumatik_yml
    YAML.load_file(ROOT.join('_data', 'oykumatik-kazanimlari.yml'))
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
end
