#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative 'curriculum_lib'

module MapStoryAnatema
  module_function

  MAX_ANATEMA = 3

  KEYWORD_HINTS = {
    /aile|anne|baba|dede|kardeş|kardes/i => %w[Aile Arkadaşlık],
    /arkadaş|arkadas|dostluk/i => %w[Arkadaşlık Dayanışma],
    /sevgi|şefkat|sefkat/i => ['Sevgi ve Şefkat', 'Empati'],
    /empati|duygu/i => %w[Empati Duygular],
    /iletişim|iletisim/i => ['İletişim'],
    /dayanışma|dayanisma|yardım|yardim/i => ['Dayanışma', 'Paylaşma ve Yardımlaşma'],
    /özgüven|ozguven|cesaret/i => ['Özgüven', 'Cesaret ve Korkular'],
    /sorumluluk/i => ['Sorumluluk'],
    /azim|başarı|basari/i => ['Azim ve Başarı'],
    /problem|çözüm|cozum/i => ['Problem Çözme', 'Karar Verme'],
    /merak|keşif|kesif/i => ['Merak ve Keşif'],
    /macera/i => %w[Macera Gizem],
    /gizem|polisiye|dedektif/i => %w[Gizem Polisiye],
    /hayal|fantast|fantazi/i => ['Hayal Gücü', 'Fantastik'],
    /bilim|teknoloji|uzay|robot/i => ['Bilim ve Teknoloji', 'Bilim Kurgu'],
    /doğa|doga|çevre|cevre|hayvan/i => %w[Doğa Hayvanlar],
    /sürdürülebilir|surdurulebilir/i => ['Sürdürülebilir Yaşam'],
    /sağlık|saglik|spor/i => ['Sağlıklı Yaşam', 'Spor ve Hareket'],
    /güvenli|guvenli/i => ['Güvenli Yaşam'],
    /adalet|hak/i => ['Haklar ve Adalet'],
    /toplum|birlikte/i => ['Toplum ve Birlikte Yaşam'],
    /hoşgörü|hosgoru|farklılık/i => ['Farklılıklar ve Hoşgörü'],
    /kültür|kultur|tarih|miras/i => ['Kültür ve Tarih', 'Kültürel Miras'],
    /sanat|müzik|muzik|resim/i => ['Sanat ve Yaratıcılık'],
    /okul|eğitim|egitim|okuma/i => ['Okul ve Eğitim', 'Okuma ve Öğrenme'],
    /çocukluk|cocukluk|büyüme|buyume/i => ['Çocukluk ve Büyüme'],
    /gezi|yolculuk|seyahat/i => ['Yolculuk ve Gezi', 'Farklı Dünyalar'],
    /gelecek|yenilik|icat/i => ['Gelecek ve Yenilik'],
    /mizah|eğlence|eglence|komik/i => ['Mizah ve Eğlence'],
    /değer|erdem|deger/i => ['Değerler']
  }.freeze

  FALLBACK = ['Macera', 'Arkadaşlık', 'Değerler'].freeze

  def map_book(book, anatemalar, deger_adlari: [])
    corpus = CurriculumLib.build_story_corpus(book, extra_fields: %w[anatema egilimler beceriler degerler])
    candidates = anatemalar.reject do |label|
      deger_adlari.any? { |d| CurriculumLib.exact_label_match?(label, d) }
    end

    picked = CurriculumLib.pick_top_labels(
      corpus,
      book[:fm],
      candidates,
      keyword_hints: KEYWORD_HINTS,
      max: MAX_ANATEMA,
      fallback: FALLBACK & anatemalar
    )
    { 'anatema' => picked }
  end
end

def main
  tymm = CurriculumLib.load_tymm
  deger_adlari = CurriculumLib.load_deger_adlari(tymm)
  anatemalar = CurriculumLib.load_anatemalar
  puts "Anatema eşlemesi (#{anatemalar.size} aday, #{CurriculumLib.story_books.size} kitap)…"

  CurriculumLib.story_books.each do |book|
    fields = MapStoryAnatema.map_book(book, anatemalar, deger_adlari: deger_adlari)
    CurriculumLib.write_frontmatter_fields(book[:path], fields)
    puts "  #{book[:path].basename} → #{fields['anatema'].join(', ')}"
  end
  puts 'Tamamlandı.'
end

main if $PROGRAM_NAME == __FILE__
