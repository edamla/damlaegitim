#!/usr/bin/env ruby
# frozen_string_literal: true

require 'csv'
require_relative 'curriculum_lib'
require_relative 'map_story_curriculum'
require_relative 'map_story_degerler'
require_relative 'map_story_anatema'
require_relative 'map_story_egilimler'
require_relative 'map_story_beceriler'

REPORT = CurriculumLib::ROOT.join('docs', 'story-metadata-report.csv')

def main
  tymm = CurriculumLib.load_tymm
  degerler, = MapStoryDegerler.load_degerler
  deger_adlari = CurriculumLib.load_deger_adlari(tymm)
  anatemalar = CurriculumLib.load_anatemalar
  egilimler = CurriculumLib.flatten_egilimler(tymm)
  beceriler = CurriculumLib.flatten_beceriler(tymm)
  report_rows = []

  CurriculumLib.story_books.each do |book|
    picked_unites = MapStoryCurriculum.pick_unites(book, tymm)
    fields = {}
    fields.merge!(MapStoryCurriculum.map_book(book, tymm))
    fields.merge!(MapStoryDegerler.map_book(book, degerler, picked_unites: picked_unites))
    fields.merge!(MapStoryAnatema.map_book(book, anatemalar, deger_adlari: deger_adlari))
    fields.merge!(MapStoryEgilimler.map_book(book, egilimler, picked_unites: picked_unites))
    fields.merge!(MapStoryBeceriler.map_book(book, beceriler, picked_unites: picked_unites))

    CurriculumLib.write_frontmatter_fields(book[:path], fields)

    confidence = fields.values_at('anatema', 'degerler', 'egilimler', 'beceriler').all? { |v| Array(v).any? } ? 'ok' : 'low'
    report_rows << [
      book[:path].basename.to_s,
      Array(fields['anatema']).size,
      Array(fields['degerler']).size,
      Array(fields['egilimler']).size,
      Array(fields['beceriler']).size,
      confidence
    ]
    puts "  #{book[:path].basename} → anatema:#{fields['anatema'].size} deger:#{fields['degerler'].size} " \
         "egilim:#{fields['egilimler'].size} beceri:#{fields['beceriler'].size}"
  end

  CSV.open(REPORT, 'w', write_headers: true,
                      headers: %w[file anatema_count degerler_count egilimler_count beceriler_count confidence]) do |csv|
    report_rows.each { |row| csv << row }
  end
  puts "Rapor: #{REPORT}"
end

main if $PROGRAM_NAME == __FILE__
