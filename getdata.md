# Damla Okul — Dış veri çekimi

> **Dokümantasyon:** Kurulum [README.md](README.md), mimari [project.md](project.md), tasarım [design.md](design.md). **Bu dosya** TurkiyeAPI, MEB, OOKGM ve HDX kaynaklı JSON’ların tek takip belgesidir; script veya şema değişince burayı güncelleyin.

Öğretmen talep formu (`/ogretmen`) ve okul meta verisi, sitede durağan JSON olarak tutulur. Üretim **beş Python 3 fetch script’i** + **bir sync script** ile yapılır (yalnızca standart kütüphane; `pip` yok). Fetch script’leri `install.sh` / `start.sh` içinde otomatik çalışmaz; [`scripts/sync_site_data.py`](scripts/sync_site_data.py) yalnızca `start.sh` hook’unda tetiklenir (`docs/data` → site dosyaları).

| Script | Kanonik çıktı (`docs/data/`) | Site türetilmiş | Yaklaşık boyut | Tüketici |
|--------|------------------------------|-----------------|----------------|----------|
| [`scripts/fetch_turkiyeadres.py`](scripts/fetch_turkiyeadres.py) | `turkiye_adres.json` | `_data/turkiye_adres_il_ilce.json` (sync) | ~4,7 MB → ~80 KB | Wizard il/ilçe (Jekyll); diğer fetch script’leri kod eşlemesi |
| [`scripts/fetch_geodata.py`](scripts/fetch_geodata.py) | `turkiye_geodata.json` | `assets/data/geodata/` (sync) | ~48 MB → il parçaları | `/okullar` harita sınır overlay |
| [`scripts/fetch_okullar.py`](scripts/fetch_okullar.py) | `okullar.json` | `assets/data/okullar.json` (sync) | ~9–21 MB | Wizard okul adı (`<datalist>`); `fetch_okuldetay.py` girdi |
| [`scripts/fetch_ozel_okullar.py`](scripts/fetch_ozel_okullar.py) | Aynı `okullar.json` (`ozel: true`) | sync | kamu dosyasına ek | Wizard datalist; detay script’i atlar |
| [`scripts/fetch_okuldetay.py`](scripts/fetch_okuldetay.py) | `okullar_detay.json` (monolit) | `assets/data/okullar-harita/{il_kod}.json` (sync) | ~90 MB → il parçaları | `/okullar` harita detay + koordinat |
| [`scripts/fetch_population.py`](scripts/fetch_population.py) | `population.json` | — (sync yok) | ~300 KB | (ileride harita / analiz) |
| [`scripts/sync_site_data.py`](scripts/sync_site_data.py) | — | `turkiye_adres_il_ilce` + `assets/data/*` | türetilmiş | `start.sh`; fetch script’leri bitişte de çağırır |

Sıra zorunlu: adres → (isteğe bağlı geodata) → kamu kurum listesi → özel birleştirme → kurum detayı. Nüfus (`fetch_population.py`) bağımsız; `turkiye_adres.json` önkoşul.

```mermaid
flowchart LR
  api["TurkiyeAPI v2 datasets"] --> adres["docs/data/turkiye_adres.json"]
  hdx["HDX COD-AB zip"] --> geodata["docs/data/turkiye_geodata.json"]
  adres --> geodata
  meb["MEB okullar_ajax.php"] --> okullar["docs/data/okullar.json"]
  ookgm["OOKGM kurumlar.php tur=okul"] --> okullar
  adres --> sync["sync_site_data.py"]
  okullar --> sync
  sync --> slim["_data/turkiye_adres_il_ilce.json"]
  sync --> assets["assets/data/okullar.json"]
  sync --> geoOut["assets/data/geodata/"]
  sync --> haritaOut["assets/data/okullar-harita/"]
  okullar --> detay["docs/data/okullar_detay.json"]
  mebSiteler["meb.k12.tr tema sayfaları"] --> detay
  geodata --> sync
  detay --> sync
  slim --> wizardIl["/ogretmen il-ilçe"]
  assets --> wizardOkul["/ogretmen okul adı"]
  geoOut --> okullarPage["/okullar harita"]
  haritaOut --> okullarPage
```

---

## Ortak kurallar

- Çalıştırma: repo kökünden `python scripts/<script>.py` (Windows Git Bash veya sistem Python 3).
- Ağ: nazik tarama — gecikme, 4 deneme, üstel bekleme. Toplu tarama saatler sürebilir.
- JSON: UTF-8, `ensure_ascii=False`. Adres dosyası girintili; `okullar` / `okullar_detay` / `turkiye_geodata` sıkışık (`separators=(",", ":")`).
- **Kanonik dosyalar** `docs/data/` altında (gitignore: `/docs`). Büyük JSON’lar git’te **tutulmaz**; site için `sync_site_data.py` veya `start.sh` kullanın.
- `_data/turkiye_adres_il_ilce.json` (~80 KB) git’te kalır; clone sonrası il/ilçe wizard sync olmadan çalışır.
- **`_data/okullar_detay.json` kullanılmaz.** Eski mimariden kalan kopya Jekyll build’ini kırar; `sync_site_data.py` başında ve sonunda otomatik silinir; `start.sh` Jekyll öncesi `--cleanup-only` tekrar çağırır (IDE’de açık dosya veya paralel fetch geri yazabilir).
- `--il` kamu script’inde plaka / TurkiyeAPI `kod` (`1` Adana, `34` İstanbul); OOKGM script’inde il adı veya plaka (`ANKARA` / `6`). MEB Bakanlık kaydı il kodu `99` yalnızca kamu listesinde vardır.

---

## 1. Türkiye adresi (`fetch_turkiyeadres.py`)

[TurkiyeAPI v2](https://docs.turkiyeapi.dev/tr/) idari birimleri: il → ilçe → mahalle / köy.

### Kaynak

| Dataset | URL |
|---------|-----|
| Meta | `https://api.turkiyeapi.dev/v2/meta` |
| Ham listeler | `https://api.turkiyeapi.dev/v2/datasets/{provinces,districts,neighborhoods,villages}.json` |

İsteğe bağlı yerel kopya: `docs/data/reference/turkiyeapi/` (`--vendor` yazar, `--from-vendor` okur).

### Komut

```bash
python scripts/fetch_turkiyeadres.py
python scripts/fetch_turkiyeadres.py --vendor
python scripts/fetch_turkiyeadres.py --from-vendor docs/data/reference/turkiyeapi
python scripts/fetch_turkiyeadres.py --output docs/data/turkiye_adres.json
```

Çıktı sayısı kaynak dataset satır sayısıyla doğrulanır; uyuşmazsa script hata verir.

### Şema (`turkiye_adres.json`)

```json
{
  "meta": {
    "kaynak": "https://docs.turkiyeapi.dev/tr/",
    "api": "https://api.turkiyeapi.dev/v2",
    "datasetVersion": "2025",
    "guncelleme": "YYYY-MM-DD",
    "lastUpdated": "API lastUpdated"
  },
  "iller": [
    {
      "kod": 1,
      "ad": "Adana",
      "ilceler": [
        {
          "kod": 1757,
          "ad": "Aladağ",
          "mahalleler": [{ "kod": 248, "ad": "Akpınar" }],
          "koyler": [{ "kod": 0, "ad": "…" }]
        }
      ]
    }
  ]
}
```

- `iller`: 81 il (Bakanlık yok). `kod` plaka ile aynı.
- İlçe / mahalle / köy `kod` değerleri TurkiyeAPI id’leridir; MEB ilçe kodu değildir.
- Wizard il-ilçe seçimi bu ağacın **yalnızca il ve ilçe** katmanını Jekyll ile sayfaya gömer (`ogretmen-adres-il-ilce`). Mahalle/köy formda kullanılmaz.

---

## 2. MEB kurum listesi (`fetch_okullar.py`)

[MEB Okullar ve Diğer Kurumlar](https://www.meb.gov.tr/baglantilar/okullar/index.php) DataTables AJAX çıktısı.

**Önkoşul:** `docs/data/turkiye_adres.json` mevcut olmalı. İl/ilçe adları bu dosyadaki kodlara çözülür (`Afyon` → Afyonkarahisar, `19mayis` → 19 Mayıs gibi takma adlar script içindedir).

### Kaynak

1. `index.php` — il `<select>` (başarısızsa plaka 1–81 + Bakanlık `99`).
2. `okullar_ajax.php` — il bazında `start`/`length=500` sayfalama, `ilce=0` (tüm ilçeler). İl başına `recordsTotal` bitene kadar.

Satır alanları: `OKUL_ADI` (`İL - İLÇE - AD`), `HOST` (`ornek.meb.k12.tr` host parçası), `YOL` (kurum kodu yolu).

### Komut

```bash
python scripts/fetch_okullar.py
python scripts/fetch_okullar.py --il 1
python scripts/fetch_okullar.py --output docs/data/okullar.json
```

`--il` yalnızca o ili çeker; çıktı dosyasını **tüm ülkenin üzerine yazar** (kısmi dosyayı `okullar.json` sanmayın). Tam liste için argümansız çalıştırın.

Gecikme: il içi sayfalar ve iller arası 0,4 sn. Tam tarama onlarca dakika sürebilir.

Çıktı `docs/data/okullar.json`; bitişte `sync_site_data.py` `assets/data/okullar.json` üretir. Dosya **sıfırdan** yazılır; önceki OOKGM özel kayıtlar silinir — ardından [`fetch_ozel_okullar.py`](scripts/fetch_ozel_okullar.py) çalıştırın.

### Şema (`okullar.json`)

```json
{
  "kaynak": "https://www.meb.gov.tr/baglantilar/okullar/index.php",
  "referans": "docs/data/turkiye_adres.json",
  "guncelleme": "YYYY-MM-DD",
  "sayi": 67754,
  "kaynak_ozel": "https://ookgm.meb.gov.tr/kurumlar.php?tur=okul",
  "sayi_ozel": 12552,
  "iller": {
    "1": {
      "ad": "Adana",
      "ilceler": {
        "1104": {
          "ad": "Seyhan",
          "kurumlar": [
            {
              "ad": "125. Yıl Ortaokulu",
              "tur": "Ortaokul",
              "kurum_kodu": "726071",
              "web": "https://125yilortaokuluseyhan.meb.k12.tr/"
            }
          ]
        }
      }
    }
  }
}
```

| Alan | Not |
|------|-----|
| `iller` / `ilceler` anahtarı | TurkiyeAPI `kod` (string). Eşleşmeyen ilçe kodu `"0"`. |
| `tur` | Kamu: kurum adından kural tablosu (`İlkokul`, `Fen Lisesi`, `Özel Eğitim`, …); bilinmeyen → `Diğer`. Özel: OOKGM resmi tür alanı (ör. `Özel Türk İlkokulu`); `infer_tur()` uygulanmaz. |
| `ozel` | Yalnızca OOKGM kayıtlarında `true`. Kamu kayıtlarda alan yoktur. |
| `kurum_kodu` | MEB yolunun son parçası; detay JSON’un anahtarı. Özel kayıtlarda **yok**. |
| `web` | `https://{HOST}.meb.k12.tr/` — yoksa alan yazılmaz. Özel kayıtlarda **yok**. |
| `adres` / `telefon` | OOKGM özel kayıtlarda doldurulur (varsa). |
| `99` | Bakanlık / merkezi kurumlar; ilçe kodu `0`. |
| `kaynak` | Kamu MEB URL’si (değişmez). |
| `kaynak_ozel` / `sayi_ozel` | OOKGM birleştirmesinden sonra; `sayi` kamu + özel toplamdır. |

Eşleşmeyen il/ilçe sayısı stderr’de `[UYARI]` olarak raporlanır; kayıt yine yazılır.

Kamu listesindeki “Özel” neredeyse tamamen **Özel Eğitim** veya **Özel İdare** adlarıdır; koleji / “Özel … İlkokulu” sicili OOKGM’den gelir.

---

## 2b. OOKGM özel okullar (`fetch_ozel_okullar.py`)

[OOKGM kurumlar.php?tur=okul](https://ookgm.meb.gov.tr/kurumlar.php?tur=okul) — özel okul sicili (ilçe, resmi tür, adres, telefon). **Kurum kodu ve web yok.** Kurs / yurt / rehabilitasyon (`tur=okul` dışı) çekilmez.

**Önkoşul:** `docs/data/okullar.json` (kamu listesi) ve `docs/data/turkiye_adres.json`. `fetch_okullar.py` yeniden çalıştırılmaz; mevcut dosyaya eklenir.

### Kaynak

1. `kurumlar.php?tur=okul` — il `<select>`. Listede olmayan iller (ör. Ardahan) `docs/data/turkiye_adres.json` ile denenir; sunucu varsayılan ile (Adana) dönerse kayıt **yazılmaz**.
2. Her il: `GET kurumlar.php?sayfa=N&tur=okul&il=ADANA&tur2=0`. Sayfa boyu ~250. İlk HTML’deki `sayfa=` linklerinden max sayfa okunur; `N=1..max` dolaşılır.
3. Tablo: ilçe, ad (BÜYÜK HARF → `title_tr`), tür (OOKGM resmi metin), adres, telefon (`tel:` veya rakam).

Sitedeki “N adet kurum bulundu” sayacı sayfa linkleriyle uyuşmayabilir (ör. Ankara 1565 yazar, tabloda 1450 benzersiz satır). Script tablo satırını kaynak alır; farkı `[UYARI]` basar.

ÖSYM 2017–2018 “Ortaöğretim Kurumları Kitapçığı” 2026’da yayımlanmıyor; okul bazında kod listesi yok. Bu script ÖSYM PDF/kılavuz birleştirmez.

### Komut

```bash
python scripts/fetch_ozel_okullar.py
python scripts/fetch_ozel_okullar.py --il ANKARA
python scripts/fetch_ozel_okullar.py --delay 0.4 --output docs/data/okullar.json
```

`--il` yalnızca o ilin `ozel === true` kayıtlarını silip taze OOKGM listesini yazar; kamu kayıtlara ve diğer illerin özel kayıtlarına dokunmaz. Üretim için argümansız çalıştırın (tüm özel kayıtlar yenilenir). Testte `--output` ile geçici dosya kullanın.

Gecikme varsayılan 0,4 sn. Çıktı kanonik yoldaysa bitişte `sync_site_data.py` `assets/data/okullar.json` üretir.

2026-08-22 tam çekim: `sayi=67754`, `sayi_ozel=12552` (kamu 55202). OOKGM `<select>` 80 il; Ardahan yok. 2 kayıt kamu adıyla çakıştığı için atlandı.

### Birleştirme

- Yeniden çalıştırmada önce ilgili `ozel === true` kayıtlar silinir, sonra taze liste eklenir.
- Çakışma (aynı il/ilçe + `fold_tr(ad)`): kamu kaydı durur; özel atlanır, uyarı sayacı.
- `fetch_okuldetay.py` `kurum_kodu` + `web` olmayanı zaten atlar; özel kayıtlar detaya girmez.
- Wizard `populateSchoolList` yalnızca `kurum.ad` kullanır; özel okullar datalist’e düşer (ayrı rozet yok).

Özel kayıt örneği:

```json
{
  "ad": "Özel Adana Doğa İlkokulu",
  "tur": "Özel Türk İlkokulu",
  "ozel": true,
  "adres": "BELEDİYE EVLERİ MAH. …",
  "telefon": "3222471144"
}
```

---

## 3. MEB okul detayı (`fetch_okuldetay.py`)

Her kurumun `web` adresindeki tema sayfalarından meta. **Girdi:** `docs/data/okullar.json` (`kurum_kodu` + `web` dolu olanlar; OOKGM özel kayıtlar atlanır).

### Sayfalar

```mermaid
flowchart LR
  hakkinda["tema/okulumuz_hakkinda.php"] --> rec["kurum kaydı"]
  rec --> iletisim["tema/iletisim.php"]
  iletisim --> harita["tema/harita.php yedek"]
  iletisim --> teskilat["tema/teskilat.php"]
  harita --> rec
  teskilat --> rec
```

| Sayfa | Ne alınır |
|-------|-----------|
| `tema/okulumuz_hakkinda.php` | Derslik / öğretmen / öğrenci, iletişim (varsa), şablon (`tema-2`…`tema-6`). İstatistik yoksa anasayfa yedek. |
| `tema/iletisim.php` | Boş telefon / belgegeçer / adres / e-posta / ulaşım; harita koordinatı. |
| `tema/harita.php` | Yalnızca `enlem` yoksa. `?R=1` kullanılmaz (JS yönlendirme). 500 kaydı bozmaz, atlanır. |
| `tema/teskilat.php` | Tüm açık kadro. `idari_personel/*.html` **çekilmez**. |

Koordinat: iframe `maps/embed` `q=lat,lng`, `LatLng()`, `@lat,lng`, `ll=`, `data-lat`/`data-lng`. Türkiye kutu kontrolü (~35–43,5 N, 25–45,5 E). `harita_url` = `https://www.google.com/maps?q={enlem},{boylam}`.

Kadro (`ul#seviyeN a`): `ad`, `unvan` (`title` / `alt` / `<span>`), `seviye`, varsa `telefon` / `eposta`. Boş anahtar yazılmaz.

- Bitişik unvan: `HASAN BİLİCİOKUL MÜDÜRÜ` → ad + unvan.
- Maskeli ad (`YU.. ME..`, en az iki `..`): ek alan yoksa satır atlanır; unvan/telefon/eposta varsa **maskeli `ad` olduğu gibi** yazılır.
- `mudur`: unvanı müdür (yardımcı değil) olan ilk **açık** isim; yoksa teşkilatın ilk açık adı. Hepsi maskeliyse alan yazılmaz.
- Placeholder ad (`.`, `-`) atlanır.

SSL: OpenSSL, host adındaki `_` karakterini joker `*.meb.k12.tr` ile reddeder. Script bu hostlarda `check_hostname` kapatır, SAN’ı kendisi doğrular.

### Resume (kritik)

Varsayılan mevcut `docs/data/okullar_detay.json` üzerine devam eder.

| Durum | Davranış |
|-------|----------|
| `durum=ok` **ve** `iletisim_durum` dolu | Atla (tamamlanmış). |
| `durum=ok` ama `iletisim_durum` yok | Hakkında **yeniden çekilmez**; yalnızca iletisim (+ harita yedek) + teskilat. İstatistikler korunur. |
| Diğer (`parse_eksik`, `http_hata`, yok) | Hakkında + ekstra sayfalar. |
| `--force` | Her şeyi baştan (hakkinda + iletisim + teskilat). |
| `--no-resume` | Çıktı dosyasını yok say, sıfırdan. |

`--limit` / `--il` / `--kurum-kodu` hedef kümeyi daraltır; resume kuralları aynı kalır.

Gecikme varsayılan 0,3 sn (okullar arası). Checkpoint: her 100 kurumda atomik yazım (`*.tmp` → replace). `Ctrl+C` mevcut durumu yazar (çıkış 130).

Tam tarama (~55k × 2 istek + seyrek harita) birçok saat sürer. Kesilirse aynı komutu tekrarlayın.

### Komut

```bash
python scripts/fetch_okuldetay.py
python scripts/fetch_okuldetay.py --il 1 --limit 20
python scripts/fetch_okuldetay.py --kurum-kodu 726071
python scripts/fetch_okuldetay.py --force --kurum-kodu 726071
python scripts/fetch_okuldetay.py --delay 0.5
python scripts/fetch_okuldetay.py --prune
```

Doğrulama örnekleri (Adana, tema 3/4/6): 125. Yıl Ortaokulu (`726071`), 19 Mayıs Anadolu Lisesi (`111512`), 5 Ocak Ortaokulu (`726185`).

### Şema (`okullar_detay.json`)

Kök:

```json
{
  "kaynak": "meb.k12.tr/tema/okulumuz_hakkinda.php+iletisim.php+teskilat.php",
  "referans": "docs/data/okullar.json",
  "guncelleme": "YYYY-MM-DD",
  "sayi": 55202,
  "kurumlar": {
    "726071": { }
  }
}
```

Kayıt alanları (hepsi her okulda yok; boş anahtar yazılmaz):

| Alan | Anlam |
|------|--------|
| `kurum_kodu`, `web` | Girdi kopyası |
| `sablon` | `tema-2` … `tema-6` veya `bilinmiyor` |
| `durum` | `ok` \| `parse_eksik` \| `http_hata` \| `zaman_asimi` |
| `derslik_sayisi`, `ogretmen_sayisi`, `ogrenci_sayisi` | Tam sayı |
| `telefon`, `belgegecer`, `adres`, `eposta` | İletişim (`eposta` yalnızca geçerli adres; `mailto:` veya metin) |
| `enlem`, `boylam` | float |
| `harita_url` | Google Maps `q=` |
| `mudur` | Açık müdür adı |
| `kadro` | `[{ "ad", "unvan", "seviye", "telefon", "eposta" }]` |
| `alanlar` | Eşleşmeyen etiket→değer (Vizyon, Misyon, Başarılar, Saatler, Yerleşim Yeri, İl/İlçe Merkezine Uzaklık, Ulaşım, Servis/Pansiyon, Isınma, Yazdır/Web atlanır) |
| `iletisim_durum` | `ok` \| `yok` \| `hata` — iletisim.php denendi; resume anahtarı |

İletisim/teskilat, mevcut hakkinda alanlarının **üstüne yazmaz** (boşsa doldurur).

---

## 4. Harita sınır verisi (`fetch_geodata.py`)

[HDX COD-AB](https://data.humdata.org/dataset/cod-ab-tur) — Harita Genel Müdürlüğü kaynaklı ülke (ADM0), il (ADM1, 81) ve ilçe (ADM2, 973) sınır poligonları. Koordinat noktaları (okul vb.) bu dosyada **yoktur**; harita uygulaması sınır overlay ile `okullar_detay` noktalarını ayrı katmanda birleştirir.

**Önkoşul:** `docs/data/turkiye_adres.json` mevcut olmalı (il/ilçe `kod` eşlemesi).

### Kaynak

| Öğe | Değer |
|-----|-------|
| Dataset | [Türkiye - Subnational Administrative Boundaries (COD-AB)](https://data.humdata.org/dataset/cod-ab-tur) |
| ZIP | `tur_admin_boundaries.geojson.zip` (~22 MB) |
| URL | `https://data.humdata.org/dataset/cod-ab-tur/resource/470bd810-2240-4ce0-b5c4-17434112ce41/download/tur_admin_boundaries.geojson.zip` |
| SHA-256 | `6d45f15de76d53da057312dfaedb60248141a1828ce6a5c7cbfeedc7f51714c3` |
| Lisans | CC BY-IGO |
| CRS | WGS84 (EPSG:4326), GeoJSON `[boylam, enlem]` |

İsteğe bağlı yerel kopya: `docs/data/reference/hdx/` (`--vendor` yazar, `--from-vendor` okur).

HDX ilçe adı il adıyla aynı olduğunda (ör. Adıyaman ili / Adıyaman ilçesi) `turkiye_adres` içindeki **Merkez** ilçesine eşlenir.

### Komut

```bash
python scripts/fetch_geodata.py
python scripts/fetch_geodata.py --vendor
python scripts/fetch_geodata.py --from-vendor docs/data/reference/hdx
python scripts/fetch_geodata.py --adres docs/data/turkiye_adres.json
python scripts/fetch_geodata.py --output docs/data/turkiye_geodata.json
```

2026-08-22 üretim: `sayi.ulke=1`, `sayi.il=81`, `sayi.ilce=973`; çıktı ~48 MB.

### Şema (`turkiye_geodata.json`)

```json
{
  "meta": {
    "kaynak": "https://data.humdata.org/dataset/cod-ab-tur",
    "lisans": "CC BY-IGO",
    "EPSG": 4326,
    "referans": "docs/data/turkiye_adres.json",
    "katmanlar": ["ulke", "il", "ilce"],
    "sayi": { "ulke": 1, "il": 81, "ilce": 973 }
  },
  "ulke": {
    "pcode": "TUR",
    "ad": "Türkiye",
    "geometry": { "type": "MultiPolygon", "coordinates": [] },
    "bbox": [25.66, 35.80, 44.82, 42.10]
  },
  "iller": {
    "34": {
      "kod": 34,
      "ad": "İstanbul",
      "pcode": "TUR034",
      "geometry": { "type": "MultiPolygon", "coordinates": [] },
      "bbox": [],
      "merkez": [28.97, 41.01],
      "ilceler": {
        "1103": {
          "kod": 1103,
          "ad": "Kadıköy",
          "geometry": { "type": "Polygon", "coordinates": [] },
          "bbox": [],
          "merkez": []
        }
      }
    }
  }
}
```

| Alan | Not |
|------|-----|
| `iller` / `ilceler` anahtarı | `turkiye_adres` / `okullar.json` ile aynı string `kod` |
| `geometry` | GeoJSON `Polygon` veya `MultiPolygon` |
| `bbox` | `[minLon, minLat, maxLon, maxLat]` — zoom-to-fit |
| `merkez` | HDX `center_lon` / `center_lat` → `[boylam, enlem]` |
| Mahalle sınırı | Bu dosyada yok; ülke geneli resmi kaynak bulunmuyor |

Harita katmanları: OSM taban + `ulke`/`iller`/`ilceler` poligon overlay + `okullar_detay` `enlem`/`boylam` marker (lazy `fetch`).

---

## Sitede kullanım

| Veri | Nasıl |
|------|--------|
| `_data/turkiye_adres_il_ilce.json` | [`_includes/ogretmen-wizard/step-contact.html`](_includes/ogretmen-wizard/step-contact.html) ve [`_layouts/okullar-harita.html`](_layouts/okullar-harita.html) — il/ilçe seçimi. `sync_site_data.py` ile `docs/data/turkiye_adres.json` kaynaklı. |
| `assets/data/okullar.json` | [`_layouts/ogretmen-wizard.html`](_layouts/ogretmen-wizard.html) — `OKULLAR_URL` ile `fetch`; seçilen il/ilçeye göre okul `<datalist>` (kamu + özel ad). |
| `assets/data/geodata/` | [`_pages/okullar.md`](_pages/okullar.md) — `index.json` + `il/{kod}.json` lazy fetch; ülke/il/ilçe choropleth. `sync_site_data.py` → `docs/data/turkiye_geodata.json` + okul sayıları. |
| `assets/data/okullar-harita/` | Aynı sayfa — `meta.json` + `{il_kod}.json` lazy fetch; okul listesi, detay ve koordinatlı marker. `sync_site_data.py` monolit `okullar_detay.json` + `okullar.json` birleşimini il parçalarına böler. |
| `docs/data/okullar_detay.json` | Kanonik monolit; tarayıcıya ve Jekyll `site.data`'ya girmez. |
| `docs/data/turkiye_geodata.json` | Kanonik; tarayıcıya doğrudan gitmez. |

**`/okullar` hayalet sayfa:** menü, footer, `llms.txt` ve sitemap dışı; `robots: noindex, nofollow`; `ghost: true` → `ai-seo-crawler` yok. Yalnızca doğrudan URL ile erişilir.

Wizard mimarisi: [project.md — Öğretmen talep formu](project.md#öğretmen-talep-formu-wizard).

---

## Güncelleme sırası

1. `python scripts/fetch_turkiyeadres.py` — ilçe/mahalle değiştiyse veya yılda bir.
2. `python scripts/fetch_geodata.py` — harita sınırı güncellemesi (adres dosyasına bağlı; yılda bir veya HDX revizyonunda).
3. `python scripts/fetch_okullar.py` — kamu kurum listesi / HOST güncellemesi. Bitişte sync `assets/data/okullar.json` üretir (**özel kayıtlar bu adımda silinir**; ardından adım 4).
4. `python scripts/fetch_ozel_okullar.py` — OOKGM özel okulları mevcut `docs/data/okullar.json` içine birleştirir; sync assets kopyasını yazar.
5. `python scripts/fetch_okuldetay.py` — yeni veya eksik detay. Bitişte sync harita il parçalarını günceller. Önceki kamu adımı `web`/`kurum_kodu` değiştirdiyse `--force` veya ilgili `--kurum-kodu`.
6. `python scripts/sync_site_data.py` — harita parçaları dahil tüm site türetilmiş dosyalar (`start.sh` bunu da çağırır).
7. Bu belgedeki tarih/sayı notunu gerekirse güncelleyin; şema değiştiyse örnek JSON’u da.

Tek il denemesi çıktıyı kısmi yapmasın diye `fetch_okullar.py --il` üretim dosyasına yazılmamalıdır. `fetch_ozel_okullar.py --il` diğer illeri silmez ama testte yine `--output` kullanın. Detay için `--il` / `--limit` güvenlidir (resume diğer illeri silmez).

---

## 6. Nüfus verisi (`fetch_population.py`)

İl ve ilçe düzeyinde toplam nüfus (TurkiyeAPI / TÜİK MEDAS) ile çocuk nüfusu 0–14 ve 0–17 (TÜİK ADNKS yaş tablosu, vendor CSV).

### Kaynak

| Katman | Kaynak | Erişim |
|--------|--------|--------|
| Toplam nüfus | [TurkiyeAPI v2](https://api.turkiyeapi.dev/v2) `population` | Otomatik (`provinces.json`, `districts.json`) |
| Çocuk 0–14 / 0–17 | TÜİK ADNKS il/ilçe yaş-cinsiyet | Vendor CSV (`docs/data/reference/tuik/`) |

TÜİK’in NIP / veriportali arayüzleri halka açık REST API sunmaz; çocuk nüfusu için tabloyu indirip vendor klasörüne koyun. Ayrıntı: [`docs/data/reference/tuik/README.md`](docs/data/reference/tuik/README.md).

### Önkoşul

`docs/data/turkiye_adres.json` (il/ilçe kod eşlemesi).

### Komut

```bash
# Üretim: güncel TÜİK vendor CSV ile
python scripts/fetch_population.py --yil 2024

# TurkiyeAPI snapshot (isteğe bağlı)
python scripts/fetch_population.py --turkiyeapi-vendor docs/data/reference/turkiyeapi

# Geliştirme: eoner 2014 bootstrap + yeni ilçe imputasyonu
python scripts/fetch_population.py --bootstrap-vendor --vendor-yil 2014 --yil 2024 --impute-new-ilce
```

`sync_site_data.py` çağrılmaz (geodata gibi).

### Şema (`population.json`)

```json
{
  "meta": {
    "kaynak": {
      "toplam_nufus": "https://api.turkiyeapi.dev/v2 (TÜİK MEDAS)",
      "cocuk_nufus": "TÜİK ADNKS — il/ilçe yaş-cinsiyet tablosu (vendor CSV)"
    },
    "referans": "docs/data/turkiye_adres.json",
    "yil": 2024,
    "vendor_yil": 2024,
    "vendor_mode": "tidy",
    "datasetVersion": "2025",
    "guncelleme": "YYYY-MM-DD",
    "tanimlar": {
      "cocuk_0_14": "ADNKS yaş bağımlılık oranı çocuk tanımı (0–14)",
      "cocuk_0_17": "BM / İstatistiklerle Çocuk tanımı (0–17)"
    }
  },
  "turkiye": {
    "nufus": 85664944,
    "cocuk_0_14": 17900000,
    "cocuk_0_17": 24500000
  },
  "iller": {
    "34": {
      "kod": 34,
      "ad": "İstanbul",
      "nufus": 15701702,
      "cocuk_0_14": 3280000,
      "cocuk_0_17": 4500000,
      "ilceler": {
        "1103": {
          "kod": 1103,
          "ad": "Adalar",
          "nufus": 17489,
          "cocuk_0_14": 2100,
          "cocuk_0_17": 2800
        }
      }
    }
  }
}
```

- İl anahtarı: plaka string (`"34"`). İlçe anahtarı: TurkiyeAPI ID (`"1103"`).
- `nufus` = TurkiyeAPI; `cocuk_*` = TÜİK vendor.
- Doğrulama: 81 il, 973 ilçe; her kayıtta `cocuk_0_14 <= cocuk_0_17 <= nufus`.

---

## Bilinen kısıtlar

- **HOST virgülü:** MEB `HOST` alanında virgül olan kayıt DNS çözmez (ör. kademeli özel eğitim siteleri). `web` yine yazılır; detay `http_hata` olabilir. Kardeş kademeler ayrı `kurum_kodu` ile listede durur.
- **Maskeli kadro:** KVKK nedeniyle bazı teşkilat sayfaları `EM.. ER...` basar. Unvan varsa satır kalır; `mudur` açık isim yoksa boştur.
- **Ulaşım metni:** Tema 6 ikon satırı; bazı tema 4 tablolarında ulaşım adres hücresine gömülüdür (`Hizmet Binasına Ulaşım --->`). Cümle içindeki “ulaşım sağlanmaktadır” ayrı alan yapılmaz.
- **`harita.php?R=1`:** Footer linki yönlendirmedir; koordinat `iletisim.php` veya sorgusuz `harita.php` içindedir.
- **404 / timeout:** `iletisim_durum=yok|hata`; hakkinda `durum` değişmez (extra-only). Hakkinda tamamen düşerse `durum` hata kodudur.
- **Büyüklük:** `docs/data/okullar_detay.json` (monolit) ve `turkiye_geodata.json` GitHub / editör için ağırdır; git’te tutulmaz (`/docs` gitignore). Site tarafında sync il parçaları üretir (`assets/data/okullar-harita/`).
- **Mahalle sınırı:** `turkiye_geodata.json` yalnızca ülke/il/ilçe içerir; mahalle poligonu ülke genelinde yok.
- **OOKGM sayacı:** “N adet kurum bulundu” ile tablo satır sayısı uyuşmayabilir; tablo kaynak kabul edilir.
- **Özel kurum kodu:** 2026’da okul bazında açık MEB/ÖSYM kod listesi yok; özel kayıtlarda `kurum_kodu` / `web` yazılmaz.

---

## Komut özeti

```bash
python scripts/fetch_turkiyeadres.py
python scripts/fetch_geodata.py
python scripts/fetch_okullar.py
python scripts/fetch_ozel_okullar.py
python scripts/sync_site_data.py
python scripts/fetch_okuldetay.py --il 1 --limit 20
python scripts/fetch_okuldetay.py
python scripts/fetch_population.py --yil 2024
```
