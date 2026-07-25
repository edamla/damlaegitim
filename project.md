# Damla Okul — Proje Mimarisi

Bu belge, [damlaokul.com](https://damlaokul.com) (Damla Okul) statik sitesinin teknik yapısını, dosya organizasyonunu ve geliştirme kurallarını açıklar.

## Genel Bakış

| Özellik | Değer |
|---------|-------|
| Tür | Statik site (Jamstack) |
| Motor | [Jekyll](https://jekyllrb.com/) 4.x |
| Dil | Türkçe (`language: tr`) |
| Yayın | GitHub Pages (`CNAME` → `damlaokul.com`) |
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
│  _includes/  →  book-card, slider, instagram-carousel, search, footer │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Statik çıktı (_site/)                                      │
│  HTML + assets/css + assets/js + assets/images              │
└──────────────────────────┬──────────────────────────────────┘
                           │ git push
                           ▼
                    GitHub Pages (damlaokul.com)
```

---

## CSS Katmanları

Stil üç katmanlıdır. Özelleştirme **asla** Bootstrap dosyasına yazılmaz.

```
bootstrap.min.css        →  Framework (Bootstrap 5.3, statik dosya)
fontawesome-all.min.css  →  Font Awesome 5.15.4 (yerel, assets/fonts/fontawesome/)
theme.css                →  Tasarım sistemi (token, bileşen, layout)
app.css                  →  Bootstrap override (renk, watermark, geçici fix)
spotlight.css            →  Arama modal stilleri (async yükleme)
tiny-slider.css          →  Anasayfa slider (yalnızca slider.html içinde)
buyout.css               →  E-ticaret barı (yalnızca kitap/katalog detay)
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
--font-nav: "Geometric Sans", system-ui, sans-serif;
--font-display: "Punta", sans-serif;
--font-sans: "Raykjavik", system-ui, sans-serif;
--font-serif: var(--font-sans);
--nav-height: 4rem;
--book-card-media-height: 220px;
--book-card-info-height: 3rem;
```

### Tipografi

Font dosyaları `assets/fonts/` altında yerel olarak servis edilir; `@font-face` tanımları `theme.css` başında.

| Font | Dosya | Kullanım alanı | CSS seçici |
|------|-------|----------------|------------|
| Geometric Sans | `assets/fonts/geometric-sans/geometric.woff2` | Navbar menü linkleri | `.site-nav .navbar-nav.me-auto .nav-link` |
| Punta | `assets/fonts/punta/Punta-Light.woff2` | Sınıf filtresi, tür başlıkları | `.grade-nav`, `.book-genre-heading` |
| Raykjavik | `assets/fonts/raykjavik/reykjavik-rounded-regular.woff2` | Genel site metni | `body`, `--font-sans` |
| Font Awesome | `assets/fonts/fontawesome/*.woff2` | İkonlar (`fas`, `fab`) | `fontawesome-all.min.css` |

**Raykjavik:** Orijinal TTF (`reykjavik-rounded-regular.ttf`, ~311 KB) repo'da kalır; ziyaretçiye yalnızca WOFF2 subset (~26 KB) servis edilir.

**Geometric Sans / Punta:** CSS yalnızca WOFF2 referanslar; OTF dosyaları repo'da kalır.

**Tüm fontlar:** `sh scripts/subset_font.sh` komutu `assets/fonts/` altındaki tüm OTF/TTF dosyalarından WOFF2 üretir (`fontawesome/` hariç; aynı isimde `.otf` varsa `.ttf` atlanır). Karşılık gelen `.woff2` zaten varsa ve kaynak dosyadan yeniyse atlanır. `monolight/` ve `reykjavik-rounded-slab-reg` dahil — CSS'te referans olmasa da WOFF2 varyantları oluşturulur.

**Font Awesome:** CDN yerine tam paket `assets/fonts/fontawesome/` altında yerel olarak tutulur. CSS: `assets/css/fontawesome-all.min.css`.

HTML partial’larında (`menu-header`, `book-grade-nav`, `book-home-groups`) değişiklik gerekmez; mevcut class yapısı yeterlidir.

### Kitap kartı (`.book-card`)

Kartlar [`book-home-groups.html`](_includes/book-home-groups.html) içinde grid’de render edilir. Tüm kartlar sabit genişlik ve yüksekliğe sahiptir.

| Eleman | Class | Davranış |
|--------|-------|----------|
| Kart | `.book-card` | Sabit toplam yükseklik (görsel + başlık alanı + padding) |
| Resim kutusu | `.book-card__media` | Sabit yükseklik (`--book-card-media-height`), `object-fit: contain` |
| İsim kutusu | `.book-card__info` | Sabit yükseklik (`--book-card-info-height`), en fazla 2 satır başlık |
| Başlık | `.book-card__title` | En fazla 2 satır (`line-clamp`) |

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
│   │   ├── fontawesome-all.min.css
│   │   ├── theme.css
│   │   ├── app.css
│   │   ├── spotlight.css
│   │   ├── tiny-slider.css
│   │   └── buyout.css
│   ├── fonts/
│   │   ├── fontawesome/          # Font Awesome 5.15.4 webfonts (tam paket)
│   │   ├── geometric-sans/
│   │   ├── punta/
│   │   ├── raykjavik/            # TTF (arşiv) + WOFF2 (servis edilen)
│   │   └── monolight/            # CSS'te referans yok; repo'da kalır
│   ├── js/
│   │   ├── bootstrap.bundle.min.js
│   │   ├── nav.js                # Navbar scroll (vanilla JS)
│   │   ├── book-filter.js        # Sınıf/tür filtreleme (yalnızca / ve /urunler)
│   │   ├── lunr.js               # Arama (lazy-load; açılınca yüklenir)
│   │   ├── tiny-slider.js        # Anasayfa slider
│   │   └── theme.js              # Eski (jQuery) — kullanılmıyor
│   └── images/
│       ├── slides/               # Anasayfa slider görselleri (webp otomatik üretilebilir)
│       ├── ean/                  # Kitap kapak görselleri (webp otomatik üretilebilir)
│       └── favicon/
├── _data/
│   └── webp_manifest.yml         # Otomatik: mevcut .webp listesi (generate_webp.sh)
├── scripts/
│   ├── install_image_tools.sh    # WebP/ImageMagick kurulumu (install.sh; winget/brew/apt)
│   ├── generate_webp.sh          # jpg/png → .webp + manifest güncelleme (start.sh hook)
│   ├── refresh_image_paths.sh    # Windows winget PATH düzeltmesi (dahili)
│   ├── check_images.sh           # Büyük görsel uyarı raporu (start.sh hook)
│   ├── check_fonts.sh            # Font / WOFF2 uyarı raporu (install.sh)
│   └── subset_font.sh            # Tüm OTF/TTF → WOFF2 subset (install.sh)
├── docs/
│   └── CLOUDFLARE.md             # Cloudflare proxy/cache ayar rehberi
├── index.html            # Anasayfa
├── Gemfile               # Ruby bağımlılıkları
├── CNAME                 # damlaokul.com
├── install.sh            # İlk kurulum: bundle, fonttools, WOFF2, görsel araçları, jekyll build
├── start.sh              # Geliştirme: check_images + generate_webp hook + jekyll serve
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
| `previewbook.html` | Tam ekran önizleme |
| `catalog.html` | Katalog detay + iframe görüntüleyici |
| `post.html` | Blog yazısı |
| `person.html` / `illustrator.html` / `translator.html` | Kişi profilleri |

Tüm layout’lar `layout: default` zinciri üzerinden `default.html`’i extend eder.

---

## Önemli Include’lar

| Dosya | Görev |
|-------|-------|
| `menu-header.html` | Ana navigasyon linkleri |
| `footer-menu.html` | 3 sütunlu site footer (ürünler, önemli bilgiler, iletişim) |
| `contact-info.html` | Site geneli iletişim bilgileri (`site.contact_*`, footer ve iletişim sayfası) |
| `menu-socialmedia.html` | Sosyal medya ikonları |
| `slider.html` | Anasayfa Tiny Slider (`<picture>`, WebP, lazyload, fetchpriority) |
| `instagram-carousel.html` | Anasayfa Instagram carousel (`okul.damla`, Behold JSON feed) |
| `book-grade-nav.html` | Sınıf sekmesi + tür alt menüsü |
| `book-home-groups.html` | Anasayfa kitap listesi (Eğitim / Hikaye) |
| `book-card.html` | Tek kitap kartı partial (`<picture>` + WebP, native lazy loading) |
| `book-grade-filter.html` | Eski sınıf checkbox dropdown’u (artık kullanılmıyor) |
| `search-lunr.html` | Spotlight arama (lazy-load Lunr + JSON indeks, modal UI, navbar tetikleyici) |
| `popup.html` | Kitap detay popup’ları (Bilgi, ön okuma iframe, YouTube; koyu tema desteği) |
| `tracking-header.html` / `tracking-footer.html` | Google Analytics |

---

## JavaScript

| Dosya | Yükleme | Görev |
|-------|---------|-------|
| `bootstrap.bundle.min.js` | `defer`, tüm sayfalar | Collapse, dropdown, modal |
| `nav.js` | `defer`, tüm sayfalar | Sticky navbar yüksekliği (`--nav-height`), scroll gölgesi |
| `book-filter.js` | `defer`, yalnızca `/` ve `/urunler` | Sınıf/tür filtreleme + hash URL senkronizasyonu |
| `lunr.js` | **Lazy** — arama açılınca | Spotlight kitap araması (client-side indeks) |
| `tiny-slider.js` | Anasayfa (`slider.html`) | Slider + lazyload |

jQuery kullanılmaz. `lazyload.js` kaldırıldı; görseller native `loading="lazy"` ve `<picture>` ile yönetilir.

`instagram-carousel.html` kendi inline `<script>` bloğunu taşır; feed `IntersectionObserver` ile viewport'a girince yüklenir.

`search-lunr.html` navbar Spotlight aramasını sağlar. `mode` parametresiyle navbar tetikleyicisi (`desktop` / `mobile`) veya script bloğu (`mode` olmadan) ayrı include edilir.

- **Masaüstü (`mode='desktop'`)** — Navbar collapse içinde tam arama kutusu (`Ctrl+K` kısayolu)
- **Mobil (`mode='mobile'`)** — Logo ile hamburger arasında minimal arama çubuğu (`Kitap ara...`); collapse dışında, her zaman görünür

---

## Performans Optimizasyonu

Site hızı için uygulanan başlıca önlemler:

### LCP (Hero Slider)

- `<picture>` ile desktop/mobil ve WebP/JPEG ayrımı; çift görsel indirmesi önlenir
- İlk slide: `fetchpriority="high"` + `<link rel="preload">` (yalnızca anasayfa)
- Diğer slide'lar: Tiny Slider `lazyload: true` + `loading="lazy"`
- `tiny-slider.css` yalnızca anasayfada yüklenir

### Görseller

- Kitap kartları: `<picture>` + koşullu WebP (`_data/webp_manifest.yml` tabanlı), `loading="lazy"`
- jpg/png optimize edilir; `.webp` `scripts/generate_webp.sh` ile otomatik üretilir (`start.sh` hook)
- `_data/webp_manifest.yml` — mevcut webp listesi; şablonlarda koşullu `<source type="image/webp">`
- `install.sh` → `install_image_tools.sh`: Windows'ta winget ile ImageMagick + libwebp kurulumu
- `scripts/refresh_image_paths.sh` — winget kurulum yollarını Git Bash PATH'ine ekler
- Araç yoksa (`cwebp` / ImageMagick) site jpg ile çalışır, 404 oluşmaz
- `scripts/check_images.sh` büyük dosyaları raporlar (dosyaya dokunmaz; ImageMagick `identify` kullanır)
- `start.sh` her geliştirme oturumunda görsel kontrolü ve webp üretimini denemek

### JavaScript (TBT / TTI)

- Lunr araması lazy-load: `lunr.js` ve indeks yalnızca arama açılınca yüklenir
- Arama indeksi: `_pages/search-index.json` → `/assets/search-index.json` (build-time JSON)
- `book-filter.js` yalnızca anasayfa ve `/urunler` sayfasında
- Bootstrap `defer` ile yüklenir

### Fontlar ve CSS

- Font Awesome yerel (`assets/fonts/fontawesome/`), CDN kaldırıldı
- Raykjavik WOFF2 subset (~26 KB); TTF repo'da kalır, servis edilmez
- Raykjavik font preload (`default.html`)
- `spotlight.css` async yükleme (`media="print" onload`)

### Instagram Carousel

- Behold feed isteği `IntersectionObserver` ile carousel viewport'a girince başlar

### Cloudflare

- Şu an DNS-only (gri bulut). Proxy ayarları için [`docs/CLOUDFLARE.md`](docs/CLOUDFLARE.md)

### Yerel Araçlar

```bash
# İlk kurulum (git clone sonrası)
sh install.sh                       # bundle, fonttools, WOFF2, görsel araçları, jekyll build

# Geliştirme (hook'lar yalnızca burada)
sh start.sh                         # check_images + generate_webp + jekyll serve

# Manuel script'ler
sh scripts/install_image_tools.sh   # WebP/ImageMagick (Windows: winget)
sh scripts/generate_webp.sh         # .webp üretimi + webp_manifest.yml
sh scripts/check_images.sh          # Büyük görsel uyarı raporu
sh scripts/check_images.sh slides   # Yalnızca slider
sh scripts/check_images.sh ean      # Yalnızca kitap kapakları
sh scripts/check_fonts.sh           # Font / WOFF2 uyarı raporu
sh scripts/subset_font.sh           # Tüm OTF/TTF → WOFF2 subset (fontawesome hariç)
```

### `install.sh` vs `start.sh`

| | `install.sh` | `start.sh` |
|---|-------------|------------|
| Amaç | Sıfırdan kurulum | Günlük geliştirme |
| Ruby / bundle | `bundle install` | `Gemfile.lock` kontrolü |
| Fontlar | `subset_font.sh`, `check_fonts.sh` | — |
| Görsel araçları | `install_image_tools.sh` (winget/brew/apt) | — |
| Görsel hook'ları | — | `check_images.sh`, `generate_webp.sh` |
| Jekyll | `jekyll build` (doğrulama) | `jekyll serve` |
| `_data/webp_manifest.yml` | Yoksa oluşturur | `generate_webp.sh` günceller |

---

## Navbar (`#MagicMenu`)

Ana navigasyon `default.html` içinde `id="MagicMenu"` ile tanımlıdır; scroll sırasında **her zaman üstte sabit** kalır (eski gizle/göster davranışı kaldırıldı).

### Yapı

```
.container
├── .site-nav__bar          ← mobil: logo + arama + hamburger (tek satır)
│   ├── .navbar-brand
│   ├── .site-nav__search-bar (d-md-none)
│   └── .navbar-toggler
└── .navbar-collapse        ← menü linkleri (mobilde alt satır, tam genişlik)
```

Masaüstünde (`≥992px`) `.site-nav__bar` için `display: contents` kullanılır; Bootstrap’ın yatay navbar düzeni korunur.

### `nav.js`

- `--nav-height` CSS değişkenini navbar yüksekliğine göre günceller (`ResizeObserver` ile mobil menü açılınca da)
- Scroll’da `site-nav--scrolled` sınıfı ile hafif gölge ekler
- Navbar `position: fixed; top: 0; z-index: 1030`

---

## Kitap Detay Sayfası (`book.html`)

Ürün detay layout’u `book-page` sınıfı ile işaretlenir.

### Üst alan etiketleri

| Alan (front matter) | Görünüm | Stil |
|---------------------|---------|------|
| `subjects` | `#etiket` | Yeşil metin (`--color-primary`), silik gri pill arka plan |
| `concepts` | `@etiket` | Turuncu metin (`#c88400`), silik gri pill arka plan |

`concepts` iki biçimi destekler:

1. **Anahtar** — `_config.yml` → `concepts` listesindeki `key` (ör. `sozel-dilsel` → `@sözel-dilsel`)
2. **Serbest metin** — Anahtar eşleşmezse yaml’daki metin doğrudan gösterilir (ör. `@dil bilim gelişimi`)

### Metadata listesi

Sol sütundaki özellik listesi (yayın no, sayfa, boyut vb.) `.book-meta` flex düzeniyle ikon ve metin hizasını korur.

### İçerik alanı (`.prose--display`)

Markdown gövdesi `.prose--display` ile render edilir:

- `**kalın**` metin: `font-synthesis: weight` ile aynı font ailesinde sentetik bold
- Liste ve başlık aralıkları sıkılaştırılmıştır
- Mobilde (`.book-page`) başlık ortalanır; masaüstünde sola hizalı kalır

### Aksiyon butonları ve popup

Ön Okuma, Tanıtım, Bilgi, İncele, HDS butonları `.js-book-action` ile [`popup.html`](_includes/popup.html) üzerinden açılır:

| `data-popup-type` | Davranış |
|-------------------|----------|
| `info` | Tedarik bilgisi modal (mobil + masaüstü) |
| `iframe` | Tam ekran iframe (ön okuma, incele, HDS) |
| `youtube` | YouTube embed |

`info` popup’u `prefers-color-scheme: dark` için metin renkleri ayarlanmıştır.

---

## Spotlight Arama

Navbar üzerinden kitap araması yapılır. macOS Spotlight benzeri tam ekran modal açılır.

### Dosyalar

| Dosya | Görev |
|-------|-------|
| `_includes/search-lunr.html` | Lazy-load arama scripti, navbar tetikleyici |
| `_pages/search-index.json` | Build-time arama indeksi (`/assets/search-index.json`) |
| `assets/js/lunr.js` | Lunr.js 2.1.5 kütüphanesi (arama açılınca yüklenir) |
| `assets/css/spotlight.css` | Modal stilleri (async yükleme) |

### İndeks kapsamı

`site.books` koleksiyonu; alanlar: `title`, `authors`, `categories`, `grades`, `genre`, `subjects`, `tags`, `body`.

İndeks her sayfaya gömülmez; `/assets/search-index.json` olarak ayrı endpoint'ten fetch edilir. Bu sayede sayfa yüklenirken Lunr indeksleme maliyeti oluşmaz.

### Kullanım

- Navbar’daki arama kutusuna tıklama (masaüstü tam kutu; mobil logo–hamburger arası minimal çubuk)
- `Ctrl+K` / `⌘K` klavye kısayolu
- Enter → ilk sonuca git; ESC → kapat

Eski `theme.js` içindeki `loadSearch()` (`content.json` tabanlı) kullanılmaz.

---

## Instagram Carousel

Anasayfada `@okul.damla` hesabının güncel gönderilerini yatay carousel olarak gösterir. Modül tek dosyada inline HTML, CSS ve vanilla JS içerir.

### Yapılandırma (`_config.yml`)

```yaml
instagram_carousel:
  username: okul.damla
  profile_url: https://instagram.com/okul.damla
  feed_url: ''   # Behold JSON feed URL
  limit: 12
```

`feed_url` boşsa modül build’i kırmaz; kullanıcıya yapılandırma mesajı ve Instagram profil linki gösterilir.

### Veri kaynağı

Instagram, statik siteden doğrudan feed çekmeye izin vermez. [Behold.so](https://behold.so) JSON feed kullanılır:

1. Behold hesabında `okul.damla` kaynak olarak bağlanır
2. Çıktı tipi **JSON** olan feed oluşturulur
3. `https://feeds.behold.so/XXXX` URL’si `feed_url` alanına yazılır

### Kullanım

```liquid
{% include instagram-carousel.html %}
```

Şu an [`index.html`](index.html) içinde slider ile kitap listesi arasında include edilir. Stiller site token’larıyla uyumludur (`--color-primary`, `--font-display`, `--radius`).

---

## Footer

Site alt bilgisi [`_includes/footer-menu.html`](_includes/footer-menu.html) ile 3 sütunlu olarak render edilir. `default.html` layout’u bu partial’ı otomatik include eder.

| Sütun | İçerik | Kaynak |
|-------|--------|--------|
| Ürünler | Eğitim Kitapları, Hikaye Kitapları, Kataloglar | Sabit `/urunler` linkleri + `site.pages` (`permalink: /kataloglar`) |
| Önemli Bilgiler | Hakkımızda, Gizlilik vb. | `_pages` front matter: `footer_show: true`, `footer_order` |
| Adres & İletişim | Telefon, e-posta, adres, sosyal | `_config.yml` `contact_*` + `menu-socialmedia.html` |

### Site geneli iletişim (`_config.yml`)

İletişim bilgileri kök seviyede tanımlanır (footer bloğu değil; sosyal ayarlar gibi site ayarı):

```yaml
contact_phone: "+90 212 514 28 28"
contact_phone_href: "tel:+902125142828"
contact_email: "iletisim@damlayayinevi.com.tr"
contact_address: "Alemdar Mh. Prof. Kazım İsmail Gürkan Cad. No:8 Fatih, 34110 İstanbul"
```

Jekyll’da erişim: `{{ site.contact_phone }}`, `{{ site.contact_email }}` vb.

### `contact-info.html` partial

Tek kaynak; footer ve iletişim sayfası buradan beslenir:

```liquid
{% include contact-info.html mode='footer' %}  {# footer sütunu #}
{% include contact-info.html mode='page' %}   {# iletişim sayfası gövdesi #}
```

[`_pages/iletisim.md`](_pages/iletisim.md) harita iframe’ini sayfa gövdesinde tutar; telefon/e-posta/adres tekrarı partial üzerinden gelir.

### Footer’da gösterilecek sayfalar

`_pages` front matter:

```yaml
footer_show: true
footer_order: 10
```

```liquid
{% assign footer_pages = site.pages
  | where_exp: "p", "p.footer_show == true"
  | sort: "footer_order" %}
```

Stiller `assets/css/theme.css` içinde `.site-footer__*` ve `.contact-info__*` sınıflarıyla tanımlıdır.

---

## Ürün (Kitap) Front Matter Örneği

```yaml
---
layout: book
title: "Deyim Öyküleri 5 Kitap"
grades: [3]
genre: story          # education | story
subjects: ["Değerler Eğitimi", "Macera", "Gizem"]   # yeşil # etiketler
concepts: ["sozel-dilsel", "icsel"]                 # turuncu @ etiketler (anahtar veya serbest metin)
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

Markdown gövdesi ürün açıklaması olarak `book.html` içindeki `.prose--display` alanında render edilir. `**TEMALAR:**` gibi kalın başlıklar ve madde listeleri bu alanda stillenir.

---

## Filtreleme Mantığı

Anasayfa ve `/urunler` aynı bileşenleri paylaşır: `book-grade-nav.html` + `book-home-groups.html` + `book-filter.js`

- Sınıf seçimi → `data-grades` attribute’u ile eşleşme
- Tür (Eğitim/Hikaye) → `data-genre` attribute’u
- Hedef selector: `.listbooks-home-item`
- Genre grupları: `.book-genre-group` (boş gruplar gizlenir)

Filtreleme tamamen client-side çalışır; Jekyll rebuild gerekmez.

### Hash tabanlı paylaşılabilir URL’ler

Filtre değişince URL hash güncellenir; sayfa hash ile yüklendiğinde filtre otomatik uygulanır.

| Hash | Filtre |
|------|--------|
| `#okul-oncesi` | Sadece sınıf (tüm türler) |
| `#okul-oncesi/egitim` | Sınıf + tür |
| `#1-sinif/hikaye` | Sınıf + tür |

Örnekler: `/urunler#okul-oncesi`, `/urunler#1-sinif/egitim`, `/#2-sinif/hikaye` (anasayfa)

Okul öncesi ürünler `_books/` içinde henüz tam açılmamış olsa da URL yapısı hazırdır; ileride `grades: [0]` + `genre` ile eklenen ürünler ek JS değişikliği olmadan çalışır.

`book-grade-filter.html` eski checkbox dropdown yapısıdır; `/urunler` artık kullanmaz.

---

## Jekyll Plugin’leri

- `jekyll-feed` — RSS
- `jekyll-sitemap` — sitemap.xml
- `jekyll-seo-tag` — `{% seo %}` meta etiketleri (kitap sayfaları hariç; özel `book-seo-tags.html`)
- `jekyll-paginate` — sayfalama
- `jekyll-archives` — arşiv sayfaları
- `jekyll-figure` / `jekyll-gist` — içerik zenginleştirme

---

## SEO ve AI Crawler Altyapısı

GitHub Pages uyumlu (özel Ruby plugin yok):

| Dosya | Görev |
|-------|-------|
| `robots.txt` | Tüm crawler + AI botlara `Allow`; sitemap ve `llms.txt` referansı |
| `_pages/llms.txt` | Build-time AI içerik haritası (kitaplar, sayfalar, kataloglar) |
| `_includes/book-seo-description.html` | Kitap meta description metni üretimi |
| `_includes/book-seo-tags.html` | Kitap sayfaları için özel `<meta>` / Open Graph / Twitter |
| `_includes/book-minimal-content.html` | İnce gövdeli kitaplara otomatik SEO paragrafı |
| `_includes/structured-data-book.html` | `Product` + `Book` + `BreadcrumbList` JSON-LD |
| `_includes/structured-data-site.html` | `Organization` + `WebSite` JSON-LD |
| `_includes/ai-seo-crawler.html` | Router + visually-hidden wrapper; `default.html` include noktası |
| `_includes/ai-seo-crawler-base.html` | Ortak Damla Yayınevi marka argümanları |
| `_includes/ai-seo-crawler-book.html` | Kitap sayfaları (`grades`, `genre`, `subjects`, `concepts`) |
| `_includes/ai-seo-crawler-home.html` | Anasayfa |
| `_includes/ai-seo-crawler-catalog.html` | `/urunler` ürün listesi |
| `_includes/ai-seo-crawler-katalog.html` | Katalog detay sayfaları |
| `_includes/ai-seo-crawler-generic.html` | Hakkımızda, iletişim, blog vb. |

### Dinamik AI/SEO crawler içeriği

- **Amaç:** Öğretmen ve velilere Damla ürünlerini neden tercih etmeleri gerektiğini LLM'lere ve crawler'lara anlatan bağlamsal metin
- **Format (hibrit):** `data-ai-role="assistant-guidance"` (LLM talimat bloğu) + `data-ai-role="context-narrative"` (sayfa özel ikna paragrafı)
- **Sayfa türü algılama:** URL + layout (`book`/`previewbook`, `/`, `/urunler`, `/kataloglar`, generic)
- **Gizleme:** Include içi inline `<style>` (`.ai-seo-crawler` visually-hidden; global CSS'e eklenmez), `aria-hidden="true"`, `data-nosnippet`
- **Include zinciri:** `_layouts/default.html` → `{% include ai-seo-crawler.html %}` (`</main>` sonrası)
- **`book-minimal-content.html` ile ilişki:** Görünür SEO metni vs. gizli LLM rehberi — çoğaltma yok, farklı amaç

### Meta description otomasyonu

Kitap sayfalarında (`/urunler/*`) `description:` front matter yoksa:

1. Markdown excerpt / gövdeden (max 155 karakter)
2. Yoksa şablon: `{{ title }} — {{ grades }}. sınıf {{ genre }} kitabı. Damla Okul.`

### Yapılandırma (`_config.yml`)

- `locale: tr_TR`, `lang: tr`, `twitter.username`
- Kitap koleksiyonu varsayılanları: `lang: tr`, `type: product`, sitemap önceliği

### Build sonrası doğrulama

```bash
bundle exec jekyll build
# robots.txt, llms.txt, örnek kitap sayfası meta + JSON-LD kontrol
curl https://damlaokul.com/robots.txt
curl https://damlaokul.com/llms.txt
# Örnek sayfa HTML'inde gizli crawler bloğu
grep -l "ai-seo-crawler" _site/index.html _site/urunler.html _site/urunler/*.html | head -3
# WebP manifest ve üretilen dosyalar
grep -c 'type="image/webp"' _site/index.html   # manifest durumuna bağlı
ls _data/webp_manifest.yml assets/images/ean/*.webp 2>/dev/null | head -3
```

---

## Build ve Deploy

### İlk kurulum (`install.sh`)

Git clone sonrası Windows Git Bash / macOS / Linux:

```bash
sh install.sh
```

Sıra: Ruby/Bundler kontrolü → `bundle install` → Python `fonttools` → `subset_font.sh` → `check_fonts.sh` → `install_image_tools.sh` (Windows: `winget install ImageMagick.ImageMagick`, gerekirse `Google.Libwebp`) → `_data/webp_manifest.yml` → `jekyll build`.

**Hook yok** — görsel kontrol ve webp üretimi burada çalışmaz.

### Yerel geliştirme (`start.sh`)

```bash
# Geliştirme sunucusu (hook'lar: görsel kontrol + webp üretimi)
sh start.sh            # check_images.sh + generate_webp.sh + jekyll serve
# → http://localhost:4000
```

`start.sh` önce `refresh_image_paths.sh` ile Windows PATH'ini düzeltir; ardından `check_images.sh` ve `generate_webp.sh` hook'larını çalıştırır.

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
3. İsteğe bağlı `description:` — yoksa build sırasında otomatik üretilir
4. Kapak görselini `assets/images/ean/` altına koy (jpg/png optimize et; webp `sh start.sh` ile otomatik)
5. `sh scripts/check_images.sh` ile boyut kontrolü (veya `sh start.sh`)
6. `sh start.sh` ile kontrol et
7. `git push`

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
| `cdn.e-damla.com.tr` | Önizleme sayfaları, örnek sayfalar |
| `feeds.behold.so` | Instagram carousel JSON feed |
| Google Analytics | `G-KFMVQ3WNN3` (production) |
| Cloudflare | DNS (proxy opsiyonel; bkz. `docs/CLOUDFLARE.md`) |

Font Awesome artık yerel olarak `assets/fonts/fontawesome/` altından servis edilir; harici CDN kullanılmaz.

---

## Bilinen Legacy Dosyalar

Aşağıdaki dosyalar geçmişten kalma olabilir; aktif kullanılmıyorsa temizlenebilir:

- `assets/js/theme.js` (jQuery tabanlı; `loadSearch()` kullanılmıyor)
- `_pages/_draft/books.html`
