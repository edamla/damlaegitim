#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative 'curriculum_lib'

dry_run = ARGV.include?('--dry-run')
paths = CurriculumLib::BOOKS_DIR.glob('**/*.md').sort
changed = []

paths.each do |path|
  content = path.read
  _fm, body = CurriculumLib.parse_frontmatter(content)
  cleaned = CurriculumLib.clean_book_body(body)
  next if cleaned == body.strip

  changed << path.relative_path_from(CurriculumLib::ROOT)
  next if dry_run

  CurriculumLib.write_book_body(path, cleaned)
end

if changed.empty?
  puts(dry_run ? 'Değişiklik yok.' : 'Temizlenecek dosya bulunamadı.')
else
  puts "#{changed.size} dosya #{dry_run ? 'değişecek' : 'temizlendi'}:"
  changed.each { |p| puts "  #{p}" }
end
