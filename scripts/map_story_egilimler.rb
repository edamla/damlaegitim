#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative 'curriculum_lib'

module MapStoryEgilimler
  module_function

  MAX_EGILIM = 6

  KEYWORD_HINTS = {
    /saygı|saygi/i => ['Bağımsızlık'],
    /sevgi|aşk|ask/i => ['Empati'],
    /dostluk|arkadaş|arkadas/i => ['Empati', 'Güven'],
    /cesaret|kahraman/i => ['Azim ve Kararlılık', 'Kendine Güvenme (Öz Güven)'],
    /empati|duygu|duyar/i => ['Empati'],
    /doğa|doga|çevre|cevre|hayvan/i => ['Merak'],
    /macera|keşif|kesif|gezi/i => ['Merak', 'Gerçeği Arama'],
    /dedektif|gizem|polisiye|sır|sir/i => ['Muhakeme', 'Analitiklik', 'Soru Sorma'],
    /atatürk|tarih|vatan|milli/i => ['Sorumluluk', 'Güven'],
    /okuma|kitap/i => ['Merak', 'Odaklanma'],
    /aile|kardeş|kardes/i => ['Empati', 'Güven'],
    /yardım|iyilik|paylaş|paylas/i => ['Sorumluluk', 'Empati'],
    /bilim|teknoloji|icat|fen/i => ['Merak', 'Yaratıcılık'],
    /oyun|eğlence|eglence/i => ['Oyunseverlik']
  }.freeze

  FALLBACK = ['Merak', 'Empati', 'Sorumluluk'].freeze

  def unit_boost(unite_labels)
    lambda do |label, score|
      unite_labels.each do |unite|
        (unite['egilimler'] || []).each do |item|
          score += 6 if CurriculumLib.exact_label_match?(item, label)
        end
      end
      score
    end
  end

  def map_book(book, egilimler, picked_unites: [])
    corpus = CurriculumLib.build_story_corpus(book, extra_fields: %w[tags anatema degerler beceriler])
    boost = unit_boost(picked_unites)

    picked = CurriculumLib.pick_top_labels(
      corpus,
      book[:fm],
      egilimler,
      keyword_hints: KEYWORD_HINTS,
      max: MAX_EGILIM,
      label_boost: boost,
      fallback: FALLBACK & egilimler
    )
    { 'egilimler' => picked }
  end
end
