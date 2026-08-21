#!/usr/bin/env ruby
# frozen_string_literal: true

require 'csv'
require 'json'
require 'pathname'
require_relative 'curriculum_lib'

ROOT = CurriculumLib::ROOT
OUTPUT_JSON = ROOT.join('_data', 'tymm.json')
OUTPUT_CSV = ROOT.join('docs', 'tymmreferans.csv')
OUTPUT_CSV_ILKOKUL = ROOT.join('docs', 'tymm-ilkokul-referans.csv')
OUTPUT_CSV_ORTAOKUL = ROOT.join('docs', 'tymm-ortaokul-referans.csv')

SKIP_POINT_LABELS = [
  /Öğrenme Kanıtları/i
].freeze

CURRICULUM_POINT_LABELS = (
  [CurriculumLib::DEGERLER_LABEL, CurriculumLib::EGILIMLER_LABEL] + CurriculumLib::BECERI_LABELS
).freeze

COMPONENT_TYPES = {
  'degerler' => 'deger',
  'egilimler' => 'egilim',
  'beceriler' => 'beceri'
}.freeze

CSV_HEADERS = %w[kademe sinif unite bilesen etiket].freeze

def kademe_for_grade(grade)
  grade.to_i <= 4 ? 'İlkokul' : 'Ortaokul'
end

def skip_point_label?(label)
  SKIP_POINT_LABELS.any? { |pattern| label.match?(pattern) }
end

def normalize_etiket(bilesen, raw)
  case bilesen
  when CurriculumLib::DEGERLER_LABEL
    CurriculumLib.normalize_deger(raw)
  when CurriculumLib::EGILIMLER_LABEL
    CurriculumLib.normalize_egilim(raw)
  else
    CurriculumLib.normalize_beceri(raw)
  end
end

def build_grade_data(chart)
  grade = CurriculumLib.grade_from_chart_name(chart['name'])
  unite_map = {}

  chart['dataPoints'].each do |point|
    label = point['label'].to_s
    next if skip_point_label?(label)
    next unless CURRICULUM_POINT_LABELS.include?(label)

    themes = CurriculumLib.parse_themes_from_html(point['beceriler'])
    themes.each do |theme_name, items|
      unite_map[theme_name] ||= {
        'label' => theme_name,
        'degerler' => [],
        'egilimler' => [],
        'beceriler' => []
      }
      normalized = items.map { |i| normalize_etiket(label, i) }.reject(&:empty?).uniq
      case label
      when CurriculumLib::DEGERLER_LABEL
        unite_map[theme_name]['degerler'] |= normalized
      when CurriculumLib::EGILIMLER_LABEL
        unite_map[theme_name]['egilimler'] |= normalized
      when *CurriculumLib::BECERI_LABELS
        unite_map[theme_name]['beceriler'] |= normalized
      end
    end
  end

  {
    'grade' => grade,
    'unites' => unite_map.values.sort_by { |u| u['label'] }
  }
end

def build_csv_rows_from_charts(charts_by_grade)
  rows = []

  charts_by_grade.sort_by { |grade, _| grade.to_i }.each do |grade, chart|
    kademe = kademe_for_grade(grade)
    chart['dataPoints'].each do |point|
      bilesen = point['label'].to_s
      next if skip_point_label?(bilesen)
      next unless CURRICULUM_POINT_LABELS.include?(bilesen)

      themes = CurriculumLib.parse_themes_from_html(point['beceriler'])
      themes.each do |unite, items|
        items.each do |raw|
          etiket = normalize_etiket(bilesen, raw)
          next if etiket.empty?

          rows << [kademe, grade, unite, bilesen, etiket]
        end
      end
    end
  end

  rows.uniq.sort_by do |kademe, grade, unite, bilesen, etiket|
    [kademe == 'İlkokul' ? 0 : 1, grade.to_i, unite, bilesen, etiket]
  end
end

def write_csv(path, rows)
  path.dirname.mkpath
  File.open(path, 'w:UTF-8') do |file|
    file.write("\uFEFF")
    csv = CSV.new(file, col_sep: ';', write_headers: true, headers: CSV_HEADERS)
    rows.each { |row| csv << row }
  end
end

def main
  charts_by_grade = {}

  [ROOT.join('docs', 'tymm-ilkokul-turkce', 'api-response.json'),
   ROOT.join('docs', 'tymm-ortaokul-turkce', 'api-response.json')].each do |path|
    data = JSON.parse(path.read)
    data['stackedChart'].each do |chart|
      grade = CurriculumLib.grade_from_chart_name(chart['name'])
      next unless grade

      charts_by_grade[grade] = chart
    end
  end

  grades = {}
  ('1'..'8').each do |g|
    next unless charts_by_grade[g]

    grades[g] = build_grade_data(charts_by_grade[g])
  end

  OUTPUT_JSON.dirname.mkpath
  OUTPUT_JSON.write(JSON.pretty_generate({ 'grades' => grades }) + "\n")

  csv_rows = build_csv_rows_from_charts(charts_by_grade)
  write_csv(OUTPUT_CSV, csv_rows)
  write_csv(OUTPUT_CSV_ILKOKUL, csv_rows.select { |row| row[0] == 'İlkokul' })
  write_csv(OUTPUT_CSV_ORTAOKUL, csv_rows.select { |row| row[0] == 'Ortaokul' })

  puts "Yazıldı: #{OUTPUT_JSON} (#{grades.size} sınıf)"
  puts "Yazıldı: #{OUTPUT_CSV} (#{csv_rows.size} satır)"
  puts "Yazıldı: #{OUTPUT_CSV_ILKOKUL} (#{csv_rows.count { |r| r[0] == 'İlkokul' }} satır)"
  puts "Yazıldı: #{OUTPUT_CSV_ORTAOKUL} (#{csv_rows.count { |r| r[0] == 'Ortaokul' }} satır)"
end

main if $PROGRAM_NAME == __FILE__
