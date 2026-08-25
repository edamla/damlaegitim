#!/usr/bin/env ruby
# frozen_string_literal: true

require 'json'
require 'csv'
require 'yaml'
require_relative 'curriculum_lib'

def write_frontmatter_fields(path, updates)
  content = path.read
  fm, body = CurriculumLib.parse_frontmatter(content)
  updates.each { |key, value| fm[key] = value }
  yaml = YAML.dump(fm)
  yaml = yaml.sub(/\A---\n/, '')
  path.write("---\n#{yaml}---\n#{body}")
end

module MapStoryDegerler
  module_function

  DEGERLER_PATH = CurriculumLib::ROOT.join('docs', 'TYMM', 'tymm-degerler.json').freeze
  MAX_DEGER = 6

  KEYWORD_HINTS = {
    /sayg[ıi]/i => ['Saygı'],
    /sevgi|aşk|ask/i => ['Sevgi'],
    /dostluk|arkadaş|arkadas/i => ['Dostluk'],
    /empati|duygu|duyar/i => %w[Duyarlılık Merhamet],
    /doğa|doga|çevre|cevre|hayvan|geri dönüşüm|cevreci/i => %w[Duyarlılık Estetik Temizlik],
    /macera|keşif|kesif|gezi|seyahat/i => %w[Dostluk Özgürlük Sorumluluk],
    /dedektif|gizem|polisiye|sır|sir/i => %w[Dürüstlük Sorumluluk Adalet],
    /atatürk|tarih|vatan|milli|kurtuluş|kurtulus|canakkale|istiklal/i => %w[Vatanseverlik Saygı Özgürlük],
    /aile|kardeş|kardes|anne|baba|dede/i => ['Aile Bütünlüğü', 'Sevgi', 'Saygı'],
    /yardım|iyilik|paylaş|paylas|merhamet/i => %w[Yardımseverlik Merhamet Dostluk],
    /adalet|hakkaniyet|eşitlik|esitlik/i => ['Adalet'],
    /dürüstlük|durustluk|doğruluk|dogruluk|ahlak|etik|erdem|değer|deger/i => %w[Dürüstlük Saygı Sorumluluk],
    /cesaret|kahraman|özgürlük|ozgurluk/i => %w[Özgürlük Sabır Sorumluluk],
    /temizlik|hijyen/i => ['Temizlik'],
    /tasarruf|tutumlu/i => ['Tasarruf'],
    /çalışkan|caliskan|azim|disiplin/i => ['Çalışkanlık'],
    /sağlık|saglik|spor|beslen/i => ['Sağlıklı Yaşam'],
    /sanat|estetik|müzik|muzik|resim/i => ['Estetik'],
    /sabır|sabir|sakin/i => ['Sabır'],
    /mahremiyet|özel alan|ozel alan/i => ['Mahremiyet'],
    /mütevazi|mutevazi|kibir/i => ['Mütevazılık']
  }.freeze

  FALLBACK = %w[Saygı Sorumluluk Sevgi].freeze

  def load_degerler
  data = JSON.parse(DEGERLER_PATH.read)
  degerler = data['degerler'].map do |d|
    {
      ad: d['ad'],
      kod: d['kod'],
      aciklama: d['aciklama'],
      keywords: keyword_tokens(d['ad'], d['aciklama'])
    }
  end
  [degerler, data['degerler'].map { |d| d['ad'] }]
  end

  def keyword_tokens(ad, aciklama)
    tokens = CurriculumLib.token_set("#{ad} #{aciklama}")
    tokens.reject { |t| t.length < 4 }
  end

  def build_corpus(book)
    fm = book[:fm]
    body = book[:body].to_s
    temalar = body[/\*{0,2}TEMALAR\*{0,2}\s*:.*$/i]
    parts = [
      fm['title'],
      fm['description'],
      Array(fm['tags']).join(' '),
      Array(fm['anatema']).join(' '),
      Array(fm['categories']).join(' '),
      temalar,
      CurriculumLib.strip_labeled_blocks(body)
    ]
    parts.compact.join(' ')
  end

  def exact_match?(value, ad)
    norm_v = CurriculumLib.normalize_tr(value)
    norm_a = CurriculumLib.normalize_tr(ad)
    return true if norm_v == norm_a
    return true if norm_v.include?(norm_a) || norm_a.include?(norm_v)

    false
  end

  def score_deger(deger, corpus, fm)
    ad = deger[:ad]
    score = 0.0
    title_tags = [fm['title'], *Array(fm['tags'])].compact.join(' ')

    Array(fm['anatema']).each { |v| score += 10 if exact_match?(v, ad) }
    Array(fm['tags']).each { |v| score += 10 if exact_match?(v, ad) }

    score += 5 if exact_match?(title_tags, ad)
    score += 5 if CurriculumLib.normalize_tr(fm['title'].to_s).include?(CurriculumLib.normalize_tr(ad))

    deger[:keywords].each do |kw|
      score += 2 if CurriculumLib.normalize_tr(corpus).include?(kw)
    end

    KEYWORD_HINTS.each do |pattern, values|
      score += 3 if values.include?(ad) && corpus.match?(pattern)
    end

    score += CurriculumLib.overlap_score(corpus, ad) * 4
    score
  end

  def pick_degerler(book, degerler)
    fm = book[:fm]
    corpus = build_corpus(book)
    scored = degerler.map do |deger|
      [deger[:ad], score_deger(deger, corpus, fm)]
    end
    picked = scored.select { |_, s| s.positive? }
                   .sort_by { |_, s| -s }
                   .first(MAX_DEGER)
                   .map(&:first)

    return picked if picked.any?

    from_meta = (Array(fm['anatema']) + Array(fm['tags'])).uniq
    official = degerler.map { |d| d[:ad] }
    fallback = from_meta.select { |v| official.any? { |ad| exact_match?(v, ad) } }
    fallback = FALLBACK if fallback.empty?
    fallback.first(MAX_DEGER)
  end

  def map_book(book, degerler)
    { 'degerler' => pick_degerler(book, degerler) }
  end
end

ROOT = CurriculumLib::ROOT
REPORT = ROOT.join('docs', 'degerler-mapping-report.csv')

def main
  degerler, _official_order = MapStoryDegerler.load_degerler
  report_rows = []

  CurriculumLib.story_books.each do |book|
    fields = MapStoryDegerler.map_book(book, degerler)
    write_frontmatter_fields(book[:path], fields)
    scores = fields['degerler'].join('; ')
    report_rows << [book[:path].basename.to_s, fields['degerler'].size, scores]
    puts "  #{book[:path].basename} → degerler:#{fields['degerler'].size} [#{scores}]"
  end

  CSV.open(REPORT, 'w', write_headers: true, headers: %w[file count degerler]) do |csv|
    report_rows.each { |row| csv << row }
  end
  puts "Rapor: #{REPORT}"
end

main if $PROGRAM_NAME == __FILE__
