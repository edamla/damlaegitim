#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative 'curriculum_lib'

module MapStoryCurriculum
  module_function

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

  def collect_unite_hints(texts)
    hints = []
    joined = texts.join(' ')
    UNITE_KEYWORDS.each { |pattern, values| hints.concat(values) if joined.match?(pattern) }
    hints.uniq
  end

  def score_unite(unite, hints, context)
    label = unite['label']
    score = 0.0
    score += 3.0 if hints.any? { |h| CurriculumLib.overlap_score(h, label) > 0.4 }
    score += CurriculumLib.overlap_score(context, label) * 2
    score
  end

  def pick_unites(book, tymm, max: 4)
    fm = book[:fm]
    grades = Array(fm['grades']).map(&:to_s)
    context_parts = Array(fm['tags']) + Array(fm['categories']) + Array(fm['anatema'])
    context = context_parts.join(' ')
    hints = collect_unite_hints(context_parts)
    unites = CurriculumLib.merge_grade_unites(tymm, grades)

    scored = unites.map { |u| [u, score_unite(u, hints, context)] }
                   .select { |_, s| s.positive? }
                   .sort_by { |_, s| -s }
    picked = scored.first(max)&.map(&:first) || []
    return picked unless picked.empty?

    unites.first(2)
  end

  def map_book(book, tymm)
    picked = pick_unites(book, tymm)
    { 'unite' => picked.map { |u| u['label'] }.uniq.first(6) }
  end
end
