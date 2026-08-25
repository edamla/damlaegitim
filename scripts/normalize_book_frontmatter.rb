#!/usr/bin/env ruby
# frozen_string_literal: true

require 'yaml'
require 'pathname'
require 'date'

BOOKS_DIR = Pathname.new(__dir__).join('..', '_books').expand_path
EXAMLINK_PREFIX = 'https://cdn.e-damla.com.tr/PUBLIC/hds_pdf/y/'.freeze

HEADER_KEYS = %w[layout title description categories].freeze
STANDARD_KEYS = %w[ean languages page size publish-number cover examlink preview_link damlaurl].freeze
OPTIONAL_STANDARD_KEYS = %w[original-name original-language].freeze
BOOK_DETAIL_KEYS = %w[paper authors illustrators].freeze
FILTERABLE_KEYS = %w[genre grades ders tags degerler anatema egilimler kazanim beceriler unite].freeze

def parse_frontmatter(content)
  match = content.match(/\A---\r?\n(.*?)\r?\n---\r?\n(.*)\z/m)
  raise "Frontmatter bulunamadı" unless match

  fm = YAML.safe_load(match[1], permitted_classes: [Date, Time], aliases: true) || {}
  [fm, match[2]]
end

def normalize_data(data)
  data = data.transform_keys(&:to_s)
  data.delete('featured')
  data.delete('sold')
  data.delete('examean')
  data['languages'] = ['Türkçe'] if data['languages'].nil? || (data['languages'].is_a?(Array) && data['languages'].empty?)
  data['publish-number'] = '' if data['publish-number'].nil?
  data['cover'] = '' if data['cover'].nil?
  %w[degerler anatema egilimler kazanim beceriler unite tags].each do |key|
    data[key] = [] if data[key].nil?
  end
  %w[kavramlar anatemalar concepts subjects].each { |key| data.delete(key) }
  data['examlink'] = '' if data['examlink'].nil?
  examlink = data['examlink'].to_s.strip
  if !examlink.empty? && !examlink.match?(%r{\Ahttps?://}i)
    data['examlink'] = "#{EXAMLINK_PREFIX}#{examlink}"
  end
  data.delete('previewpage')
  data['preview_link'] = data.delete('review_link') if data.key?('review_link')
  data['preview_link'] = '' if data['preview_link'].nil?
  data['damlaurl'] = data.delete('damlayayinevi') if data.key?('damlayayinevi')
  data['damlaurl'] = '' if data['damlaurl'].nil?
  data['youtube'] = '' if data['youtube'].nil?
  data.delete('ders') if data['genre'] != 'education'
  data.delete('ders') if data['ders'].is_a?(String) && data['ders'].strip.empty?

  data
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

def build_frontmatter(data)
  lines = []

  HEADER_KEYS.each do |key|
    next unless data.key?(key)
    next if key == 'description' && (data[key].nil? || data[key].to_s.empty?)

    prefix = key == 'title' ? "#{key}:  " : "#{key}: "
    lines << "#{prefix}#{yaml_value(data[key], key: key)}"
  end

  lines << ''
  lines << '# Standart Book Attributes'
  STANDARD_KEYS.each do |key|
    lines << "#{key}: #{yaml_value(data[key], key: key)}"
  end
  OPTIONAL_STANDARD_KEYS.each do |key|
    next if data[key].nil? || data[key].to_s.empty?

    lines << "#{key}: #{yaml_value(data[key], key: key)}"
  end

  BOOK_DETAIL_KEYS.each do |key|
    next unless data.key?(key)

    lines << "#{key}: #{yaml_value(data[key], key: key)}"
  end

  lines << ''
  lines << '# Spesific Filterable Attributes'
  lines << '# anatema: anatemalar.json (max 3) | degerler: TYMM Erdem-Değer (max 6) | egilimler: TYMM Eğilimler (max 6) | beceriler: TYMM Beceriler (max 6) | kazanim: Öykümatik | unite: TYMM üniteleri (UI dışı)'
  FILTERABLE_KEYS.each do |key|
    next if key == 'ders' && (data[key].nil? || data[key].to_s.empty?)

    lines << "#{key}: #{yaml_value(data[key], key: key)}"
  end

  lines << ''
  lines << '# Social Media Attributes'
  if data['youtube'].nil? || data['youtube'].to_s.empty?
    lines << 'youtube:'
  else
    lines << "youtube: #{yaml_value(data['youtube'], key: 'youtube')}"
  end

  lines << ''
  lines << '# For adding excerpt add <!--more--> and break the line'
  lines.join("\n")
end

def process_file(path)
  content = path.read
  data, body = parse_frontmatter(content)
  normalized = normalize_data(data)
  new_content = "---\n#{build_frontmatter(normalized)}\n---\n#{body}"
  path.write(new_content)
  path.basename.to_s
end

def main
  files = BOOKS_DIR.glob('*.md').sort
  puts "İşleniyor: #{files.size} dosya"
  files.each { |file| puts "  #{process_file(file)}" }
  puts 'Tamamlandı.'
end

main if $PROGRAM_NAME == __FILE__
