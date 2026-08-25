#!/usr/bin/env ruby
# frozen_string_literal: true

require 'json'
require 'csv'
require_relative 'curriculum_lib'

module MapStoryDegerler
  module_function

  CERCEVELER_PATH = CurriculumLib::ROOT.join('docs', 'data', 'tymm', 'cerceveler.json').freeze
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

  def load_degerler_source
    if CERCEVELER_PATH.file?
      data = JSON.parse(CERCEVELER_PATH.read)
      { 'degerler' => data.dig('degerler', 'degerler') }
    else
      cerceve = CurriculumLib.load_degerler_cercevesi
      { 'degerler' => cerceve['degerler'] }
    end
  end

  def load_degerler
    data = load_degerler_source
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

  def score_deger(deger, corpus, fm)
    ad = deger[:ad]
    score = 0.0
    title_tags = [fm['title'], *Array(fm['tags'])].compact.join(' ')

    Array(fm['tags']).each { |v| score += 10 if CurriculumLib.exact_label_match?(v, ad) }
    Array(fm['anatema']).each { |v| score += 8 if CurriculumLib.exact_label_match?(v, ad) }

    score += 5 if CurriculumLib.exact_label_match?(title_tags, ad)
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

  def pick_degerler(book, degerler, picked_unites: [])
    fm = book[:fm]
    corpus = CurriculumLib.build_story_corpus(book, extra_fields: %w[tags anatema])
    scored = degerler.map do |deger|
      score = score_deger(deger, corpus, fm)
      picked_unites.each do |unite|
        (unite['degerler'] || []).each do |item|
          score += 6 if CurriculumLib.exact_label_match?(item, deger[:ad])
        end
      end
      [deger[:ad], score]
    end
    picked = scored.select { |_, s| s.positive? }
                   .sort_by { |_, s| -s }
                   .first(MAX_DEGER)
                   .map(&:first)

    return picked if picked.any?

    FALLBACK.first(MAX_DEGER)
  end

  def map_book(book, degerler, picked_unites: [])
    {
      'degerler' => pick_degerler(book, degerler, picked_unites: picked_unites)
    }
  end
end
