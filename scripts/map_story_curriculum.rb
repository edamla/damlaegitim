#!/usr/bin/env ruby
# frozen_string_literal: true

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

module MapStoryCurriculum
  module_function

  ANATEMA_KEYWORDS = {
    /değer|erdem|ahlak|etik|karakter/i => %w[Saygı Sorumluluk Dürüstlük Sevgi Dostluk],
    /saygı|saygi/i => ['Saygı'],
    /sevgi|aşk|ask/i => ['Sevgi'],
    /dostluk|arkadaş|arkadas/i => ['Dostluk', 'Empati'],
    /cesaret|kahraman/i => ['Cesaret', 'Azim ve Kararlılık', 'Kendine Güvenme (Öz Güven)'],
    /empati|duygu|duyar/i => %w[Empati Duyarlılık Merhamet],
    /doğa|doga|çevre|cevre|hayvan/i => %w[Duyarlılık Estetik Merak],
    /macera|keşif|kesif|gezi/i => ['Merak', 'Gerçeği Arama'],
    /dedektif|gizem|polisiye|sır|sir/i => %w[Muhakeme Analitiklik Soru\ Sorma],
    /atatürk|tarih|vatan|milli|kurtuluş|kurtulus/i => %w[Vatanseverlik Saygı Özgürlük],
    /okuma|kitap/i => %w[Merak Odaklanma],
    /aile|kardeş|kardes/i => ['Aile Bütünlüğü', 'Sevgi', 'Saygı'],
    /yardım|iyilik|paylaş|paylas/i => %w[Merhamet Dostluk Sorumluluk]
  }.freeze

  UNITE_KEYWORDS = {
    /değer|erdem|ahlak|etik|karakter|hikâyelerle|hikayelerle/i => [
      'Değerlerimizle Varız', 'Güzel Davranışlarımız', 'Duygularımı Tanıyorum',
      'İletişim Ve Sosyal İlişkiler', 'Geleneklerimiz'
    ],
    /atatürk|mustafa kemal/i => ["Atatürk Ve Çocuk", "Atatürk'ü Tanımak", "Mustafa Kemal'den Atatürk'e"],
    /doğa|doga|çevre|cevre|hayvan/i => ['Doğada Neler Oluyor?', 'Çevremizdeki Yaşam', 'Sağlıklı Yaşıyorum'],
    /macera|keşif|kesif|gezi|seyahat/i => ['Oyun Dünyası', 'Minik Kâşifler', 'Farklı Dünyalar'],
    /okuma|kitap/i => ['Yol Arkadaşımız Kitaplar', 'Okuma Serüvenimiz'],
    /dedektif|gizem|polisiye/i => ['Oyun Dünyası', 'Farklı Dünyalar', 'Bilim Ve Teknoloji'],
    /tarih|vatan|milli/i => ['Atalarımızın İzleri', 'Bağımsızlık Yolu', 'Geleneklerimiz'],
    /bilim|teknoloji|icat|fen/i => ['Bilim Ve Teknoloji', 'Minik Kâşifler', 'Mucit Çocuk'],
    /duygu|empati/i => ['Duygularımı Tanıyorum', 'İletişim Ve Sosyal İlişkiler'],
    /yetenek|beceri/i => ['Yeteneklerimizi Tanıyoruz', 'Yeteneklerimizi Keşfediyoruz']
  }.freeze

  BECERI_HINTS = {
    /dedektif|gizem|analiz|muhakeme/i => ['Eleştirel Düşünme Becerisi', 'Problem Çözme Becerisi', 'Çıkarım Yapma Becerisi'],
    /macera|okuma/i => ['Okuma Becerisi', 'Dinleme/İzleme Becerisi'],
    /değer|erdem/i => ['Konuşma Becerisi', 'Yazma Becerisi', 'Kendini Tanıma (Öz Farkındalık Becerisi)'],
    /doğa|doga/i => ['Gözlemleme Becerisi', 'Bilgi Toplama Becerisi']
  }.freeze

  def collect_hints(texts)
    hints = { anatema: [], unite: [], beceriler: [] }
    joined = texts.join(' ')
    ANATEMA_KEYWORDS.each { |pattern, values| hints[:anatema].concat(values) if joined.match?(pattern) }
    UNITE_KEYWORDS.each { |pattern, values| hints[:unite].concat(values) if joined.match?(pattern) }
    BECERI_HINTS.each { |pattern, values| hints[:beceriler].concat(values) if joined.match?(pattern) }
    hints.transform_values { |v| v.uniq }
  end

  def merge_grade_unites(tymm, grades)
    unites = []
    grades.each do |grade|
      grade_data = tymm.dig('grades', grade)
      next unless grade_data

      unites.concat(grade_data['unites'] || [])
    end
    unites
  end

  def score_unite(unite, hints, context)
    label = unite['label']
    score = 0.0
    score += 3.0 if hints[:unite].any? { |h| CurriculumLib.overlap_score(h, label) > 0.4 }
    score += CurriculumLib.overlap_score(context, label) * 2
    all_items = (unite['degerler'] || []) + (unite['egilimler'] || [])
    hints[:anatema].each do |hint|
      all_items.each { |item| score += 1.5 if CurriculumLib.overlap_score(hint, item) > 0.5 }
    end
    score
  end

  def pick_unites(unites, hints, context, max: 4)
    scored = unites.map { |u| [u, score_unite(u, hints, context)] }
                   .select { |_, s| s.positive? }
                   .sort_by { |_, s| -s }
    picked = scored.first(max)&.map(&:first) || []
    return picked unless picked.empty?

    unites.first(2)
  end

  def derive_fields(unites, hints)
    anatema = hints[:anatema].dup
    beceriler = hints[:beceriler].dup
    unite_labels = []

    unites.each do |u|
      unite_labels << u['label']
      anatema.concat(u['degerler'] || [])
      anatema.concat(u['egilimler'] || [])
      beceriler.concat(u['beceriler'] || [])
    end

    {
      'unite' => unite_labels.uniq.first(6),
      'anatema' => anatema.uniq.first(12),
      'beceriler' => beceriler.uniq.first(10)
    }
  end

  def map_book(book, tymm)
    fm = book[:fm]
    grades = Array(fm['grades']).map(&:to_s)
    context_parts = Array(fm['tags']) + Array(fm['anatemalar']) + Array(fm['categories'])
    context = context_parts.join(' ')
    hints = collect_hints(context_parts)
    unites = merge_grade_unites(tymm, grades)
    picked = pick_unites(unites, hints, context)
    derive_fields(picked, hints)
  end
end

require 'csv'

ROOT = CurriculumLib::ROOT
REPORT = ROOT.join('docs', 'curriculum-mapping-report.csv')

def main
  tymm = CurriculumLib.load_tymm
  report_rows = []

  CurriculumLib.story_books.each do |book|
    fields = MapStoryCurriculum.map_book(book, tymm)
    write_frontmatter_fields(book[:path], fields)
    report_rows << [
      book[:path].basename.to_s,
      fields['unite'].size,
      fields['anatema'].size,
      fields['beceriler'].size,
      fields['unite'].empty? ? 'low' : 'ok'
    ]
    puts "  #{book[:path].basename} → unite:#{fields['unite'].size} anatema:#{fields['anatema'].size}"
  end

  CSV.open(REPORT, 'w', write_headers: true, headers: %w[file unite_count anatema_count beceriler_count confidence]) do |csv|
    report_rows.each { |row| csv << row }
  end
  puts "Rapor: #{REPORT}"
end

main if $PROGRAM_NAME == __FILE__