#!/usr/bin/env ruby
# frozen_string_literal: true

require 'csv'
require 'date'
require 'json'
require 'pathname'
require_relative 'curriculum_lib'

ROOT = CurriculumLib::ROOT
DOCS_TYMM = ROOT.join('docs', 'data', 'tymm')
INPUT_ILKOKUL = DOCS_TYMM.join('ilkokul-turkce', 'api-response.json')
INPUT_ORTAOKUL = DOCS_TYMM.join('ortaokul-turkce', 'api-response.json')
INPUT_CERCEVELER = DOCS_TYMM.join('cerceveler.json')
OUTPUT_JSON = ROOT.join('_data', 'tymm.json')
OUTPUT_CSV = DOCS_TYMM.join('tymmreferans.csv')
OUTPUT_CSV_ILKOKUL = DOCS_TYMM.join('tymm-ilkokul-referans.csv')
OUTPUT_CSV_ORTAOKUL = DOCS_TYMM.join('tymm-ortaokul-referans.csv')

SKIP_POINT_LABELS = [
  /Öğrenme Kanıtları/i
].freeze

CURRICULUM_POINT_LABELS = (
  [CurriculumLib::DEGERLER_LABEL, CurriculumLib::EGILIMLER_LABEL] + CurriculumLib::BECERI_LABELS
).freeze

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

def load_cerceveler(path)
  raise "Çerçeve kaynağı bulunamadı: #{path}" unless path.file?

  data = JSON.parse(path.read)
  %w[degerler beceriler egilimler].each do |section|
    raise "cerceveler.json eksik bölüm: #{section}" unless data[section]
  end

  data.slice('degerler', 'beceriler', 'egilimler')
end

def build_meta(grades)
  {
    'kaynak_mufredat' => 'https://tymm.meb.gov.tr/ogretim-programlari/ders/',
    'kaynak_degerler' => 'https://tymm.meb.gov.tr/beceriler/erdem-deger-eylem-cercevesi',
    'kaynak_egilimler' => 'https://tymm.meb.gov.tr/beceriler/egilimler',
    'kaynak_cerceveler' => 'docs/data/tymm/cerceveler.json',
    'referans_ham' => 'docs/data/tymm/',
    'guncelleme' => Date.today.iso8601,
    'ders' => 'turkce',
    'siniflar' => grades.keys.sort_by(&:to_i)
  }
end

def main
  charts_by_grade = {}

  [INPUT_ILKOKUL, INPUT_ORTAOKUL].each do |path|
    raise "Dosya bulunamadı: #{path}" unless path.file?

    data = JSON.parse(path.read)
    data['stackedChart'].each do |chart|
      grade = CurriculumLib.grade_from_chart_name(chart['name'])
      next unless grade

      charts_by_grade[grade] = chart
    end
  end

  raise "Çerçeve kaynağı bulunamadı: #{INPUT_CERCEVELER}" unless INPUT_CERCEVELER.file?

  grades = {}
  ('1'..'8').each do |g|
    next unless charts_by_grade[g]

    grades[g] = build_grade_data(charts_by_grade[g])
  end

  payload = {
    'meta' => build_meta(grades),
    'cerceveler' => load_cerceveler(INPUT_CERCEVELER),
    'grades' => grades
  }

  OUTPUT_JSON.dirname.mkpath
  OUTPUT_JSON.write(JSON.pretty_generate(payload) + "\n")

  csv_rows = build_csv_rows_from_charts(charts_by_grade)
  write_csv(OUTPUT_CSV, csv_rows)
  write_csv(OUTPUT_CSV_ILKOKUL, csv_rows.select { |row| row[0] == 'İlkokul' })
  write_csv(OUTPUT_CSV_ORTAOKUL, csv_rows.select { |row| row[0] == 'Ortaokul' })

  deger_count = payload.dig('cerceveler', 'degerler', 'degerler')&.size || 0
  beceri_count = payload.dig('cerceveler', 'beceriler')&.size || 0
  egilim_grup = payload.dig('cerceveler', 'egilimler', 'gruplar')&.size || 0
  puts "Yazıldı: #{OUTPUT_JSON} (#{grades.size} sınıf, cerceveler: #{deger_count} değer, #{beceri_count} beceri çerçevesi, #{egilim_grup} eğilim grubu)"
  puts "Yazıldı: #{OUTPUT_CSV} (#{csv_rows.size} satır)"
  puts "Yazıldı: #{OUTPUT_CSV_ILKOKUL} (#{csv_rows.count { |r| r[0] == 'İlkokul' }} satır)"
  puts "Yazıldı: #{OUTPUT_CSV_ORTAOKUL} (#{csv_rows.count { |r| r[0] == 'Ortaokul' }} satır)"
end

main if $PROGRAM_NAME == __FILE__
