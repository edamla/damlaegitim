#!/usr/bin/env ruby
# frozen_string_literal: true

require 'yaml'
require 'pathname'
require 'date'

BOOKS_DIR = Pathname.new(__dir__).join('..', '_books').expand_path

HEADER_KEYS = %w[layout title image categories tags genre previewpage].freeze
STANDARD_KEYS = %w[ean examean review_link languages page size publish-number cover].freeze
OPTIONAL_STANDARD_KEYS = %w[original-name original-language].freeze
FILTERABLE_KEYS = %w[grades concepts subjects examimage examlink].freeze

def parse_frontmatter(content)
  match = content.match(/\A---\r?\n(.*?)\r?\n---\r?\n(.*)\z/m)
  raise "Frontmatter bulunamadı" unless match

  fm = YAML.safe_load(match[1], permitted_classes: [Date, Time], aliases: true) || {}
  [fm, match[2]]
end

def normalize_data(data)
  data = data.transform_keys(&:to_s)
  data.delete('featured')

  ean = data['ean']
  data['examean'] = ean if data['examean'].nil? || data['examean'].to_s.empty?
  data['review_link'] = '' if data['review_link'].nil?
  data['languages'] = [] if data['languages'].nil?
  data['publish-number'] = '' if data['publish-number'].nil?
  data['cover'] = '' if data['cover'].nil?
  data['concepts'] = [] if data['concepts'].nil?
  data['subjects'] = [] if data['subjects'].nil?
  data['examimage'] = '' if data['examimage'].nil?
  data['examlink'] = '' if data['examlink'].nil?
  data['youtube'] = '' if data['youtube'].nil?

  data
end

def yaml_scalar(value)
  return '""' if value.nil? || (value.is_a?(String) && value.empty?)

  case value
  when true, false
    value.to_s
  when Integer, Float
    value.to_s
  when String
    if value.match?(/\A[\w.-]+\z/u) && !value.match?(/\A\d+\z/)
      value
    elsif value.match?(/\A\d+\z/)
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

  lines << ''
  lines << '# Spesific Filterable Attributes'
  FILTERABLE_KEYS.each do |key|
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
