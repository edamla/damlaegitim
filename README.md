# Damla Okul

[damlaokul.com](https://damlaokul.com) — Damla Yayınevi’nin okul yayınları ve eğitim materyallerini tanıtan statik web sitesi.

Yeni Maarif Modeline uygun eğitim setleri, hikaye kitapları ve kataloglar tek bir katalogda sunulur.

## Özellikler

- **Ürün kataloğu** — Sınıf ve tür (Eğitim / Hikaye) bazlı filtreleme, paylaşılabilir hash URL’leri
- **Kitap detay sayfaları** — Kapak, metadata, `#subjects` / `@concepts` etiketleri, önizleme linki, popup ile tedarik bilgisi
- **Kataloglar** — Html / PDF katalog görüntüleme
- **Anasayfa slider** — Kampanya ve duyuru görselleri
- **Instagram carousel** — `@okul.damla` hesabının güncel gönderileri (Behold JSON feed)
- **Spotlight arama** — Lunr.js ile kitap araması (`Ctrl+K`; mobilde header’da minimal arama çubuğu)
- **Sticky navbar** — Scroll’da kaybolmayan sabit üst menü (mobil + masaüstü)
- **3 sütunlu footer** — Ürünler, önemli bilgiler, iletişim ve sosyal medya
- **Mobil uyumlu** — Bootstrap 5 responsive grid; hamburger menü alt satırda açılır
- **Statik & hızlı** — Jekyll ile önceden derlenmiş HTML, GitHub Pages üzerinde yayın
- **Performans odaklı** — Lazy arama, yerel fontlar, `<picture>` + WebP, slider lazyload, koşullu script yükleme
- **SEO & AI keşfi** — `robots.txt`, `llms.txt`, otomatik kitap meta description, Product JSON-LD, sayfa bağlamına göre dinamik LLM/SEO crawler içeriği (`ai-seo-crawler`)

## Teknoloji

| Katman | Teknoloji |
|--------|-----------|
| Site motoru | Jekyll 4.x (Ruby) |
| CSS framework | Bootstrap 5.3 |
| Özel stiller | `theme.css` + `app.css` + `fontawesome-all.min.css` |
| JavaScript | Vanilla JS (filtre, navbar, arama) + Bootstrap bundle + Lunr.js (lazy) |
| Fontlar | Yerel: Geometric Sans, Punta, Raykjavik (WOFF2), Font Awesome 5.15.4 |
| Yayın | GitHub Pages |
| İçerik | Markdown + YAML front matter |

Node.js veya npm **gerekmez**.

## Hızlı Başlangıç

### Sistem gereksinimleri

Yerel geliştirme için aşağıdaki ortam önerilir. Canlı site GitHub Pages üzerinde derlenir; prod için bu araçların sunucuda kurulu olması gerekmez.

#### Tüm platformlar

| Gereksinim | Zorunlu | Açıklama |
|------------|---------|----------|
| **Git** | Evet | Repoyu klonlamak ve sürüm kontrolü |
| **Ruby 3.x** | Evet | Jekyll ve gem bağımlılıkları |
| **Bundler** | Evet | `Gemfile` üzerinden gem kurulumu (`install.sh` eksikse kurar) |
| **Python 3** + **pip** | Evet | Font WOFF2 subset (`fonttools`, `brotli` — `install.sh` kurar) |
| **Bash** | Evet | `install.sh` / `start.sh` ve `scripts/*.sh` için |

Node.js veya npm **gerekmez**.

#### Windows (önerilen: Windows 10 ve üzeri)

| Gereksinim | Zorunlu | Açıklama |
|------------|---------|----------|
| **Windows 10+** | Evet | Geliştirme ortamı hedefi |
| **Git for Windows** | Evet | [git-scm.com](https://git-scm.com/) — **Git Bash** ile `sh install.sh` / `sh start.sh` |
| **RubyInstaller** | Evet | [rubyinstaller.org](https://rubyinstaller.org/) — Ruby 3.x + **Devkit** (MSYS2) seçin; kurulumdan sonra Git Bash'i yeniden açın |
| **winget** | Önerilen | Windows App Installer ile gelir; `install.sh` ImageMagick ve libwebp kurulumunda kullanır |
| **ImageMagick** / **libwebp** | Opsiyonel | Yoksa `install.sh` winget ile kurmayı dener; başarısızsa site jpg/png ile çalışır |

Windows'ta `winget` yoksa (eski Windows veya kurumsal kısıt): ImageMagick'i [imagemagick.org](https://imagemagick.org) üzerinden manuel kurun veya yalnızca jpg/png ile devam edin.

```powershell
# winget kurulu mu kontrol
winget --version

# Manuel kurulum (install.sh başarısızsa)
winget install ImageMagick.ImageMagick
winget install Google.Libwebp
```

#### macOS

| Gereksinim | Zorunlu | Açıklama |
|------------|---------|----------|
| **Homebrew** | Önerilen | `install_image_tools.sh` → `brew install imagemagick` / `webp` |
| **Ruby 3.x** | Evet | `brew install ruby` veya RubyInstaller benzeri |

#### Linux

| Gereksinim | Zorunlu | Açıklama |
|------------|---------|----------|
| **imagemagick**, **webp** paketleri | Önerilen | `install_image_tools.sh` → `sudo apt install imagemagick webp` (Debian/Ubuntu) |

#### Özet: ne ne için?

| Araç | Kullanım |
|------|----------|
| Ruby + Bundler | Jekyll build / serve |
| Python + fonttools | `subset_font.sh` — OTF/TTF → WOFF2 |
| winget (Windows) | `install_image_tools.sh` — ImageMagick + libwebp otomatik kurulum |
| ImageMagick / cwebp | `generate_webp.sh` — jpg/png → WebP (`start.sh` hook) |
| Git Bash | Windows'ta shell script'leri çalıştırma |

### Kurulum (ilk kez)

```bash
git clone https://github.com/<org>/damlaegitim.git
cd damlaegitim
sh install.sh
```

`install.sh` — sıfırdan kurulum (hook yok):

1. Ruby / Bundler kontrolü
2. `bundle install`
3. Python `fonttools` + `brotli`
4. WOFF2 font dönüşümü (`subset_font.sh` — mevcut woff2 güncel ise atlanır)
5. Font boyut kontrolü (`check_fonts.sh`)
6. Görsel araçları (`install_image_tools.sh` — Windows: winget ImageMagick + libwebp)
7. `_data/webp_manifest.yml` yoksa oluşturma
8. `jekyll build` ile kurulum doğrulama

### Yerel geliştirme (kurulum sonrası)

```bash
sh start.sh
```

`start.sh` — geliştirme hook'ları + sunucu:

1. Büyük görselleri raporlar (`check_images.sh`)
2. Eksik WebP üretir (`generate_webp.sh`)
3. `bundle exec jekyll serve`

Tarayıcıda [http://localhost:4000](http://localhost:4000) adresini açın.

Windows’ta Git Bash ile `sh install.sh` ve `sh start.sh` çalıştırılabilir. Alternatif:

```bash
bundle exec jekyll serve
```

### Canlıya alma

```bash
git add .
git commit -m "Değişiklik açıklaması"
git push
```

GitHub Pages otomatik olarak siteyi günceller.

## Kurulum ve geliştirme script'leri

| Script | Ne zaman | Görev |
|--------|----------|-------|
| [`install.sh`](install.sh) | İlk kez (`git clone` sonrası) | Ruby gems, fonttools, WOFF2 subset, görsel araçları (winget), `jekyll build` doğrulama — **hook yok** |
| [`start.sh`](start.sh) | Her geliştirme oturumu | `check_images` + `generate_webp` hook'ları + `jekyll serve` |
| [`scripts/install_image_tools.sh`](scripts/install_image_tools.sh) | `install.sh` içinden | Windows: winget ImageMagick + libwebp; macOS: brew; Linux: apt |
| [`scripts/generate_webp.sh`](scripts/generate_webp.sh) | `start.sh` içinden | `ean/` ve `slides/` için eksik `.webp` üretir; `_data/webp_manifest.yml` günceller |
| [`scripts/refresh_image_paths.sh`](scripts/refresh_image_paths.sh) | Dahili | Windows'ta winget kurulum yollarını PATH'e ekler |
| [`scripts/check_images.sh`](scripts/check_images.sh) | `start.sh` içinden | Büyük görselleri raporlar (dosyaya dokunmaz) |
| [`scripts/subset_font.sh`](scripts/subset_font.sh) | `install.sh` içinden | OTF/TTF → WOFF2 subset |
| [`scripts/check_fonts.sh`](scripts/check_fonts.sh) | `install.sh` içinden | Font boyut uyarı raporu |

Windows Git Bash'te sıfırdan kurulum: `sh install.sh` → geliştirme: `sh start.sh`.

## Proje Yapısı (özet)

```
_books/          Ürünler (kitap / eğitim seti)
_catalogs/       Kataloglar
_data/           Jekyll data (webp_manifest.yml — otomatik)
_pages/          Statik sayfalar + search-index.json
_layouts/        HTML şablonları
_includes/       Ortak bileşenler (menü, kart, filtre, arama, ai-seo-crawler)
assets/css/      Stiller (bootstrap, fontawesome, theme, app, spotlight)
assets/fonts/    Yerel fontlar (geometric-sans, punta, raykjavik, fontawesome)
assets/js/       Script'ler
assets/images/   Görseller, slider ve kapaklar (jpg/png; .webp otomatik üretilebilir)
scripts/         Kurulum ve geliştirme araç script'leri (yukarıdaki tablo)
install.sh       İlk kurulum
start.sh         Geliştirme sunucusu + hook'lar
docs/            CLOUDFLARE.md (proxy/cache rehberi)
index.html       Anasayfa
```

Detaylı mimari için [project.md](project.md) dosyasına bakın.

## SEO ve AI Crawler

| Dosya | Açıklama |
|-------|----------|
| `robots.txt` | Arama motorları ve AI botlara tam erişim |
| `/llms.txt` | AI crawler'lar için site haritası |
| `_includes/book-seo-tags.html` | Kitap sayfaları meta / Open Graph |
| `_includes/structured-data-*.html` | schema.org JSON-LD |
| `_includes/ai-seo-crawler.html` | Tüm sayfalara `default.html` üzerinden eklenen router; sayfa türüne göre partial seçer |
| `_includes/ai-seo-crawler-*.html` | Kitap, anasayfa, katalog, katalog detay ve genel sayfa için hibrit içerik (LLM talimat + ikna metni) |
| `_includes/ai-seo-crawler-base.html` | Ortak marka argümanları (1974, profesyonel kadro, Maarif Modeli) |

Dinamik AI/SEO crawler içeriği yalnızca arama motoru ve LLM crawler'ları için üretilir; include içi `<style>` ile visually-hidden + `aria-hidden` + `data-nosnippet` kullanılır (global CSS'e bağımlı değil). `book-minimal-content.html` **görünür** ince kitap metni sunar; `ai-seo-crawler` **gizli** LLM rehber talimatları içerir. `llms.txt` site haritası; `ai-seo-crawler` sayfa bazlı bağlam — ikisi birbirini tamamlar.

Kitap `description:` alanı opsiyoneldir; boşsa başlık, sınıf ve türden otomatik üretilir. Doğrulama: `bundle exec jekyll build` sonrası `_site/robots.txt`, `_site/llms.txt`, örnek kitap HTML'i ve `.ai-seo-crawler` bloğu + `data-ai-role` attribute'ları kontrol edin.

## Yeni Ürün Ekleme

1. `_books/` altında yeni bir `.md` dosyası oluşturun
2. Front matter alanlarını doldurun:

```yaml
---
layout: book
title: "Ürün Adı"
grades: [1, 2]
genre: education
subjects: ["Değerler Eğitimi", "Macera"]     # yeşil # etiketler (detay sayfası üstü)
concepts: ["sozel-dilsel", "icsel"]           # turuncu @ etiketler (anahtar veya serbest metin)
ean: 9786053832874
---
Ürün açıklaması buraya...
```

`subjects` TEMALAR için, `concepts` çoklu zekâ / kavram etiketleri içindir. `concepts` alanına `_config.yml` anahtarı (`sozel-dilsel`) veya doğrudan metin (`Dil Bilim Gelişimi`) yazılabilir.

3. Kapak görselini `assets/images/ean/{ean}.jpg` olarak ekleyin (jpg/png optimize edin; `.webp` `sh start.sh` ile otomatik üretilir)
4. `sh scripts/check_images.sh` ile boyut kontrolü yapın (veya `sh start.sh` — hook olarak çalışır)
5. `sh start.sh` ile önizleyin
6. Commit ve push

## Stil Düzenleme

| Ne değişiyor? | Hangi dosya? |
|---------------|--------------|
| Renk, font, spacing token’ları | `assets/css/theme.css` (`:root`) |
| Yeni bileşen (kart, nav, vb.) | `assets/css/theme.css` |
| Bootstrap renk / buton override | `assets/css/app.css` |
| Font Awesome | `assets/css/fontawesome-all.min.css` + `assets/fonts/fontawesome/` |
| Arama modal stilleri | `assets/css/spotlight.css` |

Bootstrap’ın kendi dosyası (`bootstrap.min.css`) düzenlenmez.

## Performans ve Görsel Optimizasyonu

Site hızı için uygulanan önlemler:

| Alan | Uygulama |
|------|----------|
| Hero slider | Mobil-öncelik `<picture>` + koşullu WebP, mobil LCP preload (webp), `slider-init.js` defer |
| Kitap kapakları | `<picture>` + koşullu WebP, `loading="lazy"`, `fetchpriority="low"` |
| Arama | Lunr lazy-load; indeks `/assets/search-index.json` |
| Scriptler | Bootstrap `defer`; `book-filter.js` idle init (`requestIdleCallback`); tiny-slider defer |
| CSS | `content-visibility` kitap grupları; `tiny-slider.css` anasayfa head'de |
| Fontlar | Font Awesome yerel; Raykjavik WOFF2 subset (~26 KB) |
| Instagram | Feed `IntersectionObserver` ile gecikmeli yüklenir |

### Görsel politikası

| İş | Araç |
|----|------|
| Resize / JPEG sıkıştırma | **Photoshop** (manuel) — ImageMagick ile resize yapılmaz |
| jpg/png → webp | `scripts/generate_webp.sh` (`start.sh` hook) |
| Boyut uyarısı | `scripts/check_images.sh` — dosyaya dokunmaz |

Mobil slider `*m.jpg` hedefi: ≤ 120 KB (`sh scripts/check_images.sh slides`). Kod tarafında webp preload ve `<picture>` ile LCP iyileşir; kalıcı küçültme Photoshop ile yapılır.

### Cloudflare mobil benchmark (referans)

Mobil skor ~55; LCP ~11.5 s (büyük mobil jpeg preload + yanlış LCP kaynağı). Kod optimizasyonları: mobil webp preload, mobil-öncelik slider, defer JS, content-visibility. Retest: Cloudflare Speed Test mobil.

### Görsel kontrol scripti

Görseller manuel optimize edilir. Script yalnızca büyük dosyaları raporlar:

```bash
sh scripts/check_images.sh          # Tüm klasörler
sh scripts/check_images.sh slides   # Slider görselleri
sh scripts/check_images.sh ean      # Kitap kapakları
```

### WebP otomatik üretim (hibrit)

`assets/images/ean/` ve `assets/images/slides/` altındaki jpg/png dosyalarından eksik `.webp` varyantları üretilir; manifest [`_data/webp_manifest.yml`](_data/webp_manifest.yml) güncellenir. [`eanimage.html`](_includes/eanimage.html), [`book-card.html`](_includes/book-card.html) ve [`slider.html`](_includes/slider.html) yalnızca manifest'te kayıtlı webp'ler için `<source type="image/webp">` ekler — araç veya dosya yoksa jpg/png ile devam eder, 404 oluşmaz.

| Aşama | Ne yapar |
|-------|----------|
| `install.sh` | `install_image_tools.sh` — Windows'ta winget ile ImageMagick (`ImageMagick.ImageMagick`) ve gerekirse libwebp (`Google.Libwebp`) kurar |
| `start.sh` | `generate_webp.sh` — eksik webp üretir, manifest günceller |
| `refresh_image_paths.sh` | Winget kurulum yollarını Git Bash PATH'ine ekler |

```bash
sh scripts/generate_webp.sh         # Manuel çalıştırma
sh start.sh                         # Geliştirme: check_images + generate_webp + jekyll serve
```

Araçlar: `cwebp` (libwebp) veya ImageMagick (`magick`). Kurulumda otomatik denenir; yoksa site jpg ile çalışır. Üretilen `.webp` dosyalarını commit etmek prod GitHub Pages için önerilir.

### Font WOFF2 üretimi

```bash
pip install fonttools brotli   # bir kez
sh scripts/subset_font.sh      # Tüm fontlar için WOFF2 oluşturur (fontawesome hariç)
```

### Cloudflare

Site şu an Cloudflare DNS-only modunda. Proxy ve cache ayarları için [`docs/CLOUDFLARE.md`](docs/CLOUDFLARE.md).

## Instagram Carousel

Anasayfada `@okul.damla` gönderilerini gösteren carousel modülü [`_includes/instagram-carousel.html`](_includes/instagram-carousel.html) dosyasındadır. Tek dosyada inline HTML, CSS ve JS içerir.

### Kurulum

1. [behold.so](https://behold.so) üzerinde `okul.damla` hesabını bağlayın
2. Çıktı tipi **JSON** olan bir feed oluşturun
3. `_config.yml` içindeki `instagram_carousel.feed_url` alanına feed URL’sini yazın:

```yaml
instagram_carousel:
  username: okul.damla
  profile_url: https://instagram.com/okul.damla
  feed_url: 'https://feeds.behold.so/XXXX'
  limit: 12
```

Başka bir sayfaya eklemek için:

```liquid
{% include instagram-carousel.html %}
```

## Spotlight Arama

Navbar’daki arama kutusu veya `Ctrl+K` / `⌘K` ile kitap araması açılır. Sonuçlar kapak görseli, başlık, yazar ve sınıf/tür bilgisiyle listelenir.

- **Masaüstü** — Navbar’da tam arama kutusu + `Ctrl+K`
- **Mobil** — Logo ile hamburger menü arasında minimal `Kitap ara...` çubuğu (collapse dışında, her zaman görünür)

- İndeks: `site.books` → build-time `/assets/search-index.json`
- Lunr.js yalnızca arama açılınca yüklenir (sayfa yükü azaltılır)
- Dosyalar: [`_includes/search-lunr.html`](_includes/search-lunr.html), [`_pages/search-index.json`](_pages/search-index.json), [`assets/js/lunr.js`](assets/js/lunr.js)

## Navbar

Üst menü (`#MagicMenu`) scroll sırasında sabit kalır; aşağı kaydırınca gizlenmez.

- Yapı: mobilde logo + arama + hamburger üst satır; menü linkleri alt satırda tam genişlik
- Script: [`assets/js/nav.js`](assets/js/nav.js) (`--nav-height` senkronizasyonu, scroll gölgesi)

## Kitap Detay Popup’ları

Ön Okuma, Tanıtım, Bilgi, İncele ve HDS butonları [`_includes/popup.html`](_includes/popup.html) ile açılır. Bilgi popup’u iPhone koyu temada okunabilir metin renklerine sahiptir.

## Footer

Site alt bilgisi [`_includes/footer-menu.html`](_includes/footer-menu.html) ile 3 sütunlu olarak gösterilir:

1. **Ürünler** — Eğitim / Hikaye kitapları (`/urunler`) ve kataloglar sayfası
2. **Önemli Bilgiler** — `footer_show: true` olan `_pages` kayıtları (`footer_order` ile sıralama)
3. **Adres & İletişim** — `_config.yml` içindeki `contact_*` alanları + sosyal medya ikonları

### İletişim bilgileri

Telefon, e-posta ve adres `_config.yml` kök seviyesinde tanımlanır:

```yaml
contact_phone: "+90 212 514 28 28"
contact_phone_href: "tel:+902125142828"
contact_email: "iletisim@damlayayinevi.com.tr"
contact_address: "Alemdar Mh. Prof. Kazım İsmail Gürkan Cad. No:8 Fatih, 34110 İstanbul"
```

Paylaşılan partial: [`_includes/contact-info.html`](_includes/contact-info.html)

```liquid
{% include contact-info.html mode='footer' %}  {# footer #}
{% include contact-info.html mode='page' %}   {# iletişim sayfası #}
```

Yeni bir sayfayı footer’da listelemek için front matter’a `footer_show: true` ve `footer_order` ekleyin.

## Sayfalar

| URL | Açıklama |
|-----|----------|
| `/` | Anasayfa — slider + Instagram carousel + sınıf/tür filtreli ürün listesi |
| `/urunler` | Tüm ürünler, sınıf/tür nav filtresi, hash URL desteği |
| `/urunler/:title` | Ürün detay |
| `/kataloglar` | Katalog listesi |
| `/kataloglar/:title` | Katalog detay |
| `/hakkimizda` | Hakkımızda |
| `/iletisim` | İletişim |

## Filtre URL’leri

Anasayfa ve `/urunler` sayfasında sınıf/tür filtresi URL hash ile paylaşılabilir (Jekyll rebuild gerekmez):

```
/urunler#okul-oncesi          → Okul öncesi (tüm türler)
/urunler#okul-oncesi/egitim   → Okul öncesi, eğitim
/urunler#1-sinif/hikaye       → 1. sınıf, hikaye
/#2-sinif/egitim              → Anasayfa, 2. sınıf eğitim
```

Nav’dan filtre seçildiğinde URL otomatik güncellenir; hash ile açılan sayfada filtre sayfa yüklenirken uygulanır.

## Lisans ve İletişim

© Damla Yayınevi — [damlaokul.com](https://damlaokul.com)

- [Facebook](https://www.facebook.com/damlayayinevi)
- [Instagram (Damla Yayınevi)](https://instagram.com/damlayayinevi)
- [Instagram (Damla Okul)](https://instagram.com/okul.damla)
- [YouTube](https://www.youtube.com/c/damlayayinevi)
- [Twitter](https://twitter.com/damlayayinevi)
