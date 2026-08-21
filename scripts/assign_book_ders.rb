#!/usr/bin/env ruby
# frozen_string_literal: true

require 'json'
require 'pathname'
require 'yaml'
require 'date'

ROOT = Pathname.new(__dir__).join('..').expand_path
BOOKS_DIR = ROOT.join('_books')
DERSLER_PATH = ROOT.join('_data', 'dersler.json')

TR_MAP = {
  'ç' => 'c', 'Ç' => 'c',
  'ğ' => 'g', 'Ğ' => 'g',
  'ı' => 'i', 'I' => 'i', 'İ' => 'i',
  'ö' => 'o', 'Ö' => 'o',
  'ş' => 's', 'Ş' => 's',
  'ü' => 'u', 'Ü' => 'u'
}.freeze

def parse_frontmatter(content)
  match = content.match(/\A---\r?\n(.*?)\r?\n---\r?\n(.*)\z/m)
  raise 'Frontmatter bulunamadı' unless match

  fm = YAML.safe_load(match[1], permitted_classes: [Date, Time], aliases: true) || {}
  [fm.transform_keys(&:to_s), match[2]]
end

def normalize_text(text)
  value = text.to_s.downcase
  TR_MAP.each { |from, to| value = value.gsub(from, to) }
  value.gsub(/[^a-z0-9\s-]/, ' ').squeeze(' ').strip
end

def plain_scalar?(value)
  value.is_a?(String) &&
    !value.empty? &&
    value.match?(/\A[\p{L}\p{N}._-]+\z/u)
end

def yaml_scalar(value)
  return '""' if value.nil? || (value.is_a?(String) && value.empty?)

  case value
  when true, false
    value.to_s
  when Integer, Float
    value.to_s
  when String
    if plain_scalar?(value)
      value
    else
      %("#{value.gsub('\\', '\\\\').gsub('"', '\\"')}")
    end
  else
    %("#{value}")
  end
end

def yaml_value(value, key: nil)
  return '' if key == 'youtube' && (value.nil? || value == '')

  case value
  when Array
    return '[]' if value.empty?

    inner = value.map { |item| yaml_scalar(item) }.join(', ')
    "[#{inner}]"
  else
    yaml_scalar(value)
  end
end

def detect_level(data)
  categories = Array(data['categories']).map(&:to_s)
  return 'ortaokul' if categories.any? { |c| c.include?('Ortaokul') }
  return 'ilkokul' if categories.any? { |c| c.include?('İlkokul') || c.include?('Ilkokul') }

  grades = Array(data['grades']).map { |g| g.to_i }.select(&:positive?)
  return nil if grades.empty?

  grades.max <= 4 ? 'ilkokul' : 'ortaokul'
end

def subject_index(dersler)
  index = {}
  %w[ilkokul ortaokul].each do |level|
    dersler.fetch(level, {}).fetch('subjects', []).each do |subject|
      index[subject['name']] ||= []
      index[subject['name']] << {
        'level' => level,
        'grades' => subject['grades'].map(&:to_i)
      }
    end
  end
  index
end

def valid_ders?(subject_index, ders_name, level, book_grades)
  entries = subject_index[ders_name]
  return false unless entries

  book_grades = Array(book_grades).map(&:to_i).select(&:positive?)

  entries.any? do |info|
    next false if level && info['level'] != level

    book_grades.empty? || book_grades.any? { |grade| info['grades'].include?(grade) }
  end
end

def excluded?(text, exclude_patterns)
  exclude_patterns.any? { |pattern| text.include?(pattern) }
end

def slug_match?(basename, slug_patterns)
  slug_patterns.any? do |pattern|
    basename == pattern || basename.start_with?("#{pattern}-") || basename.start_with?(pattern)
  end
end

def pattern_match?(text, patterns)
  patterns.any? { |pattern| text.include?(pattern) }
end

def infer_ders(data, basename, dersler, subject_index)
  return nil unless data['genre'] == 'education'

  level = detect_level(data)
  combined = normalize_text([
    basename,
    data['title'],
    data['description']
  ].compact.join(' '))

  exclude_patterns = dersler.dig('exclude', 'patterns') || []
  return nil if excluded?(combined, exclude_patterns.map { |p| normalize_text(p) })

  dersler.fetch('map', []).each do |entry|
    map_level = entry['level']
    next if map_level != 'both' && level && map_level != level

    if slug_match?(basename, Array(entry['slug']))
      ders = entry['ders']
      return ders if valid_ders?(subject_index, ders, level, data['grades'])
    end
  end

  dersler.fetch('map', []).each do |entry|
    map_level = entry['level']
    next if map_level != 'both' && level && map_level != level
    next unless pattern_match?(combined, Array(entry['patterns']).map { |p| normalize_text(p) })

    ders = entry['ders']
    return ders if valid_ders?(subject_index, ders, level, data['grades'])
  end

  nil
end

def patch_ders_in_content(content, ders_value)
  match = content.match(/\A(---\r?\n.*?\r?\n---\r?\n)(.*)\z/m)
  raise 'Frontmatter bulunamadı' unless match

  frontmatter = match[1]
  body = match[2]

  if frontmatter.match?(/^ders:\s*.+$/m)
    if ders_value.nil? || ders_value.to_s.strip.empty?
      frontmatter = frontmatter.gsub(/^ders:\s*.+\r?\n/, '')
    else
      frontmatter = frontmatter.sub(/^ders:\s*.+$/m, "ders: #{yaml_scalar(ders_value)}")
    end
  elsif ders_value && !ders_value.to_s.strip.empty?
    frontmatter = frontmatter.sub(/^((?:genre|grades):[^\n]*\n)+/m) do |block|
      "#{block}ders: #{yaml_scalar(ders_value)}\n"
    end
  end

  "#{frontmatter}#{body}"
end

def update_ders_in_file(path, dersler, subject_index, dry_run:)
  content = path.read
  data, = parse_frontmatter(content)
  basename = path.basename('.md').to_s
  original_ders = data['ders']

  if data['genre'] != 'education'
    new_ders = nil
  elsif !original_ders.to_s.strip.empty?
    unless subject_index.key?(original_ders)
      return [:invalid_override, basename, original_ders]
    end
    new_ders = original_ders
  else
    new_ders = infer_ders(data, basename, dersler, subject_index)
  end

  changed = original_ders.to_s != new_ders.to_s
  path.write(patch_ders_in_content(content, new_ders)) if changed && !dry_run

  if data['genre'] != 'education'
    [:skipped_non_education, basename, nil]
  elsif new_ders
    changed ? [:assigned, basename, new_ders] : [:unchanged, basename, new_ders]
  elsif excluded?(normalize_text([basename, data['title'], data['description']].compact.join(' ')),
                (dersler.dig('exclude', 'patterns') || []).map { |p| normalize_text(p) })
    [:general_only, basename, nil]
  elsif original_ders.to_s.strip.empty?
    [:manual_required, basename, nil]
  else
    [:cleared, basename, nil]
  end
end

def main
  dry_run = ARGV.include?('--dry-run')
  dersler = JSON.parse(DERSLER_PATH.read)
  subject_index = subject_index(dersler)

  map_names = dersler.fetch('map', []).map { |entry| entry['ders'] }.uniq
  map_names.each do |name|
    warn "UYARI: map dersi subjects listesinde yok: #{name}" unless subject_index.key?(name)
  end

  stats = Hash.new(0)
  manual = []
  invalid = []

  BOOKS_DIR.glob('*.md').sort.each do |path|
    status, basename, value = update_ders_in_file(path, dersler, subject_index, dry_run: dry_run)
    stats[status] += 1
    manual << basename if status == :manual_required
    invalid << [basename, value] if status == :invalid_override
  end

  puts dry_run ? 'DRY RUN — dosya yazılmadı' : 'Dosyalar güncellendi'
  puts "Atanan: #{stats[:assigned]}"
  puts "Değişmedi: #{stats[:unchanged]}"
  puts "Genel-only (ders yok): #{stats[:general_only]}"
  puts "Hikaye/diğer (education değil): #{stats[:skipped_non_education]}"
  puts "MANUEL GEREKLİ: #{manual.size}"
  manual.each { |name| puts "  - #{name}" }
  unless invalid.empty?
    puts "GEÇERSİZ OVERRIDE: #{invalid.size}"
    invalid.each { |name, ders| puts "  - #{name}: #{ders}" }
  end
end

main if $PROGRAM_NAME == __FILE__
