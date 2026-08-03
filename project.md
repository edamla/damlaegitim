# Damla Okul — Proje Mimarisi

> **Dokümantasyon:** Bu projenin belgeleri üç dosyada toplanmıştır; mimari, kurulum veya UI değişikliklerinde ilgili belgeleri birlikte güncelleyin:
> - [README.md](README.md) — Genel bakış, kurulum ve hızlı başlangıç
> - [project.md](project.md) — Teknik mimari ve geliştirme kuralları *(bu dosya)*
> - [design.md](design.md) — Stil, tasarım sistemi ve UI bileşenleri

Bu belge, [damlaokul.com](https://damlaokul.com) (Damla Okul) statik sitesinin teknik yapısını, dosya organizasyonunu ve geliştirme kurallarını açıklar. Stil, renk, tipografi ve bileşen tasarımı için [design.md](design.md) dosyasına bakın.

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

Stil dosyaları ve sorumluluk ayrımı [design.md](design.md) dosyasında ayrıntılı olarak tanımlıdır.

Özet: `theme.css` (bileşen + token) → `app.css` (Bootstrap override). `bootstrap.min.css` **düzenlenmez**.

---

## Klasör Yapısı

```
damlaegitim/
├── _config.yml           # Site ayarları, koleksiyonlar, plugin’ler
├── _books/               # Ürünler (kitap / eğitim seti) — ~187 kayıt
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
│   ├── subset_font.sh            # Tüm OTF/TTF → WOFF2 subset (install.sh)
│   ├── normalize_book_frontmatter.rb   # Kitap front matter sıralama/normalize (`preview_link`, `examlink`, `damlaurl` korunur)
│   └── fill_preview_link_from_config.rb # Tek seferlik: boş preview_link → varsayılan CDN URL
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
| `eanimage.html` | Kitap kapak `<picture>` + koşullu WebP (`eanimage` partial) |
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

- Mobil-öncelik `<picture>`: mobil webp/jpeg önce, desktop `min-width: 768px`
- İlk slide `<img src>` mobil jpeg; `fetchpriority="high"`, `width`/`height` ipucu
- Preload: mobil **webp** (`max-width: 767px`); desktop webp veya jpeg (`min-width: 768px`) — anasayfa head
- `tiny-slider.js` + `slider-init.js` defer; inline init kaldırıldı
- Diğer slide'lar: Tiny Slider `lazyload: true` + `loading="lazy"`
- `tiny-slider.css` anasayfa head'de preload + link (body içi link yok)

### Görseller

- Kitap kartları: `<picture>` + koşullu WebP, `loading="lazy"`, `fetchpriority="low"`
- jpg/png **Photoshop** ile optimize edilir (resize/sıkıştırma); ImageMagick resize kullanılmaz
- `.webp` `scripts/generate_webp.sh` ile otomatik üretilir (`start.sh` hook)
- `_data/webp_manifest.yml` — mevcut webp listesi; şablonlarda koşullu `<source type="image/webp">`
- `install.sh` → `install_image_tools.sh`: Windows'ta winget ile ImageMagick + libwebp kurulumu
- `scripts/refresh_image_paths.sh` — winget kurulum yollarını Git Bash PATH'ine ekler
- Araç yoksa (`cwebp` / ImageMagick) site jpg ile çalışır, 404 oluşmaz
- `scripts/check_images.sh` büyük dosyaları raporlar (dosyaya dokunmaz; ImageMagick `identify` kullanır)
- `start.sh` her geliştirme oturumunda görsel kontrolü ve webp üretimini denemek

### JavaScript (TBT / TTI)

- Lunr araması lazy-load: `lunr.js` ve indeks yalnızca arama açılınca yüklenir
- Arama indeksi: `_pages/search-index.json` → `/assets/search-index.json` (build-time JSON)
- `book-filter.js` yalnızca anasayfa ve `/urunler`; anasayfa init `requestIdleCallback` (fallback `setTimeout`)
- Bootstrap `defer` ile yüklenir

### Fontlar ve CSS

- Font Awesome yerel (`assets/fonts/fontawesome/`), CDN kaldırıldı
- Raykjavik WOFF2 subset (~26 KB); TTF repo'da kalır, servis edilmez
- Raykjavik font preload (`default.html`)
- `spotlight.css` async yükleme (`media="print" onload`)
- `.book-genre-group`: `content-visibility: auto` (below-fold paint maliyeti)

### Cloudflare mobil benchmark (referans)

Skor ~55; LCP ~11.5 s, TTI ~13.3 s (büyük mobil jpeg, senkron slider JS). Kod düzeltmeleri sonrası Cloudflare Speed Test ile mobil retest önerilir.

### Instagram Carousel

- Behold feed isteği `IntersectionObserver` ile carousel viewport'a girince başlar

### Cloudflare

- Şu an DNS-only (gri bulut); proxy veya cache ayarı bu repoda dokümante edilmez.

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

Ana navigasyon `default.html` içinde `id="MagicMenu"` ile tanımlıdır; scroll sırasında **her zaman üstte sabit** kalır.

Yapı, responsive davranış ve görsel stiller [design.md — Site Navbar](design.md#1-site-navbar-magicmenu) bölümünde tanımlıdır.

### `nav.js`

- `--nav-height` CSS değişkenini navbar yüksekliğine göre günceller (`ResizeObserver` ile mobil menü açılınca da)
- Scroll’da `site-nav--scrolled` sınıfı ile hafif gölge ekler

---

## Kitap Detay Sayfası (`book.html`)

Ürün detay layout’u `book-page` sınıfı ile işaretlenir. Etiket stilleri, prose düzeni ve popup görünümü [design.md — Kitap Detay](design.md#6-kitap-detay-book-page) bölümünde tanımlıdır.

### Üst alan etiketleri

| Alan (front matter) | Görünüm |
|---------------------|---------|
| `anatemalar` | `#etiket` (yeşil) |
| `kavramlar` | `@etiket` (turuncu) |

`kavramlar` her kitabın kendi front matter’ında tanımlanır. Yaml’daki metin `@` önekiyle küçük harfe çevrilerek gösterilir.

### Aksiyon butonları ve popup

Ön Okuma, Tanıtım, Bilgi, İncele ve HDS butonları `.js-book-action` ile [`popup.html`](_includes/popup.html) üzerinden açılır:

| `data-popup-type` | Davranış |
|-------------------|----------|
| `info` | Tedarik bilgisi modal (mobil + masaüstü) |
| `iframe` | Tam ekran iframe (ön okuma, incele, HDS) |
| `youtube` | YouTube embed |

Masaüstünde iframe/youtube popup; mobilde yeni sekme. `info` popup’u `prefers-color-scheme: dark` destekler.

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

`site.books` koleksiyonu; alanlar: `title`, `authors`, `categories`, `grades`, `genre`, `anatemalar`, `tags`, `body`.

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

Şu an [`index.html`](index.html) içinde slider ile kitap listesi arasında include edilir. Görsel tasarım [design.md — Instagram Carousel](design.md#8-instagram-carousel-ig-carousel) bölümünde tanımlıdır.

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

Footer düzeni ve stiller [design.md — Site Footer](design.md#2-site-footer-site-footer) bölümünde tanımlıdır.

---

## Ürün (Kitap) Front Matter Örneği

```yaml
---
layout: book
title: "Deyim Öyküleri 5 Kitap"
grades: [3]
genre: story          # education | story
anatemalar: ["Değerler Eğitimi", "Macera", "Gizem"]   # yeşil # etiketler
kavramlar: ["Dil Bilim", "Milli Kültür", "Zaman Mekan"]   # turuncu @ etiketler (kitap front matter)
categories: ["Çocuk", "Hikaye"]
ean: 9786053832874
preview_link: "https://cdn.e-damla.com.tr/PUBLIC/ornek-sayfalar/9786053832874/index.html"
examlink: ""   # HDS yoksa boş; doluysa tam PDF URL (ör. https://cdn.e-damla.com.tr/PUBLIC/hds_pdf/y/...)
damlaurl: ""   # Damla Yayınevi ürün sayfası; boşsa Bilgi → tedarik popup
languages: ["Türkçe"]
page: Her Biri 64
size: "14x20cm"
publish-number: 1443
cover: "Karton Kapak"
---
```

Markdown gövdesi ürün açıklaması olarak `book.html` içindeki `.prose--display` alanında render edilir. `**TEMALAR:**` gibi kalın başlıklar ve madde listeleri bu alanda stillenir.

Ön izleme URL’si kitap front matter’ındaki `preview_link` alanında tutulur. `preview_link` doluysa İncele butonu ve `previewbook` iframe görünür; boşsa görünmez. Eksik kitaplarda varsayılan desen: `https://cdn.e-damla.com.tr/PUBLIC/ornek-sayfalar/{ean}/index.html`; bazı kitaplarda özel path’ler (`damlaegitim/`, `/mobile/` vb.) korunur. `/urun-inceleme-linkleri` sayfası `preview_link` dolu tüm kitapları listeler.

HDS PDF linkleri kitap front matter’ındaki tam `examlink` URL’si ile tanımlanır; `book.html` içinde `examlink` doluysa HDS butonu görünür, boş veya yoksa görünmez. Site genelinde `examlink` için `_config.yml` ayarı yoktur.

### `examlink` (HDS)

| Durum | Front matter | Kitap sayfası |
|-------|--------------|---------------|
| HDS yok | `examlink: ""` | HDS butonu görünmez |
| HDS var | Tam CDN URL | HDS butonu görünür (popup iframe) |

Örnek URL: `https://cdn.e-damla.com.tr/PUBLIC/hds_pdf/y/deyim-oykuleri-y.pdf`

`scripts/normalize_book_frontmatter.rb` tüm kitaplarda `examlink` satırını korur; eksikse `examlink: ""` yazar, göreli dosya adı verilmişse tam URL’ye çevirir.

### `damlaurl` (Bilgi)

| Durum | Front matter | Kitap sayfası |
|-------|--------------|---------------|
| URL yok | `damlaurl: ""` | Bilgi → tedarik bilgisi popup |
| URL var | Tam ürün sayfası URL | Bilgi → iframe popup |

Örnek URL: `https://www.damlayayinevi.com.tr/...`

`scripts/normalize_book_frontmatter.rb` tüm kitaplarda `damlaurl` satırını korur; eksikse `damlaurl: ""` yazar. Eski `damlayayinevi` front matter alanı varsa `damlaurl`’a taşınır. Site genelinde `buyout` veya `damlayayinevi` config ayarı yoktur.

### `preview_link` bakımı

| Araç | Görev |
|------|-------|
| `scripts/fill_preview_link_from_config.rb` | `preview_link` boş + `ean` dolu kitaplara varsayılan CDN URL yazar; mevcut URL’lere dokunmaz |
| `scripts/normalize_book_frontmatter.rb` | Front matter sıralar; `preview_link`, `examlink` ve `damlaurl` Standart Book Attributes altında korunur |

Yeni kitap eklerken `preview_link` doğrudan front matter’a yazılır; özel path gerekmezse `{ean}` ile varsayılan desen kullanılır.

---

## Ürün İnceleme Linkleri Sayfası

| Özellik | Değer |
|---------|-------|
| Dosya | [`_pages/linkler.html`](_pages/linkler.html) |
| URL | `/urun-inceleme-linkleri` |
| Layout | `page` (`show_title: false`) |
| Veri | `site.books` → `preview_link` dolu kitaplar (`sort: title`) |
| Stil / JS | Sayfa içi inline `<style>` + `<script>` (include yok) |
| Footer | `footer_show: true`, `footer_order: 15` |

Kart düzeni: solda kapak (`eanimage.html`), sağda sınıf rozeti + başlık + dört aksiyon — Kitabı incele (`preview_link`), Kitaba git (ürün URL), Whatsappda paylaş, Linki kopyala. Arama kutusu başlık ve sınıf rozeti üzerinde client-side filtre uygular (`toLocaleLowerCase('tr-TR')`).

Görsel tasarım [design.md — Ürün İnceleme Linkleri](design.md#13-ürün-inceleme-linkleri-review-links) bölümünde tanımlıdır.

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
| `_includes/ai-seo-crawler-book.html` | Kitap sayfaları (`grades`, `genre`, `anatemalar`, `kavramlar`) |
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
2. Front matter doldur (`title`, `grades`, `genre`, `ean`, `preview_link`, `examlink`, `damlaurl`…)
3. `preview_link` — ön izleme URL’si; boş bırakılırsa `scripts/fill_preview_link_from_config.rb` ile varsayılan desen yazılabilir
4. `examlink` — HDS PDF tam URL’si; yoksa `examlink: ""` (HDS butonu görünmez)
5. `damlaurl` — Damla Yayınevi ürün sayfası tam URL’si; yoksa `damlaurl: ""` (Bilgi → tedarik popup)
6. İsteğe bağlı `description:` — yoksa build sırasında otomatik üretilir
7. Kapak görselini `assets/images/ean/{ean}.jpg` olarak ekle (jpg/png optimize et; webp `sh start.sh` ile otomatik)
8. `sh scripts/check_images.sh` ile boyut kontrolü (veya `sh start.sh`)
9. `sh start.sh` ile kontrol et
10. `git push`

---

## Yeni Bileşen / Stil Ekleme

1. Tasarım kuralları ve dosya seçimi → [design.md — Yeni Stil Ekleme Rehberi](design.md#yeni-stil-ekleme-rehberi)
2. Partial gerekiyorsa → `_includes/` altına ekle
3. HTML’de Bootstrap grid class’ları (`row`, `col-*`) kullanılabilir

---

## Harici Bağımlılıklar

| Kaynak | Kullanım |
|--------|----------|
| `cdn.e-damla.com.tr` | Kitap `preview_link` ön izleme sayfaları; `examlink` HDS PDF’leri |
| `feeds.behold.so` | Instagram carousel JSON feed |
| Google Analytics | `G-PR1C1WGQB6` (`site.google_analytics`; yalnızca production) |
| Cloudflare | DNS (şu an proxy kapalı — gri bulut) |

Font Awesome artık yerel olarak `assets/fonts/fontawesome/` altından servis edilir; harici CDN kullanılmaz.

---

## Bilinen Legacy Dosyalar

Aşağıdaki dosyalar geçmişten kalma olabilir; aktif kullanılmıyorsa temizlenebilir:

- `assets/js/theme.js` (jQuery tabanlı; `loadSearch()` kullanılmıyor)
- `_pages/_draft/books.html`
