#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MEB Okullar ve Diğer Kurumlar → docs/data/okullar.json"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from data_paths import CANONICAL, REF_TURKIYE_ADRES

ROOT = Path(__file__).resolve().parents[1]
ADRES_PATH = CANONICAL["turkiye_adres"]
OUTPUT_PATH = CANONICAL["okullar"]
BAKANLIK_IL_KOD = "99"

INDEX_URL = "https://www.meb.gov.tr/baglantilar/okullar/index.php"
AJAX_URL = "https://www.meb.gov.tr/baglantilar/okullar/okullar_ajax.php"
REFERER = "https://www.meb.gov.tr/baglantilar/okullar/index.php"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

BATCH_SIZE = 500
DELAY_SEC = 0.4
MAX_RETRIES = 4
RETRY_BACKOFF = 2.0

# En uzun eşleşme önce. (desen, tür etiketi)
TUR_PATTERNS: List[Tuple[str, str]] = [
    ("mesleki ve teknik anadolu lisesi", "Mesleki ve Teknik Anadolu Lisesi"),
    ("çok programlı anadolu lisesi", "Çok Programlı Anadolu Lisesi"),
    ("anadolu imam hatip lisesi", "Anadolu İmam Hatip Lisesi"),
    ("imam hatip ortaokulu", "İmam Hatip Ortaokulu"),
    ("imam hatip lisesi", "İmam Hatip Lisesi"),
    ("sosyal bilimler lisesi", "Sosyal Bilimler Lisesi"),
    ("güzel sanatlar lisesi", "Güzel Sanatlar Lisesi"),
    ("ilçe millî eğitim müdürlüğü", "İlçe Milli Eğitim Müdürlüğü"),
    ("ilçe milli eğitim müdürlüğü", "İlçe Milli Eğitim Müdürlüğü"),
    ("il millî eğitim müdürlüğü", "İl Milli Eğitim Müdürlüğü"),
    ("il milli eğitim müdürlüğü", "İl Milli Eğitim Müdürlüğü"),
    ("millî eğitim müdürlüğü", "Milli Eğitim Müdürlüğü"),
    ("milli eğitim müdürlüğü", "Milli Eğitim Müdürlüğü"),
    ("rehberlik ve araştırma merkezi", "Rehberlik ve Araştırma Merkezi"),
    ("halk eğitimi merkezi", "Halk Eğitimi Merkezi"),
    ("mesleki eğitim merkezi", "Mesleki Eğitim Merkezi"),
    ("bilim ve sanat merkezi", "Bilim ve Sanat Merkezi"),
    ("öğretmenevi ve akşam sanat okulu", "Öğretmenevi"),
    ("özel eğitim uygulama okulu", "Özel Eğitim"),
    ("özel eğitim meslek okulu", "Özel Eğitim"),
    ("özel eğitim iş uygulama merkezi", "Özel Eğitim"),
    ("özel eğitim anaokulu", "Özel Eğitim"),
    ("olgunlaşma enstitüsü", "Olgunlaşma Enstitüsü"),
    ("açık öğretim lisesi", "Açık Öğretim Lisesi"),
    ("mesleki açık öğretim", "Açık Öğretim Lisesi"),
    ("yatılı bölge okulu", "Yatılı Bölge Okulu"),
    ("yatılı bölge ortaokulu", "Yatılı Bölge Okulu"),
    ("fen lisesi", "Fen Lisesi"),
    ("spor lisesi", "Spor Lisesi"),
    ("anadolu lisesi", "Anadolu Lisesi"),
    ("öğretmenevi", "Öğretmenevi"),
    ("öğretmen evi", "Öğretmenevi"),
    ("eğitim ve uygulama merkezi", "Özel Eğitim"),
    ("hizmetiçi eğitim enstitüsü", "Hizmetiçi Eğitim Enstitüsü"),
    ("milli eğitim yayınevi", "Milli Eğitim Yayınevi"),
    ("bilsem", "Bilim ve Sanat Merkezi"),
    ("özel eğitim", "Özel Eğitim"),
    ("anaokulu", "Anaokulu"),
    ("ilkokulu", "İlkokul"),
    ("ilkokul", "İlkokul"),
    ("ortaokulu", "Ortaokul"),
    ("ortaokul", "Ortaokul"),
    ("lisesi", "Lise"),
    ("lise", "Lise"),
    (" ybo", "Yatılı Bölge Okulu"),
]


IL_ALIASES = {
    "afyon": "Afyonkarahisar",
}

ILCE_ALIASES = {
    "ondokuzmayis": "19 mayıs",
    "19mayis": "19 mayıs",
    "dogubeyazit": "Doğubayazıt",
    "poturge": "Pütürge",
    "cagliyancerit": "Çağlayancerit",
}


def fold_tr(text: str) -> str:
    """Türkçe harfleri küçük harfe çevir (i/İ ayrımı korunur)."""
    text = unicodedata.normalize("NFC", text or "")
    table = str.maketrans(
        {
            "I": "ı",
            "İ": "i",
            "Ş": "ş",
            "Ğ": "ğ",
            "Ü": "ü",
            "Ö": "ö",
            "Ç": "ç",
            "Â": "a",
            "â": "a",
            "Î": "i",
            "î": "i",
            "Û": "u",
            "û": "u",
        }
    )
    return text.translate(table).lower()


def fold_ascii(text: str) -> str:
    """Karşılaştırma için ASCII katlama (bağcılar ≈ bagcilar)."""
    t = fold_tr(text).translate(
        str.maketrans(
            {
                "ğ": "g",
                "ü": "u",
                "ş": "s",
                "ı": "i",
                "ö": "o",
                "ç": "c",
            }
        )
    )
    return re.sub(r"[^a-z0-9]+", "", t)


def title_tr(text: str) -> str:
    """Kelime başlarını Türkçe title-case yap."""
    parts = re.split(r"(\s+|-)", text.strip())
    out = []
    for part in parts:
        if not part or part.isspace() or part == "-":
            out.append(part)
            continue
        folded = fold_tr(part)
        if not folded:
            out.append(part)
            continue
        first = folded[0]
        first_map = {
            "i": "İ",
            "ı": "I",
            "ş": "Ş",
            "ğ": "Ğ",
            "ü": "Ü",
            "ö": "Ö",
            "ç": "Ç",
        }
        out.append(first_map.get(first, first.upper()) + folded[1:])
    return "".join(out)


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


class IlSelectParser(HTMLParser):
    """index.php içindeki il <select> seçeneklerini toplar."""

    def __init__(self) -> None:
        super().__init__()
        self._in_select = False
        self._select_name = ""
        self._in_option = False
        self._option_value = ""
        self._option_text: List[str] = []
        self.iller: List[Tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        ad = dict(attrs)
        if tag == "select":
            name = (ad.get("name") or ad.get("id") or "").lower()
            if "il" in name and "ilce" not in name:
                self._in_select = True
                self._select_name = name
        elif tag == "option" and self._in_select:
            self._in_option = True
            self._option_value = (ad.get("value") or "").strip()
            self._option_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "select" and self._in_select:
            self._in_select = False
        elif tag == "option" and self._in_option:
            label = re.sub(r"\s+", " ", "".join(self._option_text)).strip()
            if self._option_value and label and fold_tr(label) not in ("tümü", "tumü", "seçiniz", "seciniz"):
                self.iller.append((self._option_value, label))
            self._in_option = False

    def handle_data(self, data: str) -> None:
        if self._in_option:
            self._option_text.append(data)


def http_request(
    url: str,
    data: Optional[bytes] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 60,
) -> bytes:
    req_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/html, */*; q=0.01",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    }
    if headers:
        req_headers.update(headers)
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, data=data, headers=req_headers, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read()


def request_with_retry(url: str, data: Optional[bytes] = None, headers: Optional[Dict[str, str]] = None) -> bytes:
    last_err: Optional[BaseException] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return http_request(url, data=data, headers=headers)
        except (urllib.error.URLError, TimeoutError, ssl.SSLError, ConnectionError) as exc:
            last_err = exc
            wait = RETRY_BACKOFF * attempt
            print(f"  [WARN] istek başarısız ({attempt}/{MAX_RETRIES}): {exc}; {wait:.1f}s sonra tekrar", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"İstek başarısız: {url}") from last_err


def parse_iller_from_index(html: str) -> List[Tuple[str, str]]:
    parser = IlSelectParser()
    parser.feed(html)
    if parser.iller:
        return parser.iller

    # Yedek: bazı sürümlerde il listesi JS/option dışında da gelebilir.
    found: List[Tuple[str, str]] = []
    for match in re.finditer(
        r'<option[^>]*value=["\']([^"\']+)["\'][^>]*>([^<]+)</option>',
        html,
        flags=re.I,
    ):
        value, label = match.group(1).strip(), strip_html(match.group(2))
        if value and label and fold_tr(label) not in ("tümü", "tumü", "seçiniz", "seciniz"):
            found.append((value, label))
    return found


def fallback_iller() -> List[Tuple[str, str]]:
    """index.php parse edilemezse plaka kodları (1–81) + Bakanlık."""
    names = [
        "ADANA", "ADIYAMAN", "AFYONKARAHİSAR", "AĞRI", "AMASYA", "ANKARA", "ANTALYA",
        "ARTVİN", "AYDIN", "BALIKESİR", "BİLECİK", "BİNGÖL", "BİTLİS", "BOLU",
        "BURDUR", "BURSA", "ÇANAKKALE", "ÇANKIRI", "ÇORUM", "DENİZLİ", "DİYARBAKIR",
        "EDİRNE", "ELAZIĞ", "ERZİNCAN", "ERZURUM", "ESKİŞEHİR", "GAZİANTEP", "GİRESUN",
        "GÜMÜŞHANE", "HAKKARİ", "HATAY", "ISPARTA", "MERSİN", "İSTANBUL", "İZMİR",
        "KARS", "KASTAMONU", "KAYSERİ", "KIRKLARELİ", "KIRŞEHİR", "KOCAELİ", "KONYA",
        "KÜTAHYA", "MALATYA", "MANİSA", "KAHRAMANMARAŞ", "MARDİN", "MUĞLA", "MUŞ",
        "NEVŞEHİR", "NİĞDE", "ORDU", "RİZE", "SAKARYA", "SAMSUN", "SİİRT", "SİNOP",
        "SİVAS", "TEKİRDAĞ", "TOKAT", "TRABZON", "TUNCELİ", "ŞANLIURFA", "UŞAK",
        "VAN", "YOZGAT", "ZONGULDAK", "AKSARAY", "BAYBURT", "KARAMAN", "KIRIKKALE",
        "BATMAN", "ŞIRNAK", "BARTIN", "ARDAHAN", "IĞDIR", "YALOVA", "KARABÜK",
        "KİLİS", "OSMANİYE", "DÜZCE",
    ]
    rows = [(str(i), names[i - 1]) for i in range(1, 82)]
    rows.append(("99", "BAKANLIK"))
    return rows


def ajax_payload(il: str, start: int, length: int, draw: int = 1) -> bytes:
    fields: Dict[str, str] = {
        "draw": str(draw),
        "columns[0][data]": "OKUL_ADI",
        "columns[0][name]": "",
        "columns[0][searchable]": "true",
        "columns[0][orderable]": "true",
        "columns[0][search][value]": "",
        "columns[0][search][regex]": "false",
        "columns[1][data]": "OKUL_ADI",
        "columns[1][name]": "",
        "columns[1][searchable]": "true",
        "columns[1][orderable]": "true",
        "columns[1][search][value]": "",
        "columns[1][search][regex]": "false",
        "columns[2][data]": "OKUL_ADI",
        "columns[2][name]": "",
        "columns[2][searchable]": "true",
        "columns[2][orderable]": "true",
        "columns[2][search][value]": "",
        "columns[2][search][regex]": "false",
        "order[0][column]": "0",
        "order[0][dir]": "asc",
        "order[0][name]": "",
        "start": str(start),
        "length": str(length),
        "search[value]": "",
        "search[regex]": "false",
        "il": il,
        "ilce": "0",
    }
    return urllib.parse.urlencode(fields).encode("utf-8")


def fetch_il_rows(il_kodu: str) -> List[Dict[str, Any]]:
    collected: List[Dict[str, Any]] = []
    start = 0
    draw = 1
    total: Optional[int] = None
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://www.meb.gov.tr",
        "Referer": REFERER,
        "X-Requested-With": "XMLHttpRequest",
    }
    while True:
        body = ajax_payload(il_kodu, start=start, length=BATCH_SIZE, draw=draw)
        raw = request_with_retry(AJAX_URL, data=body, headers=headers)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"JSON değil (il={il_kodu} start={start}): {raw[:200]!r}") from exc

        rows = payload.get("data") or []
        total = int(payload.get("recordsTotal") or payload.get("recordsFiltered") or 0)
        collected.extend(rows)
        print(f"    start={start} alınan={len(rows)} toplam={total} biriken={len(collected)}")
        if not rows:
            break
        start += BATCH_SIZE
        draw += 1
        if total and start >= total:
            break
        time.sleep(DELAY_SEC)
    return collected


def parse_okul_adi(raw: str) -> Tuple[str, str, str]:
    """'İL - İLÇE - AD' → (il, ilce, ad)."""
    text = strip_html(raw)
    parts = [p.strip() for p in text.split(" - ") if p.strip()]
    if len(parts) >= 3:
        return parts[0], parts[1], " - ".join(parts[2:])
    if len(parts) == 2:
        return parts[0], "", parts[1]
    return "", "", text


def infer_tur(ad: str) -> str:
    folded = fold_tr(ad).replace("ı", "i")
    padded = f" {folded} "
    for pattern, label in TUR_PATTERNS:
        needle = pattern.replace("ı", "i")
        if needle.startswith(" ") or needle.endswith(" "):
            if needle in padded:
                return label
        elif needle in folded:
            return label
    return "Diğer"


class AdresLookup:
    """turkiye_adres.json → il/ilçe adı ve kodu eşlemesi."""

    def __init__(self, data: Dict[str, Any]) -> None:
        self.il_by_name: Dict[str, Tuple[str, str]] = {}
        self.ilce_by_il_name: Dict[str, Dict[str, Tuple[str, str]]] = {}
        self.unmatched_il = 0
        self.unmatched_ilce = 0

        for il in data.get("iller", []):
            il_kod = str(il["kod"])
            il_ad = il["ad"]
            self._register_il(il_ad, il_kod, il_ad)
            ilce_local: Dict[str, Tuple[str, str]] = {}
            for ilce in il.get("ilceler", []):
                ilce_kod = str(ilce["kod"])
                ilce_ad = ilce["ad"]
                ilce_local[fold_tr(ilce_ad)] = (ilce_kod, ilce_ad)
                ilce_local[fold_ascii(ilce_ad)] = (ilce_kod, ilce_ad)
            self.ilce_by_il_name[il_kod] = ilce_local

    def _register_il(self, name: str, il_kod: str, il_ad: str) -> None:
        self.il_by_name[fold_tr(name)] = (il_kod, il_ad)
        self.il_by_name[fold_ascii(name)] = (il_kod, il_ad)

    def resolve_il(self, name: str) -> Tuple[str, str]:
        folded = fold_tr(name)
        ascii_name = fold_ascii(name)
        if folded in ("bakanlık", "bakanlik") or ascii_name == "bakanlik":
            return BAKANLIK_IL_KOD, "Bakanlık"
        alias = IL_ALIASES.get(folded) or IL_ALIASES.get(ascii_name)
        if alias:
            hit = self.il_by_name.get(fold_tr(alias)) or self.il_by_name.get(fold_ascii(alias))
            if hit:
                return hit
        if folded in self.il_by_name:
            return self.il_by_name[folded]
        if ascii_name in self.il_by_name:
            return self.il_by_name[ascii_name]
        for key, value in self.il_by_name.items():
            if fold_ascii(key) == ascii_name:
                return value
        self.unmatched_il += 1
        canonical = title_tr(name)
        return BAKANLIK_IL_KOD if canonical == "Bakanlık" else "0", canonical

    def resolve_ilce(self, il_kod: str, name: str) -> Tuple[str, str]:
        if il_kod == BAKANLIK_IL_KOD:
            label = name.strip() or "Merkez"
            return "0", title_tr(label)

        if not name:
            name = "Merkez"
        ascii_name = fold_ascii(name)
        alias = ILCE_ALIASES.get(ascii_name)
        if alias:
            name = alias
            ascii_name = fold_ascii(alias)

        local = self.ilce_by_il_name.get(il_kod, {})
        folded = fold_tr(name)
        if folded in local:
            return local[folded]
        if ascii_name in local:
            return local[ascii_name]
        compact = re.sub(r"\s+", " ", folded)
        for key, value in local.items():
            if re.sub(r"\s+", " ", key) == compact:
                return value
            if fold_ascii(key) == ascii_name:
                return value
        self.unmatched_ilce += 1
        return "0", title_tr(name)


def load_adres_lookup() -> AdresLookup:
    data = json.loads(ADRES_PATH.read_text(encoding="utf-8"))
    return AdresLookup(data)


def kurum_from_row(
    row: Dict[str, Any],
    fallback_il: str,
    adres: AdresLookup,
) -> Tuple[str, str, str, str, Dict[str, str]]:
    okul_adi = row.get("OKUL_ADI") or ""
    parsed_il, parsed_ilce, ad = parse_okul_adi(str(okul_adi))
    il_kod, il_ad = adres.resolve_il(parsed_il or fallback_il)
    ilce_kod, ilce_ad = adres.resolve_ilce(il_kod, parsed_ilce)
    yol = str(row.get("YOL") or "").strip().strip("/")
    kurum_kodu = yol.split("/")[-1] if yol else ""
    host = str(row.get("HOST") or "").strip()
    item: Dict[str, str] = {
        "ad": ad or strip_html(str(okul_adi)),
        "tur": infer_tur(ad or str(okul_adi)),
    }
    if kurum_kodu:
        item["kurum_kodu"] = kurum_kodu
    if host:
        item["web"] = f"https://{host}.meb.k12.tr/"
    return il_kod, il_ad, ilce_kod, ilce_ad, item


def sort_iller(
    iller: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    ordered: Dict[str, Dict[str, Any]] = {}

    def il_sort_key(kod: str) -> Tuple[int, str]:
        if kod == BAKANLIK_IL_KOD:
            return (2, kod)
        try:
            return (0, f"{int(kod):05d}")
        except ValueError:
            return (1, kod)

    def ilce_sort_key(kod: str) -> Tuple[int, str]:
        try:
            return (0, f"{int(kod):06d}")
        except ValueError:
            return (1, kod)

    for il_kod in sorted(iller.keys(), key=il_sort_key):
        il_node = iller[il_kod]
        ilce_ordered: Dict[str, Dict[str, Any]] = {}
        for ilce_kod in sorted(il_node["ilceler"].keys(), key=ilce_sort_key):
            ilce_node = il_node["ilceler"][ilce_kod]
            kurumlar = sorted(ilce_node["kurumlar"], key=lambda k: fold_tr(k.get("ad", "")))
            ilce_ordered[ilce_kod] = {"ad": ilce_node["ad"], "kurumlar": kurumlar}
        ordered[il_kod] = {"ad": il_node["ad"], "ilceler": ilce_ordered}
    return ordered


def fetch_index_html() -> str:
    raw = request_with_retry(INDEX_URL)
    return raw.decode("utf-8", errors="replace")


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="MEB okul/kurum listesini docs/data/okullar.json olarak üretir")
    parser.add_argument("--il", help="Yalnızca bu il kodu (ör. 1 veya 34)")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args(list(argv) if argv is not None else None)

    print("İl listesi alınıyor…")
    try:
        index_html = fetch_index_html()
        iller = parse_iller_from_index(index_html)
    except Exception as exc:
        print(f"  [WARN] index.php okunamadı ({exc}); plaka listesi kullanılacak", file=sys.stderr)
        iller = []

    if not iller:
        iller = fallback_iller()
        print(f"  yedek il listesi: {len(iller)}")
    else:
        print(f"  {len(iller)} il bulundu")

    if args.il:
        wanted = str(args.il).strip()
        iller = [pair for pair in iller if pair[0] == wanted or fold_tr(pair[1]) == fold_tr(wanted)]
        if not iller:
            print(f"İl bulunamadı: {args.il}", file=sys.stderr)
            return 1

    adres = load_adres_lookup()
    hierarchy: Dict[str, Dict[str, Any]] = {}
    seen: set[Tuple[str, str, str, str]] = set()
    count = 0

    for i, (kod, ad) in enumerate(iller, start=1):
        print(f"[{i}/{len(iller)}] {ad} (kod={kod})")
        try:
            rows = fetch_il_rows(kod)
        except Exception as exc:
            print(f"  [HATA] {ad}: {exc}", file=sys.stderr)
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            il_kod, il_ad, ilce_kod, ilce_ad, item = kurum_from_row(
                row, fallback_il=ad, adres=adres
            )
            key = (il_kod, ilce_kod, item.get("kurum_kodu", ""), item.get("ad", ""))
            if key in seen:
                continue
            seen.add(key)
            il_node = hierarchy.setdefault(il_kod, {"ad": il_ad, "ilceler": {}})
            il_node["ad"] = il_ad
            ilce_node = il_node["ilceler"].setdefault(
                ilce_kod, {"ad": ilce_ad, "kurumlar": []}
            )
            ilce_node["ad"] = ilce_ad
            ilce_node["kurumlar"].append(item)
            count += 1
        time.sleep(DELAY_SEC)

    if adres.unmatched_il or adres.unmatched_ilce:
        print(
            f"  [UYARI] eşleşmeyen il: {adres.unmatched_il}, ilçe: {adres.unmatched_ilce}",
            file=sys.stderr,
        )

    payload = {
        "kaynak": INDEX_URL,
        "referans": REF_TURKIYE_ADRES,
        "guncelleme": date.today().isoformat(),
        "sayi": count,
        "iller": sort_iller(hierarchy),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Yazıldı: {args.output} ({count} kurum, {len(payload['iller'])} il)")
    from sync_site_data import sync

    sync()
    return 0 if count else 1


if __name__ == "__main__":
    sys.exit(main())
