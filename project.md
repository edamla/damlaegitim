# Damla Okul — Proje Mimarisi

Bu belge, [damlaegitim.com](https://damlaegitim.com) (Damla Okul) statik sitesinin teknik yapısını, dosya organizasyonunu ve geliştirme kurallarını açıklar.

## Genel Bakış

| Özellik | Değer |
|---------|-------|
| Tür | Statik site (Jamstack) |
| Motor | [Jekyll](https://jekyllrb.com/) 4.x |
| Dil | Türkçe (`language: tr`) |
| Yayın | GitHub Pages (`CNAME` → `damlaegitim.com`) |
| Build çıktısı | `_site/` (gitignore) |
| Node/npm | **Yok** — CSS doğrudan düzenlenir, build adımı gerekmez |

Site, **Damla Okul** markası altında Damla Yayınevi’nin okul yayınlarını ve eğitim setlerini listeleyen bir ürün kataloğudur. İçerik Markdown + YAML front matter ile yönetilir; görünüm Bootstrap 5 ve özel CSS katmanlarıyla sağlanır.

---

## Mimari Diyagram

```
┌─────────────────────────────────────────────────────────────┐
│  İçerik (Markdown + YAML)                                   │
│  _books/  _catalogs/  _pages/  _posts/  _slides/  index   │
└──────────────────────────┬──────────────────────────────────┘
                           │ Jekyll build
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Şablonlar                                                  │
│  _layouts/  →  default.html  →  book.html, page.html, …     │
│  _includes/  →  book-card, slider, menu, filtreler         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Statik çıktı (_site/)                                      │
│  HTML + assets/css + assets/js + assets/images              │
└──────────────────────────┬──────────────────────────────────┘
                           │ git push
                           ▼
                    GitHub Pages (damlaegitim.com)
```

---

## CSS Katmanları

Stil üç katmanlıdır. Özelleştirme **asla** Bootstrap dosyasına yazılmaz.

```
bootstrap.min.css   →  Framework (Bootstrap 5.3, statik dosya)
theme.css           →  Tasarım sistemi (token, bileşen, layout)
app.css             →  Bootstrap override (renk, watermark, geçici fix)
tiny-slider.css     →  Anasayfa slider (3. parti)
buyout.css          →  E-ticaret barı (yalnızca kitap/katalog detay)
```

### Sorumluluk ayrımı

| Dosya | Ne yazılır | Ne yazılmaz |
|-------|------------|-------------|
| `assets/css/theme.css` | `:root` token’lar, `.book-card`, `.grade-nav`, `.site-nav`, `.prose` | Bootstrap class override, `!important` |
| `assets/css/app.css` | `--bs-primary`, `.btn-primary`, body arka plan, sayfa özel düzeltmeler | Yeni bileşen tanımı |

**Kural:** Yeni bileşen → `theme.css`. Bootstrap’ı ezmek → `app.css`.

### Tasarım token’ları (`theme.css` → `:root`)

```css
--color-primary: #03a87c;
--color-primary-dark: #028a66;
--color-surface: #fafafa;
--font-serif: Lora, Georgia, serif;
--nav-height: 4rem;
```

---

## Klasör Yapısı

```
damlaegitim/
├── _config.yml           # Site ayarları, koleksiyonlar, plugin’ler
├── _books/               # Ürünler (kitap / eğitim seti) — ~55 kayıt
├── _catalogs/            # PDF/flipbook kataloglar
├── _slides/              # Anasayfa slider verisi (output: false)
├── _posts/               # Blog yazıları
├── _pages/               # Statik sayfalar (hakkımızda, ürünler, iletişim…)
├── _layouts/             # HTML şablonları
├── _includes/            # Yeniden kullanılabilir parçalar
├── assets/
│   ├── css/
│   │   ├── bootstrap.min.css
│   │   ├── theme.css
│   │   ├── app.css
│   │   ├── tiny-slider.css
│   │   └── buyout.css
│   ├── js/
│   │   ├── bootstrap.bundle.min.js
│   │   ├── nav.js              # Navbar scroll (vanilla JS)
│   │   ├── book-filter.js      # Sınıf/tür filtreleme
│   │   ├── theme.js              # Eski (jQuery) — kullanılmıyor
│   │   ├── tiny-slider.js
│   │   └── lazyload.js
│   └── images/
│       ├── ean/                  # Kitap kapak görselleri
│       └── favicon/
├── index.html            # Anasayfa
├── Gemfile               # Ruby bağımlılıkları
├── CNAME                 # damlaegitim.com
├── install.sh            # bundle install
├── start.sh              # jekyll serve
└── _site/                # Build çıktısı (gitignore)
```

---

## Koleksiyonlar ve URL’ler

| Koleksiyon | Klasör | URL | Layout | Çıktı |
|------------|--------|-----|--------|-------|
| `books` | `_books/` | `/urunler/:title` | `book` | Evet |
| `catalogs` | `_catalogs/` | `/kataloglar/:title` | `catalog` | Evet |
| `slides` | `_slides/` | — | — | Hayır (veri kaynağı) |
| Sayfalar | `_pages/` | `/:title/` | `page` | Evet |
| Yazılar | `_posts/` | varsayılan | `post` | Evet |

`_pages` klasörü `_config.yml` içinde `include: ["_pages"]` ile Jekyll kaynaklarına dahil edilir.

---

## Layout’lar

| Dosya | Kullanım |
|-------|----------|
| `default.html` | Kök şablon: head, navbar, footer, script’ler |
| `page.html` | Basit içerik sayfası |
| `page-sidebar.html` | İçerik + yan menü |
| `book.html` | Ürün detay sayfası |
| `book2.html` / `previewbook.html` | Tam ekran önizleme varyantları |
| `catalog.html` | Katalog detay + iframe görüntüleyici |
| `post.html` | Blog yazısı |
| `person.html` / `illustrator.html` / `translator.html` | Kişi profilleri |

Tüm layout’lar `layout: default` zinciri üzerinden `default.html`’i extend eder.

---

## Önemli Include’lar

| Dosya | Görev |
|-------|-------|
| `menu-header.html` | Ana navigasyon linkleri |
| `menu-socialmedia.html` | Sosyal medya ikonları |
| `slider.html` | Anasayfa Tiny Slider |
| `book-grade-nav.html` | Sınıf sekmesi + tür alt menüsü |
| `book-home-groups.html` | Anasayfa kitap listesi (Eğitim / Hikaye) |
| `book-card.html` | Tek kitap kartı partial |
| `book-grade-filter.html` | Ürünler sayfası sınıf checkbox’ları |
| `tracking-header.html` / `tracking-footer.html` | Google Analytics |

---

## JavaScript

| Dosya | Bağımlılık | Görev |
|-------|------------|-------|
| `bootstrap.bundle.min.js` | — | Collapse, dropdown, modal |
| `nav.js` | — | Scroll’da navbar gizle/göster |
| `book-filter.js` | — | Anasayfa ve `/urunler` filtreleme |
| `tiny-slider.js` | — | Anasayfa slider |
| `lazyload.js` | — | Görsel lazy loading (`lazyimages: enabled`) |

jQuery kullanılmaz. Eski `theme.js` dosyası repoda kalabilir ancak `default.html`’de yüklenmez.

---

## Ürün (Kitap) Front Matter Örneği

```yaml
---
layout: book
title: "Deyim Öyküleri 5 Kitap"
grades: [3]
genre: story          # education | story
subjects: ["Dil Bilim", "Milli Kültür"]
image: assets/images/ean/9786053832874.jpg
categories: ["Çocuk", "Hikaye"]
previewpage: true
ean: 9786053832874
review_link: "https://cdn.e-damla.com.tr/..."
languages: ["Türkçe"]
page: Her Biri 64
size: "14x20cm"
publish-number: 1443
cover: "Karton Kapak"
---
```

Markdown gövdesi ürün açıklaması olarak `book.html` içindeki `.prose` alanında render edilir.

---

## Filtreleme Mantığı

**Anasayfa:** `book-grade-nav.html` + `book-filter.js`
- Sınıf seçimi → `data-grades` attribute’u ile eşleşme
- Tür (Eğitim/Hikaye) → `data-genre` attribute’u
- Hedef selector: `.listbooks-home-item`

**Ürünler sayfası (`/urunler`):** Dropdown checkbox’lar + `filterBooks()`
- Hedef selector: `.listbooks-item`

---

## Jekyll Plugin’leri

- `jekyll-feed` — RSS
- `jekyll-sitemap` — sitemap.xml
- `jekyll-seo-tag` — `{% seo %}` meta etiketleri
- `jekyll-paginate` — sayfalama
- `jekyll-archives` — arşiv sayfaları
- `jekyll-figure` / `jekyll-gist` — içerik zenginleştirme

---

## Build ve Deploy

### Yerel geliştirme

```bash
# İlk kurulum
sh install.sh          # bundle install

# Geliştirme sunucusu
sh start.sh            # bundle exec jekyll serve
# → http://localhost:4000
```

### Canlıya alma

```bash
bundle exec jekyll build   # isteğe bağlı yerel doğrulama
git add .
git commit -m "..."
git push
```

GitHub Pages, push sonrası kaynak branch’ten Jekyll build alır. **CI/CD veya npm build yoktur.** CSS değişiklikleri doğrudan `assets/css/` altında yapılır ve commit edilir.

---

## Yeni Ürün Ekleme

1. `_books/yeni-urun.md` oluştur
2. Front matter doldur (`title`, `grades`, `genre`, `image`, `ean`…)
3. Kapak görselini `assets/images/ean/` altına koy
4. `bundle exec jekyll serve` ile kontrol et
5. `git push`

---

## Yeni Bileşen / Stil Ekleme

1. Kalıcı görsel bileşen → `theme.css` (Components bölümü)
2. Bootstrap override → `app.css`
3. HTML’de Bootstrap grid class’ları (`row`, `col-*`) kullanılabilir
4. Partial gerekiyorsa → `_includes/` altına ekle

---

## Harici Bağımlılıklar

| Kaynak | Kullanım |
|--------|----------|
| Google Fonts (Lora) | Makale/kitap tipografisi |
| Font Awesome 5 CDN | İkonlar |
| `cdn.e-damla.com.tr` | Önizleme sayfaları, örnek sayfalar |
| Google Analytics | `G-KFMVQ3WNN3` (production) |

---

## Bilinen Legacy Dosyalar

Aşağıdaki dosyalar geçmişten kalma olabilir; aktif kullanılmıyorsa temizlenebilir:

- `_layouts/catalog-old.html`, `book2.html`
- `assets/js/theme.js` (jQuery tabanlı)
- `_pages/_draft/books.html`
- `_includes/search-lunr.html` (navbar’da devre dışı)
