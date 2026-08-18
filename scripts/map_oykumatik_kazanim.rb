#!/usr/bin/env ruby
# frozen_string_literal: true

require 'yaml'
require_relative 'curriculum_lib'
require_relative 'map_story_curriculum'

MAX_KAZANIM = 10

BILISSEL_HINTS = {
  /dedektif|gizem|analiz|çöz|coz|muhakeme|sır|sir/i => 3,
  /değer|erdem|ahlak|etik|karakter|yardım|yardim|saygı|saygi/i => 2,
  /macera|okuma|kitap|hikaye/i => 2,
  /yarat|hayal|kurgu|senaryo/i => 4,
  /karakter|kahraman|şahıs|sahis/i => 3,
  /zaman|mekan|mekân|tarih|coğraf|cograf/i => 2
}.freeze

KAVRAMSAL_HINTS = {
  /olay|örgü|orgu|sıra|sira|plot/i => 1,
  /zaman|mekan|mekân|tarih|coğraf|cograf/i => 2,
  /karakter|kahraman|şahıs|sahis|kişilik|kisilik/i => 3,
  /dil|anlatım|anlatim|üslup|uslup|konu/i => 4
}.freeze

def grade_pool(grades, entry)
  pool_grades = Array(entry['grades'])
  return true if pool_grades.empty?

  book_grades = grades.map(&:to_i)
  pool_grades.any? do |g|
    next book_grades.include?(8) if g == 'lise'

    book_grades.include?(g.to_i)
  end
end

def score_code(code, entry, context)
  score = CurriculumLib.overlap_score(context, entry['label']) * 5
  score += CurriculumLib.overlap_score(context, entry['kavramsal']) * 2
  score += CurriculumLib.overlap_score(context, entry['bilissel']) * 1.5

  BILISSEL_HINTS.each do |pattern, level|
    parts = code.split('.')
    score += 2.5 if context.match?(pattern) && parts[2].to_i == level
  end

  KAVRAMSAL_HINTS.each do |pattern, level|
    parts = code.split('.')
    score += 2.0 if context.match?(pattern) && parts[1].to_i == level
  end

  score += 1.0 if context.match?(/değer|erdem/i) && entry['bilissel'] == 'Uygulama'
  score += 1.0 if context.match?(/dedektif|gizem/i) && entry['bilissel'] == 'Çözümleme'
  score
end

def select_kazanim_codes(fm, body, by_code)
  grades = Array(fm['grades']).map(&:to_s)
  context_parts = Array(fm['tags']) + Array(fm['anatemalar']) + Array(fm['categories'])
  stripped = CurriculumLib.strip_labeled_blocks(body)
  context = (context_parts.join(' ') + ' ' + stripped).strip

  candidates = by_code.filter_map do |code, entry|
    next unless grade_pool(grades, entry)

  [code, score_code(code, entry, context)]
  end

  candidates.sort_by { |_, s| -s }
            .first(MAX_KAZANIM)
            .map(&:first)
            .compact
            .uniq
            .sort
end

def main
  data = CurriculumLib.load_oykumatik_yml
  by_code = data['by_code'] || {}

  CurriculumLib.story_books.each do |book|
    codes = select_kazanim_codes(book[:fm], book[:body], by_code)
    write_frontmatter_fields(book[:path], { 'kazanim' => codes })
    puts "  #{book[:path].basename} → kazanim:#{codes.size}"
  end
end

main if $PROGRAM_NAME == __FILE__
