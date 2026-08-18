# Damla Okul — Tasarım Sistemi ve UI Mimarisi

> **Dokümantasyon:** Bu projenin belgeleri üç dosyada toplanmıştır; mimari, kurulum veya UI değişikliklerinde ilgili belgeleri birlikte güncelleyin:
> - [README.md](README.md) — Genel bakış, kurulum ve hızlı başlangıç
> - [project.md](project.md) — Teknik mimari ve geliştirme kuralları
> - [design.md](design.md) — Stil, tasarım sistemi ve UI bileşenleri *(bu dosya)*

Bu belge [damlaokul.com](https://damlaokul.com) sitesinin görsel kimliğini, CSS mimarisini, bileşen kütüphanesini ve tasarım tercihlerini tanımlar. Teknik build/deploy bilgisi için [project.md](project.md); kurulum için [README.md](README.md) dosyasına bakın.

---

## Tasarım İlkeleri

| İlke | Uygulama |
|------|----------|
| **Bootstrap tabanlı, marka üstü** | Grid ve utility class'ları Bootstrap 5.3'ten; görsel kimlik özel CSS katmanlarıyla |
| **Token öncelikli** | Renk, font, spacing değerleri `:root` CSS değişkenlerinde; hard-coded tekrar yok |
| **Katman ayrımı** | Yeni bileşen → `theme.css`; Bootstrap override → `app.css`; framework dosyasına dokunulmaz |
| **Mobil öncelikli** | Breakpoint'ler Bootstrap ile uyumlu; navbar, grade-nav ve kart grid'i mobilde önce tasarlanır |
| **Performans bilinçli** | Lazy görseller, koşullu CSS/JS yükleme, `content-visibility`, yerel fontlar |
| **Erişilebilirlik** | Semantik HTML, `aria-*` etiketleri, klavye kısayolları (`Ctrl+K`, `ESC`), yeterli kontrast |
| **Tutarlı modal dili** | Spotlight arama ve kitap popup'ları aynı cam efekti + blur + yuvarlatılmış köşe stilini paylaşır |

---

## CSS Mimari Diyagramı

```
┌─────────────────────────────────────────────────────────────┐
│  bootstrap.min.css        Bootstrap 5.3 (düzenlenmez)       │
├─────────────────────────────────────────────────────────────┤
│  fontawesome-all.min.css  İkonlar (yerel webfont)           │
├─────────────────────────────────────────────────────────────┤
│  theme.css                Tasarım sistemi: token, bileşen   │
├─────────────────────────────────────────────────────────────┤
│  app.css                  Bootstrap override, body, navbar    │
├─────────────────────────────────────────────────────────────┤
│  spotlight.css            Arama modal (async, tüm sayfalar) │
├─────────────────────────────────────────────────────────────┤
│  tiny-slider.css          Anasayfa slider (yalnızca /)      │
└─────────────────────────────────────────────────────────────┘
```

### Yükleme sırası (`default.html` head)

1. `fontawesome-all.min.css`
2. `bootstrap.min.css`
3. `theme.css`
4. `app.css`
5. Anasayfada ek: `tiny-slider.css` (preload + link)
6. `spotlight.css` — `search-lunr.html` içinde async (`media="print" onload`)

### Sorumluluk tablosu

| Dosya | Ne yazılır | Ne yazılmaz |
|-------|------------|-------------|
| `assets/css/theme.css` | `:root` token'lar, bileşen class'ları (`.book-card`, `.grade-nav`, `.site-footer`…) | Bootstrap class override, gereksiz `!important` |
| `assets/css/app.css` | `--bs-primary`, `.btn-primary`, `body` arka plan, navbar ince ayar | Yeni bileşen tanımı |
| `assets/css/bootstrap.min.css` | — | **Hiçbir değişiklik yapılmaz** |
| `assets/css/spotlight.css` | Arama modal ve tetikleyici stilleri | Genel site bileşenleri |
| `assets/css/tiny-slider.css` | Slider kütüphanesi | — |

**Kural:** Yeni kalıcı bileşen → `theme.css`. Bootstrap'ı markaya uydurmak → `app.css`.

---

## Tasarım Token'ları

Tüm token'lar `theme.css` → `:root` bloğunda tanımlıdır. Bileşenlerde mümkün olduğunca bu değişkenler kullanılır; `app.css` ve `spotlight.css` fallback değerleriyle (`var(--color-primary, #03a87c)`) uyumludur.

### Renkler

| Token | Değer | Kullanım |
|-------|-------|----------|
| `--color-primary` | `#03a87c` | Marka yeşili — linkler, vurgular, footer başlıkları, aktif durumlar |
| `--color-primary-dark` | `#028a66` | Hover, gradient bitiş, buton active |
| `--color-danger` | `#ea2f65` | Tehlike / uyarı vurguları |
| `--color-text` | `#212529` | Ana metin (Bootstrap body rengiyle uyumlu) |
| `--color-muted` | `#6c757d` | İkincil metin, placeholder |
| `--color-border` | `#dee2e6` | Kart kenarlıkları, navbar alt çizgi |
| `--color-surface` | `#fafafa` | Sayfa arka planı (`body`) |
| `--color-footer-bg` | `#25272a` | Footer koyu zemin |
| `--color-accent-concept` | `#9a6500` | Kavram pill metni, tagline border (WCAG AA) |
| `--color-accent-concept-muted` | `#fdf6e8` | Kavram pill arka planı |

**Bootstrap eşlemesi** (`app.css`):

```css
--bs-primary: #03a87c;
--bs-primary-rgb: 3, 168, 124;
--bs-link-color: #03a87c;
--bs-link-hover-color: #028a66;
--bs-body-bg: #fafafa;
--bs-border-color: #dee2e6;
```

**Semantik renkler (bileşen özel):**

| Bağlam | Renk | Class / seçici |
|--------|------|----------------|
| Konu etiketleri | `--color-primary` | `.book-curriculum__chip--unite`, `.book-card__theme` |
| Etiket pill | `--color-accent-concept` | `.book-detail__tags .tag` |
| Kavram özeti (alıntı) | `--color-accent-concept` sol border | `.book-detail__tagline` |
| Grade nav ikonları | Sınıfa göre (aşağıda) | `.grade-nav-item[data-grade="N"] .grade-nav-icons` |
| Spotlight metin | `#1d1d1f` / `#86868b` | Apple-inspired nötr gri tonları |
| Satın Al butonu | Bootstrap `text-success` | `.js-book-action` + `fa-shopping-cart` |

### Tipografi

| Token | Font ailesi | Kullanım |
|-------|-------------|----------|
| `--font-nav` | Geometric Sans | Navbar menü linkleri |
| `--font-display` | Punta (Light, 300) | Sınıf filtresi, tür başlıkları, footer başlıkları, bölüm başlıkları |
| `--font-sans` | Raykjavik | Genel site metni, `body`, kitap açıklamaları |
| `--font-serif` | `var(--font-sans)` | Kitap kartı başlıkları (şu an sans ile aynı) |

### Boşluk ve boyut

| Token | Değer | Kullanım |
|-------|-------|----------|
| `--space-4` | `1rem` | Kart içi dikey boşluk |
| `--space-6` | `1.5rem` | Kart padding |
| `--radius` | `0.5rem` | Kart, buton, Instagram carousel |
| `--shadow-sm` | `0 1px 3px rgba(0,0,0,0.08)` | Kart hover gölgesi |
| `--nav-height` | `4rem` (dinamik) | Fixed navbar yüksekliği; `nav.js` ile güncellenir |
| `--container-max` | `1280px` | Geniş ekran container sınırı |
| `--book-card-media-height` | `220px` (mobil: `160px`) | Kitap kartı kapak alanı |
| `--book-card-info-height` | `7rem` (mobil: `6.25rem`) | Kitap kartı başlık + yazar + tema alanı |

### Geçişler

- Linkler ve butonlar: `transition: all 0.2s` veya `0.15s ease`
- Kart hover: `box-shadow 0.2s ease`, kapak `transform: scale(1.02) 0.2s`
- Navbar scroll gölgesi: `box-shadow 0.2s ease-in-out`
- Modal açılış: `opacity 0.2s`, `transform scale/translateY 0.25s`

---

## Tipografi Sistemi

### Font dosyaları

| Font | Kaynak | Servis edilen | CSS `@font-face` |
|------|--------|---------------|------------------|
| Geometric Sans | `assets/fonts/geometric-sans/geometric.woff2` | WOFF2 | `theme.css` başı |
| Punta Light | `assets/fonts/punta/Punta-Light.woff2` | WOFF2 | `theme.css` başı |
| Raykjavik Rounded | `assets/fonts/raykjavik/reykjavik-rounded-regular.woff2` | WOFF2 (~26 KB subset) | `theme.css` başı |
| Font Awesome 5.15.4 | `assets/fonts/fontawesome/*.woff2` | Yerel tam paket | `fontawesome-all.min.css` |

Tüm `@font-face` tanımlarında `font-display: swap` kullanılır. Raykjavik `default.html` head'de preload edilir.

### Font atama haritası

| Alan | Font | Boyut / ağırlık |
|------|------|-----------------|
| `body` | Raykjavik | Varsayılan |
| Navbar `.nav-link` (ana menü) | Geometric Sans | `0.93rem`, bold |
| `.grade-nav-label` | Punta | `clamp(0.95rem, 1.4vw, 1.15rem)`, 600 |
| `.book-genre-heading` | Punta | `1.1rem`, 700 |
| `.site-footer__heading` | Punta | `0.85rem`, 700, uppercase, `letter-spacing: 0.04em` |
| `.book-card__title` | Raykjavik (serif token) | `1rem`, 2 satır clamp |
| `.article-headline` (kitap detay) | Raykjavik | `3.2rem` (`.display-4` ile), mobilde ortalı |
| `.book-detail__tagline` (kavram özeti) | Raykjavik | İtalik alıntı, turuncu sol border |
| `.prose--display` (ürün açıklaması) | Raykjavik | `0.95rem`, `line-height: 1.15`, `#5c636a` |
| `article` (blog) | Raykjavik | `1.1rem`, `line-height: 1.86` |

### Prose stilleri

İki prose varyantı vardır:

| Class | Kullanım | Özellik |
|-------|----------|---------|
| `.prose` | Blog / genel makale | Geniş satır aralığı, `2rem` paragraf margin |
| `.prose--display` | Kitap detay markdown gövdesi | Sıkı satır aralığı, sentetik bold (`font-synthesis: weight`), gri ton metin |

Kitap detayda `**kalın**` metin aynı font ailesinde `font-weight: 700` ile render edilir; ayrı bold font dosyası yüklenmez.

---

## Responsive Breakpoint'ler

Bootstrap 5 breakpoint'leri ile uyumlu:

| Breakpoint | Genişlik | Tasarım kararları |
|------------|----------|-------------------|
| xs / sm | `< 576px` | Grade nav 2 sütun grid; kitap grid 2 sütun |
| md | `≥ 768px` | Popup masaüstü modu; slider desktop görseli; grade submenu hover |
| lg | `≥ 992px` | Navbar yatay düzen (`display: contents`); kitap grid 4 sütun; masaüstü arama kutusu |
| xl | `≥ 1200px` | Container max 1280px |
| 1920px+ | `≥ 1920px` | `html { font-size: 17px }`, article büyütülmüş |

### Mobil navbar yapısı

```
.container
├── .site-nav__bar          ← logo + arama + hamburger (tek satır)
│   ├── .navbar-brand
│   ├── .site-nav__search-bar (d-lg-none)
│   └── .navbar-toggler
└── .navbar-collapse        ← menü linkleri (mobilde alt satır, tam genişlik)
```

Masaüstünde (`≥992px`) `.site-nav__bar { display: contents }` ile Bootstrap'ın yatay navbar düzeni korunur.

---

## Sayfa İskeleti (Shell)

### Layout hiyerarşisi

```
default.html
├── <nav id="MagicMenu" class="site-nav ... fixed-top">
├── <main class="site-content">  ← {{ content }}
├── ai-seo-crawler (gizli)
├── scripts (defer)
└── footer-menu.html
```

- `body` padding-top: `var(--nav-height)` — içerik navbar altında kalmaz
- `.site-content`: `min-height: 400px`; anasayfa slider için `.remove-site-content-margin` (`margin-top: -30px`)
- `body.homefirstpage`: anasayfa body class'ı

### Genel sayfa layout'u (`page.html`)

```liquid
<div class="container">
  <h3 class="fw-bold spanborder"><span>{{ page.title }}</span></h3>  {# show_title != false #}
  <div class="page-content">{{ content }}</div>
</div>
```

`.spanborder`: alt çizgili bölüm başlığı stili — iç `span` altında kısa vurgu çizgisi.

---

## Bileşen Kataloğu

### 1. Site Navbar (`#MagicMenu`)

| Özellik | Değer |
|---------|-------|
| Konum | `position: fixed; top: 0; z-index: 1030` |
| Arka plan | Beyaz (`bg-white`), alt border `#dee2e6` |
| Scroll | `site-nav--scrolled` → `box-shadow: 0 2px 12px rgba(0,0,0,0.08)` |
| Logo | `.site-nav__logo` — `max-height: 2.5rem` |
| Vurgulu link | `.highlight .nav-link` — yeşil border + hover fill |

**Dosyalar:** `_layouts/default.html`, `assets/css/theme.css`, `assets/css/app.css`, `assets/js/nav.js`

### 2. Site Footer (`.site-footer`)

3 sütunlu koyu footer:

| Sütun | Class | İçerik |
|-------|-------|--------|
| Ürünler | `.site-footer__col` | Eğitim/Hikaye/Katalog linkleri |
| Önemli Bilgiler | `.site-footer__col` | `footer_show: true` sayfalar |
| İletişim | `.site-footer__col` | `contact-info--footer` + sosyal ikonlar |

Stil özellikleri:
- Arka plan: `--color-footer-bg` (`#25272a`)
- Başlıklar: Punta, uppercase, `--color-primary`
- Linkler: `rgba(255,255,255,0.75)` → hover `--color-primary`
- Alt bölüm: `.site-footer__bottom` — logo (`logo-bw.png`) + copyright

**Dosya:** `_includes/footer-menu.html`, `theme.css` → `.site-footer__*`

### 3. Sınıf Filtresi (`.grade-nav`)

9 sütunlu grid (mobilde 2 sütun); okul öncesi + 1–8. sınıf.

**Sınıf ikon renkleri:**

| `data-grade` | Renk |
|--------------|------|
| `0` (Okul öncesi) | `--color-primary` |
| `1`, `5` | `#e67e22` |
| `2`, `6` | `#e84393` |
| `3`, `7` | `#27ae60` |
| `4`, `8` | `#8e44ad` |

**Durumlar:**
- `.active` — alt çizgi (`box-shadow: inset 0 -2px 0`)
- `.open` — alt menü açık; caret 180° döner
- `.has-genre` — seçili tür etiketi `::after` ile gösterilir

Alt menü (`.grade-submenu`): absolute dropdown; masaüstünde hover ile de açılır.

**Dosyalar:** `_includes/book-grade-nav.html`, `theme.css`, `book-filter.js`

### 4. Kitap Kartı (`.book-card`)

BEM yapısı:

```
.book-card
├── .book-card__link
│   ├── .book-card__media
│   │   └── .book-card__cover (object-fit: contain)
│   └── .book-card__info
│       ├── .book-card__title (line-clamp: 2)
│       ├── .book-card__author (isteğe bağlı)
│       └── .book-card__theme (outline pill, ilk anatema)
```

- Sabit toplam yükseklik — grid hizası bozulmaz
- Tema pill: beyaz zemin, ince border, yeşil metin (`--color-primary`); kart altına `margin-top: auto`
- Hover: hafif gölge + kapak `scale(1.02)`
- Grid: `.listbooks-home.row` — mobil 2, masaüstü 4 sütun CSS Grid

**Dosyalar:** `_includes/book-card.html`, `theme.css`

### 5. Tür Grupları (`.book-genre-group`)

- Başlık: `.book-genre-heading` — Punta, alt border
- Performans: `content-visibility: auto; contain-intrinsic-size: auto 500px`

### 6. Kitap Detay (`.book-page`)

| Bölüm | Class | Not |
|-------|-------|-----|
| Kapak | `.book img` | `drop-shadow` |
| Başlık | `.article-headline.display-4` | `margin-bottom: var(--space-6)`; mobilde ortalı |
| Hero meta | `.book-detail__hero-meta` | Yalnızca `genre: story`; boşsa render edilmez |
| Müfredat paneli | `.book-curriculum` | İki bölüm: TYMM + Öykümatik; alt satırlarda label + yatay scroll şeridi |
| TYMM bölüm başlığı | `.book-curriculum__heading` | «Türkiye Yüzyılı Maarif Modeli»; altında Ünitesi / Anateması / Becerileri |
| Öykümatik bölüm başlığı | `.book-curriculum__heading` | «Türkiye'de İlk ve Tek Damla Hikaye Kazanım Sistemi»; altında Öykümatik Kazanım Kodu |
| TYMM ünite | `.book-curriculum__chip--unite` | Dolu yeşil chip; tek satır, `overflow-x: auto` |
| TYMM anatema | `.book-curriculum__chip--anatema` | Outline yeşil chip; tek satır scroll |
| TYMM beceriler | `.book-curriculum__chip--beceri` | Outline chip; düz liste, tek satır scroll |
| Kazanım kodları | `.book-curriculum__chip--kazanim` | Monospace kod chip; `title` ile kazanım metni |
| Scroll ipucu | `.book-curriculum__scroll::after` | Sağ kenar fade + chevron; mobilde label üstte, tam genişlik scroll |
| Etiketler | `.book-detail__tags .tag` | Panel altında turuncu pill |
| Aksiyonlar | `.book-detail__actions .js-book-action` | Outline `btn-sm`, `fa-sm` ikon, `min-height: 2.25rem` |
| Metadata | `.book-meta__item` | Flex: ikon + metin |
| Açıklama | `.prose--display` | Markdown gövdesi |

Hero sırası: başlık → müfredat paneli (`.book-curriculum`) → etiketler → aksiyonlar. Panel iki bölümden oluşur: **Türkiye Yüzyılı Maarif Modeli** (Ünitesi, Anateması, Becerileri) ve **Türkiye'de İlk ve Tek Damla Hikaye Kazanım Sistemi** (Öykümatik Kazanım Kodu). Mobilde satırlar dikey; chip şeritleri sağ fade ve chevron ile kaydırılabilir olduğunu gösterir.

**Dosyalar:** `_layouts/book.html`, `_includes/book-hero-meta.html`

### 7. Hero Slider (`.slider`)

- Tiny Slider kütüphanesi
- Aspect ratio: desktop `1250/504`, mobil `1181/950`
- İlk slide: `fetchpriority="high"`, preload (webp öncelikli)
- Diğer slide'lar: lazy (`tns-lazy-img`, `loading="lazy"`)
- Container: `.remove-site-content-margin` ile navbar boşluğu telafi

**Dosyalar:** `_includes/slider.html`, `theme.css` → `.slider`, `tiny-slider.css`

### 8. Instagram Carousel (`.ig-carousel`)

Tek dosyada inline `<style>` + `<script>` — istisna bileşen.

- Site token'larıyla uyumlu: `--font-display`, `--color-primary`, `--radius`, `--shadow-sm`
- Yatay scroll-snap carousel; skeleton yükleme durumu
- Kart: `aspect-ratio: 1`, hover caption gradient overlay
- Responsive item genişliği: 50% → 33% → 25%

**Dosya:** `_includes/instagram-carousel.html`

### 9. Spotlight Arama

macOS Spotlight ilhamlı tam ekran modal:

| Eleman | Class | Stil |
|--------|-------|------|
| Overlay | `.spotlight-backdrop` | `backdrop-filter: blur(8px)`, koyu yarı saydam |
| Kutu | `.spotlight-container` | `border-radius: 16px`, cam efekti |
| Tetikleyici (masaüstü) | `.search-trigger-wrapper` | `min-width: 200px`, gri arka plan |
| Tetikleyici (mobil) | `.search-trigger-mobile` | Logo–hamburger arası tam genişlik |
| Sonuç | `.spotlight-item` | Kapak thumbnail + başlık + meta |
| Hover | — | `rgba(3, 168, 124, 0.1)` arka plan |

Kısayol göstergesi: `Ctrl+K` badge. `prefers-color-scheme: dark` desteği var.

**URL senkronu (`?q=`):** Site genelinde geçerli. Sayfa `?q=terim` ile yüklenince modal otomatik açılır. Modal'da yazarken `history.replaceState` ile bulunulan sayfanın URL'sine `?q=` eklenir (paylaşılabilir arama linki). ESC / kapatınca `?q=` silinir; sayfa hash'i (`/urunler#2-sinif/egitim`) korunur. Boş Ctrl+K açılışında URL değişmez. SearchAction schema kanonik giriş: `/?q={search_term_string}`.

Lunr indeks alanları: `title` (yüksek boost), `ean` (barkod), `authors`, `categories`, `grades`, `genre`, `anatemalar`, `tags`, `body`. İndeks kapakları `assets/images/ean/{ean}.webp|jpg` kullanır. 4+ haneli sayısal sorguda `ean` doğrudan eşleştirilir.

**Dosyalar:** `_includes/search-lunr.html`, `_pages/search-index.json`, `assets/css/spotlight.css`, `assets/js/lunr.js`

### 10. Kitap Popup'ları (`#popup-overlay`)

Spotlight ile aynı görsel dil:

| Varyant | Class | Boyut |
|---------|-------|-------|
| Tedarik bilgisi | `.popup-container` | `520px` max |
| Medya (iframe/YouTube) | `.popup-container--media` | `min(960px, 92vw)` |

- `z-index: 10000` (spotlight: 9999)
- Masaüstünde iframe/youtube popup; mobilde yeni sekme
- `info` popup: `prefers-color-scheme: dark` metin renkleri ayarlı

**Dosya:** `_includes/popup.html` (inline style + script)

### 11. Satın Al / Bilgi (`damlaurl`)

Eski `.buyout` satıcı barı ve `buyout.css` kaldırıldı. Satın alma akışı kitap front matter’ındaki `damlaurl` alanı ve `book.html` aksiyon butonlarıyla yönetilir:

| `damlaurl` | Buton | İkon | Popup |
|------------|-------|------|-------|
| Dolu | **Satın Al** | `fa-shopping-cart` (`text-success`) | `data-popup-type="iframe"` → Damla Yayınevi ürün sayfası |
| Boş | **Bilgi** | `fa-info-circle` (`text-info`) | `data-popup-type="info"` → tedarik bilgisi |

**Dosyalar:** `_layouts/book.html`, `_includes/popup.html`

### 12. İletişim Bilgisi (`.contact-info`)

| Mod | Class | Bağlam |
|-----|-------|--------|
| Footer | `.contact-info--footer` | Beyaz yarı saydam metin |
| Sayfa | `.contact-info--page` | Normal sayfa metni |

**Dosya:** `_includes/contact-info.html`

### 13. Ürün İnceleme Linkleri (`.review-links`)

Tek sayfa bileşeni; inline CSS + JS (`_pages/linkler.html` — include yok).

| Eleman | Class | Not |
|--------|-------|-----|
| Kapsayıcı | `.review-links` | `max-width: 44rem`, ortalanmış liste |
| Kart | `.review-links__card` | Yatay düzen; hover border/gölge |
| Kapak | `.review-links__media` + `eanimage.html` | Solda ~5.5rem; `review-links__cover` |
| Rozet | `.review-links__badge` | Sınıf etiketi (Okul Öncesi / N.Sınıf) |
| Başlık | `.review-links__title` | Ürün detay sayfasına link |
| Aksiyonlar | `.review-links__actions` | 2×2 grid: Kitabı incele, Kitaba git, Whatsappda paylaş, Linki kopyala |
| Arama | `.review-links__search-input` | Başlık + sınıf rozeti client-side filtre |

Token kullanımı: `--font-sans`, `--font-display`, `--color-primary`, `--radius`, `--shadow-sm`, `--color-border`. `show_title: false` ile sayfa başlığı özel header bloğunda.

**Dosya:** `_pages/linkler.html`

---

## İkonografi

- **Kütüphane:** Font Awesome 5.15.4 (yerel, CDN yok)
- **Stiller:** `fas` (solid), `fab` (brand)
- **Grade nav:** Her sınıf için 2 ikon (Font Awesome education set)
- **Book meta:** Renkli ikonlar (`text-primary`, `text-danger`, `text-dark`)
- **Sosyal medya:** `menu-socialmedia.html` — `fab fa-*`
- **X (Twitter):** `.site-social__icon--x` özel SVG/block

---

## Görsel İşleme

### Kitap kapakları

- Yol: `assets/images/ean/{ean}.jpg`
- Render: `<picture>` + koşullu WebP (`webp_manifest.yml`)
- Kart: `object-fit: contain`, `loading="lazy"`, `fetchpriority="low"`
- Gölge: `.cover-shadow` veya `.book img { filter: drop-shadow(...) }`

### Slider görselleri

- Yol: `assets/images/slides/`
- Mobil/desktop ayrı dosya (`mobile-img` / `img`)
- Hedef: mobil `*m.jpg` ≤ 120 KB (Photoshop ile optimize)

### WebP politikası

Şablonlar yalnızca manifest'te kayıtlı webp için `<source type="image/webp">` ekler — 404 oluşmaz.

---

## İsimlendirme Kuralları

| Desen | Örnek | Kullanım |
|-------|-------|----------|
| BEM blok | `.book-card` | Yeni bileşenler |
| BEM element | `.book-card__title` | Alt parçalar |
| BEM modifier | `.contact-info--footer` | Varyantlar |
| Site prefix | `.site-nav__*`, `.site-footer__*` | Global shell bileşenleri |
| Bootstrap utility | `.d-flex`, `.col-md-4` | Layout — HTML'de doğrudan |
| Legacy | `.kitap-kutu`, `.kitap-kutu-home` | Geçiş dönemi; yeni kodda kullanılmaz |
| JS hook | `.js-book-action` | Davranış bağlantısı, stil değil |

**Tercih:** Yeni bileşenlerde BEM + site prefix; Bootstrap class'ları yalnızca grid/spacing için.

---

## Sayfa Özel Stiller (İstisnalar)

Bazı sayfalar kendi `<style>` bloğunu taşır. Bu **istisnadır**; kalıcı bileşenler `theme.css`'e taşınmalıdır.

| Sayfa / partial | Pattern | Not |
|-----------------|---------|-----|
| `_pages/linkler.html` | `.review-links__*` | Ürün inceleme linkleri; token + inline arama/kopyala; bkz. [§13 Ürün İnceleme Linkleri](#13-ürün-inceleme-linkleri-review-links) |
| `_includes/instagram-carousel.html` | `.ig-carousel__*` | Tek modül; inline CSS kabul edilir |
| `_includes/popup.html` | `.popup-*` | Modal; kitap detayda include |
| `_includes/ai-seo-crawler*.html` | `.ai-seo-crawler` | Görsel olarak gizli; inline style |

Yeni sayfa özel stil eklerken mevcut token'ları referans alın; hard-coded renk yerine `var(--color-*)` kullanın.

---

## Koyu Tema Desteği

Site genelinde dark mode yok; `body` her zaman açık tema. Aşağıdaki bileşenler `prefers-color-scheme: dark` ile OS koyu temasına uyum sağlar:

- `.spotlight-container` ve alt elemanları
- `.popup-container` ve `.popup-body` metin renkleri

Navbar, footer ve ana içerik koyu tema desteklemez.

---

## Erişilebilirlik Desenleri

| Özellik | Uygulama |
|---------|----------|
| Skip / landmark | `<main role="main">`, `<nav aria-label="...">` |
| Modal | `role="dialog"`, `aria-modal="true"`, `aria-label` |
| Klavye | `Ctrl+K` arama, `ESC` modal kapat, `Enter` ilk sonuç |
| Görsel | `alt` metinleri, `width`/`height` ipuçları (CLS önleme) |
| Gizli SEO | `aria-hidden="true"`, `data-nosnippet` (ai-seo-crawler) |
| Touch | Grade nav caret: `touch-action: manipulation`, min 2.75rem hedef |

---

## Yeni Stil Ekleme Rehberi

### Kalıcı bileşen

1. `theme.css` → Components bölümüne BEM class'ları ekle
2. Gerekirse `:root`'a yeni token ekle
3. HTML partial → `_includes/` veya layout
4. Bootstrap grid ile layout; özel görünüm theme'den

### Bootstrap override

1. `app.css`'e ekle
2. Mümkünse CSS değişkeni (`--bs-*`) kullan
3. `!important` yalnızca Bootstrap specificity gerektirdiğinde

### Tek sayfa / tek kullanım

1. Sayfa front matter altında `<style>` bloğu kabul edilir
2. Token referansı zorunlu; bileşen büyürse `theme.css`'e taşı

### Yapılmaması gerekenler

- `bootstrap.min.css` düzenlemek
- Inline `style=""` attribute (istisna: dinamik JS)
- CDN font/icon (tüm fontlar yerel)
- jQuery tabanlı UI (`theme.js` legacy)
- Global CSS'e AI crawler gizleme kuralları (include içi inline style)

---

## Legacy ve Geçiş

| Öğe | Durum | Yönlendirme |
|-----|-------|-------------|
| `.kitap-kutu`, `.kitap-kutu-home` | Geçiş | `.book-card` kullan |
| `book-grade-filter.html` | Kullanılmıyor | `.grade-nav` |
| `assets/js/theme.js` | Legacy jQuery | Kullanma |
| `.text-humayun` | Özel sarı (`#ffc107`) | Nadir kullanım |
| Eski watermark arka plan | Kaldırıldı | `body { background-image: none }` |

---

## İlgili Dosya Referansı

| Konu | Dosya |
|------|-------|
| Ana stil | `assets/css/theme.css` |
| Bootstrap override | `assets/css/app.css` |
| Arama UI | `assets/css/spotlight.css` |
| Kök şablon | `_layouts/default.html` |
| Navbar JS | `assets/js/nav.js` |
| Font subset | `scripts/subset_font.sh` |
| Görsel optimizasyon | [README.md — Performans](README.md#performans-ve-görsel-optimizasyonu) |
