# Damla Okul

[damlaokul.com](https://damlaokul.com) — Damla Yayınevi’nin okul yayınları ve eğitim materyallerini tanıtan statik web sitesi.

Yeni Maarif Modeline uygun eğitim setleri, hikaye kitapları ve kataloglar tek bir katalogda sunulur.

## Özellikler

- **Ürün kataloğu** — Sınıf ve tür (Eğitim / Hikaye) bazlı filtreleme
- **Kitap detay sayfaları** — Kapak, metadata, önizleme linki, tedarik bilgisi
- **Kataloglar** — Html / PDF katalog görüntüleme
- **Anasayfa slider** — Kampanya ve duyuru görselleri
- **Mobil uyumlu** — Bootstrap 5 responsive grid
- **Statik & hızlı** — Jekyll ile önceden derlenmiş HTML, GitHub Pages üzerinde yayın

## Teknoloji

| Katman | Teknoloji |
|--------|-----------|
| Site motoru | Jekyll 4.x (Ruby) |
| CSS framework | Bootstrap 5.3 |
| Özel stiller | `theme.css` + `app.css` |
| JavaScript | Vanilla JS (filtre, navbar) + Bootstrap bundle |
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
_includes/       Ortak bileşenler (menü, kart, filtre)
assets/css/      Stiller (bootstrap, theme, app)
assets/js/       Script’ler
assets/images/   Görseller ve kapaklar
index.html       Anasayfa
```

Detaylı mimari için [project.md](project.md) dosyasına bakın.

## Yeni Ürün Ekleme

1. `_books/` altında yeni bir `.md` dosyası oluşturun
2. Front matter alanlarını doldurun:

```yaml
---
layout: book
title: "Ürün Adı"
grades: [1, 2]
genre: education
image: assets/images/ean/9786053832874.jpg
ean: 9786053832874
---
Ürün açıklaması buraya...
```

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

## Sayfalar

| URL | Açıklama |
|-----|----------|
| `/` | Anasayfa — slider + sınıf/tür filtreli ürün listesi |
| `/urunler` | Tüm ürünler, dropdown filtreler |
| `/urunler/:title` | Ürün detay |
| `/kataloglar` | Katalog listesi |
| `/kataloglar/:title` | Katalog detay |
| `/hakkimizda` | Hakkımızda |
| `/iletisim` | İletişim |

## Lisans ve İletişim

© Damla Yayınevi — [damlaokul.com](https://damlaokul.com)

- [Facebook](https://www.facebook.com/damlayayinevi)
- [Instagram](https://instagram.com/damlayayinevi)
- [YouTube](https://www.youtube.com/c/damlayayinevi)
- [Twitter](https://twitter.com/damlayayinevi)
