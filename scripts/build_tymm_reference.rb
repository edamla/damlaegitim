#!/usr/bin/env ruby
# frozen_string_literal: true

require 'csv'
require 'json'
require 'yaml'
require 'pathname'
require_relative 'curriculum_lib'

ROOT = CurriculumLib::ROOT
OUTPUT_YML = ROOT.join('_data', 'tymm.yml')
OUTPUT_CSV = ROOT.join('docs', 'tymmreferans.csv')

COMPONENT_TYPES = {
  'degerler' => 'deger',
  'egilimler' => 'egilim',
  'beceriler' => 'beceri'
}.freeze

def build_grade_data(chart)
  grade = CurriculumLib.grade_from_chart_name(chart['name'])
  unite_map = {}

  chart['dataPoints'].each do |point|
    label = point['label'].to_s
    themes = CurriculumLib.parse_themes_from_html(point['beceriler'])
    themes.each do |theme_name, items|
      unite_map[theme_name] ||= {
        'label' => theme_name,
        'degerler' => [],
        'egilimler' => [],
        'beceriler' => []
      }
      case label
      when CurriculumLib::DEGERLER_LABEL
        unite_map[theme_name]['degerler'] |= items.map { |i| CurriculumLib.normalize_deger(i) }
      when CurriculumLib::EGILIMLER_LABEL
        unite_map[theme_name]['egilimler'] |= items.map { |i| CurriculumLib.normalize_egilim(i) }
      when *CurriculumLib::BECERI_LABELS
        unite_map[theme_name]['beceriler'] |= items.map { |i| CurriculumLib.normalize_beceri(i) }
      end
    end
  end

  {
    'grade' => grade,
    'unites' => unite_map.values.sort_by { |u| u['label'] }
  }
end

def build_csv_rows(grades)
  rows = []
  grades.sort_by { |grade, _| grade.to_i }.each do |grade, grade_data|
    Array(grade_data['unites']).each do |unite|
      unite_label = unite['label']
      COMPONENT_TYPES.each do |field, tip|
        Array(unite[field]).each do |etiket|
          rows << [grade, unite_label, tip, etiket]
        end
      end
    end
  end
  rows.sort_by { |grade, unite, tip, etiket| [grade.to_i, unite, tip, etiket] }
end

def write_csv(path, rows)
  path.dirname.mkpath
  CSV.open(path, 'w', col_sep: ';', encoding: 'UTF-8', write_headers: true,
           headers: %w[sinif unite tip etiket]) do |csv|
    rows.each { |row| csv << row }
  end
end

def main
  grades = {}
  processed = {}

  [ROOT.join('docs', 'tymm-ilkokul-turkce', 'api-response.json'),
   ROOT.join('docs', 'tymm-ortaokul-turkce', 'api-response.json')].each do |path|
    data = JSON.parse(path.read)
    data['stackedChart'].each do |chart|
      grade_data = build_grade_data(chart)
      grade = grade_data['grade']
      next unless grade

      processed[grade] = grade_data
    end
  end

  ('1'..'8').each { |g| grades[g] = processed[g] if processed[g] }

  OUTPUT_YML.dirname.mkpath
  OUTPUT_YML.write({ 'grades' => grades }.to_yaml)

  csv_rows = build_csv_rows(grades)
  write_csv(OUTPUT_CSV, csv_rows)

  puts "Yazıldı: #{OUTPUT_YML} (#{grades.size} sınıf)"
  puts "Yazıldı: #{OUTPUT_CSV} (#{csv_rows.size} satır + başlık)"
end

main if $PROGRAM_NAME == __FILE__