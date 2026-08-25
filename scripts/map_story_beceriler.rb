#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative 'curriculum_lib'

module MapStoryBeceriler
  module_function

  MAX_BECERI = 6

  KEYWORD_HINTS = {
    /dedektif|gizem|analiz|muhakeme|polisiye/i => [
      'Eleştirel Düşünme Becerisi', 'Problem Çözme Becerisi', 'Çıkarım Yapma Becerisi'
    ],
    /macera|okuma|kitap/i => ['Okuma Becerisi', 'Dinleme/İzleme Becerisi'],
    /değer|erdem|ahlak/i => [
      'Konuşma Becerisi', 'Yazma Becerisi', 'Kendini Tanıma (Öz Farkındalık Becerisi)'
    ],
    /doğa|doga|çevre|hayvan/i => ['Gözlemleme Becerisi', 'Bilgi Toplama Becerisi'],
    /tarih|vatan|kültür|kultur/i => ['Kültür Okuryazarlığı', 'Okuma Becerisi'],
    /bilim|teknoloji|uzay|robot/i => ['Bilgi Okuryazarlığı', 'Dijital Okuryazarlık'],
    /duygu|empati/i => ['Kendini Tanıma (Öz Farkındalık Becerisi)', 'İletişim Becerisi']
  }.freeze

  FALLBACK = ['Okuma Becerisi', 'Dinleme/İzleme Becerisi', 'Konuşma Becerisi'].freeze

  def unit_boost(unite_labels)
    lambda do |label, score|
      unite_labels.each do |unite|
        (unite['beceriler'] || []).each do |item|
          norm_item = CurriculumLib.normalize_beceri(item)
          norm_label = CurriculumLib.normalize_beceri(label)
          if CurriculumLib.exact_label_match?(norm_item, norm_label) ||
             CurriculumLib.overlap_score(norm_item, norm_label) > 0.6
            score += 6
          end
        end
      end
      score
    end
  end

  def map_book(book, beceriler, picked_unites: [])
    corpus = CurriculumLib.build_story_corpus(book, extra_fields: %w[tags anatema degerler egilimler])
    boost = unit_boost(picked_unites)

    picked = CurriculumLib.pick_top_labels(
      corpus,
      book[:fm],
      beceriler,
      keyword_hints: KEYWORD_HINTS,
      max: MAX_BECERI,
      label_boost: boost,
      fallback: FALLBACK & beceriler
    )
    { 'beceriler' => picked }
  end
end
