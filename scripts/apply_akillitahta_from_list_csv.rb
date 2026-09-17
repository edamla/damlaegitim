#!/usr/bin/env ruby
# frozen_string_literal: true

require 'csv'
require 'date'
require 'pathname'
require 'set'
require 'yaml'

ROOT = Pathname.new(__dir__).join('..').expand_path
BOOKS_DIR = ROOT.join('_books')
CSV_PATH = Pathname(ENV.fetch('DAMLA_AKILLITATHA_CSV', ROOT.join('list.csv').to_s))
JACCARD_MIN = 0.38
CDN_HOST = 'cdn.e-damla.com.tr'
LEGACY_CDN_HOSTS = [
  'e-damla.ams3.digitaloceanspaces.com'
].freeze

def normalize_cdn_url(url)
  return url if url.nil? || url.empty?

  u = url.to_s.strip
  LEGACY_CDN_HOSTS.each do |host|
    u = u.sub("https://#{host}/", "https://#{CDN_HOST}/")
    u = u.sub("http://#{host}/", "https://#{CDN_HOST}/")
  end
  u
end

TR_MAP = {
  'ç' => 'c', 'Ç' => 'c', 'ğ' => 'g', 'Ğ' => 'g', 'ı' => 'i', 'I' => 'i', 'İ' => 'i',
  'ö' => 'o', 'Ö' => 'o', 'ş' => 's', 'Ş' => 's', 'ü' => 'u', 'Ü' => 'u'
}.freeze

def fold_tr(s)
  s.to_s.chars.map { |c| TR_MAP[c] || c }.join.downcase
end

def tokens(s)
  fold_tr(s).gsub(/[^a-z0-9\s]/, ' ').split.reject { |t| t.length < 2 }
end

def jaccard(a, b)
  sa = tokens(a).to_set
  sb = tokens(b).to_set
  return 0.0 if sa.empty? || sb.empty?

  (sa & sb).size.to_f / (sa | sb).size
end

def parse_frontmatter(path)
  content = path.read(encoding: 'UTF-8')
  return nil unless content.start_with?('---')

  rest = content[3..]
  end_idx = rest.index("\n---\n")
  return nil unless end_idx

  yaml = rest[0...end_idx]
  body = rest[(end_idx + 5)..]
  { data: YAML.safe_load(yaml, permitted_classes: [Date]), body: body, yaml: yaml }
end

def quote_yaml(val)
  return '""' if val.nil? || val.to_s.empty?

  "\"#{val.to_s.gsub('"', '\\"')}\""
end

def replace_akillitahta_block(yaml_src, at)
  lines = yaml_src.lines
  out = []
  i = 0
  while i < lines.size
    if lines[i].start_with?('akillitahta:')
      out << "akillitahta:\n"
      out << "  exe: #{quote_yaml(at['exe'])}\n"
      out << "  deb: #{quote_yaml(at['deb'])}\n"
      out << "  appimage: #{quote_yaml(at['appimage'])}\n"
      out << "  dmg: #{quote_yaml(at['dmg'])}\n"
      i += 1
      while i < lines.size && lines[i].start_with?('  ')
        i += 1
      end
      next
    end
    out << lines[i]
    i += 1
  end
  out.join
end

def ensure_akillitahta_block(yaml_src, at)
  return replace_akillitahta_block(yaml_src, at) if yaml_src.include?('akillitahta:')

  insert = "akillitahta:\n" \
           "  exe: #{quote_yaml(at['exe'])}\n" \
           "  deb: #{quote_yaml(at['deb'])}\n" \
           "  appimage: #{quote_yaml(at['appimage'])}\n" \
           "  dmg: #{quote_yaml(at['dmg'])}\n"
  yaml_src.sub(/\n# Social Media Attributes\n/, "\n#{insert}\n# Social Media Attributes\n")
end

def grade_from_text(text)
  t = text.to_s
  return 0 if t.match?(/okul\s*oncesi/i)
  m = t.match(/(\d+)\s*\.?\s*sinif/i) || t.match(/(\d+)\s*\.?\s*sınıf/i)
  return m[1].to_i if m
  m = t.match(/(?:seti|ades|defterim|problemler|paragraf|dilbilgisi|sorubankasi|kralegitimseti)(\d+)\z/i)
  m ? m[1].to_i : nil
end

def grade_from_slug(slug)
  m = slug.to_s.match(/(\d+)\z/)
  m ? m[1].to_i : nil
end

def label_for_slug(slug, product)
  p = product.to_s.strip
  return p unless p.empty?

  slug.to_s.sub(/^edamla-/, '').tr('-', ' ')
end

def load_education_books
  paths = BOOKS_DIR.glob('*.md') + BOOKS_DIR.join('_draft').glob('*.md')
  paths.filter_map do |path|
    parsed = parse_frontmatter(path)
    next unless parsed
    data = parsed[:data]
    next unless data.is_a?(Hash) && data['genre'] == 'education'

    {
      path: path,
      basename: path.basename('.md').to_s,
      title: data['title'].to_s,
      grades: Array(data['grades']).map(&:to_i)
    }
  end
end

def compact_slug(slug)
  slug.to_s.sub(/^edamla-/, '').gsub(/[^a-z0-9]/i, '')
end

def compact_basename(basename)
  basename.to_s.gsub(/[^a-z0-9]/i, '')
end

def score_book(label, slug, grade, book)
  title_score = jaccard(label, book[:title])
  base_score = jaccard(label, book[:basename].tr('-', ' '))
  slug_score = jaccard(slug.sub(/^edamla-/, ''), book[:basename].tr('-', ' '))
  score = [title_score, base_score, slug_score].max

  s_compact = compact_slug(slug)
  b_compact = compact_basename(book[:basename])
  score = 0.95 if s_compact == b_compact
  score = [score, 0.85].max if b_compact.include?(s_compact) || s_compact.include?(b_compact)

  if grade && book[:grades].any?
    score += 0.12 if book[:grades].include?(grade)
    score -= 0.25 unless book[:grades].include?(grade)
  end

  score
end

def match_slug_to_book(slug, product, books)
  label = label_for_slug(slug, product)
  grade = grade_from_text(label) || grade_from_text(product) || grade_from_slug(slug)

  best = nil
  best_score = 0.0
  books.each do |book|
    score = score_book(label, slug, grade, book)
    next if score < JACCARD_MIN
    next if score <= best_score

    best_score = score
    best = book
  end
  best ? [best, best_score] : [nil, 0.0]
end

unless CSV_PATH.file?
  warn "list.csv bulunamadı: #{CSV_PATH}"
  exit 1
end

books = load_education_books
by_slug = Hash.new { |h, k| h[k] = { 'product' => '', 'exe' => '', 'appimage' => '' } }

CSV.foreach(CSV_PATH, headers: true, encoding: 'UTF-8') do |row|
  slug = row['slug']&.strip
  platform = row['platform']&.strip&.downcase
  url = row['url']&.strip
  product = row['product']&.strip
  next if slug.nil? || slug.empty? || url.nil? || url.empty?

  by_slug[slug]['product'] = product if product && !product.empty?
  case platform
  when 'windows'
    by_slug[slug]['exe'] = normalize_cdn_url(url)
  when 'linux'
    by_slug[slug]['appimage'] = normalize_cdn_url(url)
  else
    warn "Uyarı: bilinmeyen platform #{platform} (#{slug})"
  end
end

# Her slug → en iyi kitap; aynı kitaba birden fazla slug: en yüksek skor kazanır
candidates = by_slug.map do |slug, links|
  book, score = match_slug_to_book(slug, links['product'], books)
  { slug: slug, links: links, book: book, score: score }
end

assigned = {}
candidates.sort_by { |c| -c[:score] }.each do |c|
  next unless c[:book]
  path_key = c[:book][:path].to_s
  next if assigned.key?(path_key)

  assigned[path_key] = c
end

updated = []
unmapped = []

assigned.each_value do |c|
  path = c[:book][:path]
  parsed = parse_frontmatter(path)
  unless parsed
    warn "Hata: #{path.basename} front matter okunamadı"
    next
  end

  at = {
    'exe' => c[:links]['exe'],
    'deb' => '',
    'appimage' => c[:links]['appimage'],
    'dmg' => ''
  }

  new_yaml = ensure_akillitahta_block(parsed[:yaml], at)
  path.write("---\n#{new_yaml}\n---\n#{parsed[:body]}")
  updated << "#{path.relative_path_from(ROOT)} (#{c[:slug]}, skor #{c[:score].round(2)})"
end

by_slug.each_key do |slug|
  hit = assigned.values.any? { |c| c[:slug] == slug }
  unmapped << slug unless hit
end

puts "list.csv: #{by_slug.size} ürün (slug)"
puts "Güncellenen: #{updated.size}"
updated.sort.each { |line| puts "  #{line}" }
puts "Eşleşmeyen slug: #{unmapped.join(', ')}" if unmapped.any?

low = candidates.select { |c| c[:book] && assigned.values.none? { |a| a[:slug] == c[:slug] } }
low.each do |c|
  puts "  Atlandı (daha iyi eşleşme var): #{c[:slug]} → #{c[:book][:basename]} (#{c[:score].round(2)})"
end
