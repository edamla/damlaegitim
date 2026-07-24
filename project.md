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
| Geometric Sans | `assets/fonts/geometric-sans/geometric.otf` | Navbar menü linkleri | `.site-nav .navbar-nav.me-auto .nav-link` |
| Punta | `assets/fonts/punta/Punta-Light.otf` | Sınıf filtresi, tür başlıkları | `.grade-nav`, `.book-genre-heading` |
| Raykjavik | `assets/fonts/raykjavik/reykjavik-rounded-regular.ttf` | Genel site metni | `body`, `--font-sans` |

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
│   │   ├── theme.css
│   │   ├── app.css
│   │   ├── tiny-slider.css
│   │   └── buyout.css
│   ├── fonts/
│   │   ├── geometric-sans/
│   │   ├── punta/
│   │   └── raykjavik/
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
├── CNAME                 # damlaokul.com
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
| `slider.html` | Anasayfa Tiny Slider |
| `instagram-carousel.html` | Anasayfa Instagram carousel (`okul.damla`, Behold JSON feed) |
| `book-grade-nav.html` | Sınıf sekmesi + tür alt menüsü |
| `book-home-groups.html` | Anasayfa kitap listesi (Eğitim / Hikaye) |
| `book-card.html` | Tek kitap kartı partial (sabit resim + isim kutusu) |
| `book-grade-filter.html` | Eski sınıf checkbox dropdown’u (artık kullanılmıyor) |
| `search-lunr.html` | Spotlight arama (Lunr.js indeks + modal UI + navbar tetikleyici) |
| `popup.html` | Kitap detay popup’ları (Bilgi, ön okuma iframe, YouTube; koyu tema desteği) |
| `tracking-header.html` / `tracking-footer.html` | Google Analytics |

---

## JavaScript

| Dosya | Bağımlılık | Görev |
|-------|------------|-------|
| `bootstrap.bundle.min.js` | — | Collapse, dropdown, modal |
| `nav.js` | — | Sticky navbar yüksekliği (`--nav-height`), scroll gölgesi |
| `book-filter.js` | — | Sınıf/tür filtreleme + hash URL senkronizasyonu |
| `lunr.js` | — | Spotlight kitap araması (client-side indeks) |
| `tiny-slider.js` | — | Anasayfa slider |
| `lazyload.js` | — | Görsel lazy loading (`lazyimages: enabled`) |

jQuery kullanılmaz. Eski `theme.js` dosyası repoda kalabilir ancak `default.html`’de yüklenmez.

`instagram-carousel.html` kendi inline `<script>` bloğunu taşır; harici JS dosyası veya tiny-slider bağımlılığı yoktur.

`search-lunr.html` navbar Spotlight aramasını sağlar; jQuery kullanılmaz. `mode` parametresiyle navbar tetikleyicisi (`desktop` / `mobile`) veya script bloğu (`mode` olmadan) ayrı include edilir.

- **Masaüstü (`mode='desktop'`)** — Navbar collapse içinde tam arama kutusu (`Ctrl+K` kısayolu)
- **Mobil (`mode='mobile'`)** — Logo ile hamburger arasında minimal arama çubuğu (`Kitap ara...`); collapse dışında, her zaman görünür

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
| `_includes/search-lunr.html` | Lunr indeks (build-time), modal UI, inline CSS/JS, navbar tetikleyici |
| `assets/js/lunr.js` | Lunr.js 2.1.5 kütüphanesi |

### İndeks kapsamı

`site.books` koleksiyonu; alanlar: `title`, `authors`, `categories`, `grades`, `genre`, `subjects`, `tags`, `body`.

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
```

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
3. İsteğe bağlı `description:` — yoksa build sırasında otomatik üretilir
4. Kapak görselini `assets/images/ean/` altına koy
5. `bundle exec jekyll serve` ile kontrol et
6. `git push`

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
| Font Awesome 5 CDN | İkonlar |
| `cdn.e-damla.com.tr` | Önizleme sayfaları, örnek sayfalar |
| `feeds.behold.so` | Instagram carousel JSON feed |
| Google Analytics | `G-KFMVQ3WNN3` (production) |

---

## Bilinen Legacy Dosyalar

Aşağıdaki dosyalar geçmişten kalma olabilir; aktif kullanılmıyorsa temizlenebilir:

- `assets/js/theme.js` (jQuery tabanlı; `loadSearch()` kullanılmıyor)
- `_pages/_draft/books.html`
