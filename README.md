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
- **SEO & AI keşfi** — `robots.txt`, `llms.txt`, otomatik kitap meta description, Product JSON-LD

## Teknoloji

| Katman | Teknoloji |
|--------|-----------|
| Site motoru | Jekyll 4.x (Ruby) |
| CSS framework | Bootstrap 5.3 |
| Özel stiller | `theme.css` + `app.css` |
| JavaScript | Vanilla JS (filtre, navbar, arama) + Bootstrap bundle + Lunr.js |
| Yayın | GitHub Pages |
| İçerik | Markdown + YAML front matter |

Node.js veya npm **gerekmez**.

## Hızlı Başlangıç

### Gereksinimler

- Ruby 3.x
- Bundler (`gem install bundler`)

### Kurulum

```bash
git clone https://github.com/<org>/damlaegitim.git
cd damlaegitim
sh install.sh
```

### Yerel geliştirme

```bash
sh start.sh
```

Tarayıcıda [http://localhost:4000](http://localhost:4000) adresini açın.

Windows’ta Git Bash veya WSL ile `sh start.sh` çalıştırılabilir. Alternatif:

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

## Proje Yapısı (özet)

```
_books/          Ürünler (kitap / eğitim seti)
_catalogs/       Kataloglar
_pages/          Statik sayfalar (hakkımızda, iletişim, ürünler listesi)
_layouts/        HTML şablonları
_includes/       Ortak bileşenler (menü, kart, filtre, arama)
assets/css/      Stiller (bootstrap, theme, app)
assets/js/       Script’ler
assets/images/   Görseller ve kapaklar
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

Kitap `description:` alanı opsiyoneldir; boşsa başlık, sınıf ve türden otomatik üretilir. Doğrulama: `bundle exec jekyll build` sonrası `_site/robots.txt`, `_site/llms.txt` ve örnek kitap HTML'i kontrol edin.

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
image: assets/images/ean/9786053832874.jpg
ean: 9786053832874
---
Ürün açıklaması buraya...
```

`subjects` TEMALAR için, `concepts` çoklu zekâ / kavram etiketleri içindir. `concepts` alanına `_config.yml` anahtarı (`sozel-dilsel`) veya doğrudan metin (`Dil Bilim Gelişimi`) yazılabilir.

3. Kapak görselini `assets/images/ean/` klasörüne ekleyin
4. `bundle exec jekyll serve` ile önizleyin
5. Commit ve push

## Stil Düzenleme

| Ne değişiyor? | Hangi dosya? |
|---------------|--------------|
| Renk, font, spacing token’ları | `assets/css/theme.css` (`:root`) |
| Yeni bileşen (kart, nav, vb.) | `assets/css/theme.css` |
| Bootstrap renk / buton override | `assets/css/app.css` |

Bootstrap’ın kendi dosyası (`bootstrap.min.css`) düzenlenmez.

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

- İndeks: `site.books` (başlık, yazar, kategori, sınıf, tür, etiket, içerik)
- Dosya: [`_includes/search-lunr.html`](_includes/search-lunr.html)
- Kütüphane: [`assets/js/lunr.js`](assets/js/lunr.js)

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
