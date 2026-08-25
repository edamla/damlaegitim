#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MEB okul siteleri (hakkinda + iletisim + teskilat) → docs/data/okullar_detay.json"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import shutil
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from data_paths import CANONICAL, REF_OKULLAR

ROOT = Path(__file__).resolve().parents[1]
OKULLAR_PATH = CANONICAL["okullar"]
OUTPUT_PATH = CANONICAL["okullar_detay"]

KAYNAK = "meb.k12.tr/tema/okulumuz_hakkinda.php+iletisim.php+teskilat.php"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DELAY_SEC = 0.3
MAX_RETRIES = 4
RETRY_BACKOFF = 2.0
CHECKPOINT_EVERY = 100
HTTP_TIMEOUT = 25

PLACEHOLDER_VALUES = {
    "göndermek için tıklayınız",
    "e-posta göndermek için tıklayın",
    "eposta göndermek için tıklayınız",
    "yazdır",
    "-",
    "–",
    "—",
}

SKIP_ALAN_LABELS = {"yazdır", "web", "e-posta göndermek için tıklayın"}

EXCLUDE_ALAN_LABELS = {
    "vizyon",
    "misyon",
    "başarılar",
    "basarilar",
    "saatler",
    "yerleşim yeri",
    "yerlesim yeri",
    "il/ilçe merkezine uzaklık",
    "il/ilce merkezine uzaklik",
    "ulaşım",
    "ulasim",
    "servis",
    "servis bilgisi",
    "pansiyon",
    "pansiyon bilgileri",
    "ısınma",
    "isinma",
}

CORE_STATS = ("derslik_sayisi", "ogretmen_sayisi", "ogrenci_sayisi")

CANONICAL_LABELS = {
    "derslik sayısı": "derslik_sayisi",
    "derslik": "derslik_sayisi",
    "öğretmen sayısı": "ogretmen_sayisi",
    "ogretmen sayısı": "ogretmen_sayisi",
    "öğretmen": "ogretmen_sayisi",
    "ogretmen": "ogretmen_sayisi",
    "öğrenci sayısı": "ogrenci_sayisi",
    "ogrenci sayısı": "ogrenci_sayisi",
    "öğrenci": "ogrenci_sayisi",
    "ogrenci": "ogrenci_sayisi",
    "telefon": "telefon",
    "belgegeçer": "belgegecer",
    "belgegecer": "belgegecer",
    "fax": "belgegecer",
    "adres": "adres",
    "e-posta": "eposta",
    "eposta": "eposta",
    "e posta": "eposta",
    "ulaşım": "ulasim",
    "ulasim": "ulasim",
}

TEMA_RE = re.compile(r"/tema/tema/(\d+)/", re.I)
SCRIPT_RE = re.compile(r"(?is)<(script|style)[^>]*>.*?</\1>")
COMMENT_RE = re.compile(r"(?is)<!--.*?-->")
TAG_RE = re.compile(r"<[^>]+>")
SPAN_STAT_RE = re.compile(
    r"<span[^>]*>\s*([^<]+?)\s*</span>\s*([^<]*)",
    re.I,
)
TR_RE = re.compile(r"(?is)<tr[^>]*>(.*?)</tr>")
CELL_RE = re.compile(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>")
BOOTSTRAP_ROW_RE = re.compile(
    r'(?is)col-xs-3[^>]*>\s*([^<]+?)\s*</div>\s*'
    r'<div class="col-(?:sm-8|xs-7)[^"]*"[^>]*>(.*?)</div>'
)
SEVIYE_UL_RE = re.compile(r"(?is)<ul[^>]*\bid=['\"]seviye(\d+)['\"][^>]*>(.*?)</ul>")
ANCHOR_RE = re.compile(r"(?is)<a\s([^>]+)>(.*?)</a>")
ATTR_RE = re.compile(r"""(\w+)\s*=\s*['"]([^'"]*)['"]""")
MAPS_Q_RE = re.compile(
    r"(?:google\.com/maps[^\"'\s<>]*[?&]q=|maps/embed/v1/place\?q=)"
    r"([+-]?\d{1,3}\.\d+)\s*,\s*([+-]?\d{1,3}\.\d+)",
    re.I,
)
LATLNG_JS_RE = re.compile(
    r"LatLng\s*\(\s*([+-]?\d+\.\d+)\s*,\s*([+-]?\d+\.\d+)\s*\)",
    re.I,
)
AT_COORD_RE = re.compile(r"@([+-]?\d{1,3}\.\d+),([+-]?\d{1,3}\.\d+)")
LL_COORD_RE = re.compile(r"[?&]ll=([+-]?\d+\.\d+),([+-]?\d+\.\d+)", re.I)
DATA_LAT_RE = re.compile(r'data-lat=["\']([+-]?\d+\.\d+)["\']', re.I)
DATA_LNG_RE = re.compile(r'data-l(?:ng|on)=["\']([+-]?\d+\.\d+)["\']', re.I)
MASKED_DOTS_RE = re.compile(r"\.\.")
UNVAN_SPLIT_RE = re.compile(
    r"(?i)(.+?)\s*(okul\s*müdürü|müdür\s*başyardımcısı|müdür\s*yardımcısı|müdür)\s*$"
)
SPAN_UNVAN_RE = re.compile(r"(?is)<span[^>]*>(.*?)(?:</span>|$)")
STRONG_RE = re.compile(
    r"(?is)<strong>\s*([^<]+?)\s*</strong>\s*:\s*(.*?)(?=<br\s*/?>|</div>|<strong>|$)"
)
DASH_CONTACT_RE = re.compile(
    r"(?is)(?:<i[^>]*>\s*</i>\s*)?"
    r"(Telefon|Belgegeçer|Belgegecer|Adres|Ulaşım|Ulasim|WEB|Yerleşim Yeri|Eposta|E-Posta)"
    r"\s*[-–]\s*([^<]*)"
)
ICON_LABEL_RE = re.compile(
    r"(?is)<i[^>]*>\s*</i>\s*"
    r"(Telefon|Belgegeçer|Belgegecer|Adres|Ulaşım|Ulasim)\s+"
    r"([^<]+)"
)
PHONE_ICON_RE = re.compile(
    r'(?is)<i[^>]*\bfa-phone\b[^>]*>\s*</i>\s*([^<]{3,})'
)
FAX_ICON_RE = re.compile(
    r'(?is)<i[^>]*\bfa-fax\b[^>]*>\s*</i>\s*([^<]{1,})'
)
STRONG_BR_RE = re.compile(
    r"(?is)<strong>\s*(Adres|Telefon|Belgegeçer|Belgegecer)[:\s]*</strong>"
    r"\s*(?:<br\s*/?>\s*)*(.*?)(?=<hr|<strong>|</p>|<div|$)"
)
ULASIM_IN_ADRES_RE = re.compile(
    r"(?i)(?:hizmet\s+binas[ıi]na\s+ula[sş][iı]m|(?:^|(?:<br\s*/?>)|\s)ula[sş][iı]m)"
    r"\s*(?:[:：]|[-–>]{2,})\s*"
)
LEADING_ARROW_RE = re.compile(r"^(?:-+\s*>+|-+>|/+>|>)+\s*")
EPOSTA_HREF_RE = re.compile(r'(?i)href=["\']([^"\']*eposta_gonder\.php[^"\']*)["\']')
MAILTO_RE = re.compile(r'(?i)mailto:([^"\'\s>?]+)')
HOMEPAGE_STAT_RE = re.compile(
    r"(?is)(Derslik Sayısı|Öğretmen Sayısı|Öğrenci Sayısı)\s*(?:</[^>]+>\s*){0,6}"
    r"(?:<[^>]+>\s*){0,6}:?\s*(?:</[^>]+>\s*){0,6}(?:<[^>]+>\s*){0,6}(\d+|-)"
)
HOMEPAGE_CARD_RE = re.compile(
    r"(?is)(Derslik Sayısı|Öğretmen Sayısı|Öğrenci Sayısı)\s*</[^>]+>\s*"
    r"(?:<[^>]+>\s*)*(\d+)"
)
WS_RE = re.compile(r"\s+")
INT_PLAIN_RE = re.compile(r"^\d+$")
INT_THOUSANDS_RE = re.compile(r"^\d{1,3}(?:\.\d{3})+$")


def fold_label(text: str) -> str:
    t = html_lib.unescape(text or "")
    t = t.replace("İ", "i").replace("I", "ı")
    t = t.casefold()
    t = t.replace("î", "i")
    return WS_RE.sub(" ", t).strip(" :-\t\n\r")


def normalize_ws(text: str) -> str:
    t = html_lib.unescape(text or "")
    t = t.replace("\xa0", " ").replace("&nbsp;", " ")
    return WS_RE.sub(" ", t).strip()


def strip_html(text: str) -> str:
    t = SCRIPT_RE.sub(" ", text or "")
    t = TAG_RE.sub(" ", t)
    return normalize_ws(t)


def clean_label(text: str) -> str:
    t = strip_html(text)
    return t.strip(" :-\t")


def is_placeholder(value: str) -> bool:
    folded = fold_label(value)
    if not folded:
        return True
    if folded in PLACEHOLDER_VALUES:
        return True
    if "tıklayınız" in folded or "tiklayiniz" in folded:
        return True
    return False


def parse_int(value: str) -> Optional[int]:
    v = normalize_ws(value).replace(" ", "")
    if not v or is_placeholder(v):
        return None
    if INT_PLAIN_RE.match(v):
        return int(v)
    if INT_THOUSANDS_RE.match(v):
        return int(v.replace(".", ""))
    return None


def clean_phone(value: str) -> Optional[str]:
    v = normalize_ws(value)
    if is_placeholder(v):
        return None
    v = re.sub(r"-{2,}$", "", v).strip(" -")
    if not v or v == "0":
        return None
    if not re.search(r"\d", v):
        return None
    return v


def looks_like_email(value: str) -> bool:
    return bool(re.search(r"[^@\s]+@[^@\s]+\.[^@\s]+", value or ""))


def normalize_alan_label(label: str) -> str:
    folded = fold_label(label)
    return re.sub(r"\s*/\s*", "/", folded)


def is_excluded_alan(label: str) -> bool:
    folded = normalize_alan_label(label)
    return folded in SKIP_ALAN_LABELS or folded in EXCLUDE_ALAN_LABELS


def extract_email_from_html(html: str) -> Optional[str]:
    for m in MAILTO_RE.finditer(html or ""):
        cand = html_lib.unescape(m.group(1).strip())
        if looks_like_email(cand):
            return cand
    return None


def detect_sablon(html: str) -> str:
    nums = TEMA_RE.findall(html or "")
    if nums:
        # En sık geçen tema numarası (asset yolu)
        counts: Dict[str, int] = {}
        for n in nums:
            counts[n] = counts.get(n, 0) + 1
        best = max(counts, key=lambda k: counts[k])
        return f"tema-{best}"
    return "bilinmiyor"


def join_url(web: str, path: str) -> str:
    base = (web or "").strip()
    if not base:
        return path
    if not base.endswith("/"):
        base += "/"
    return urllib.parse.urljoin(base, path.lstrip("/"))


def clean_field_value(value: str) -> str:
    return LEADING_ARROW_RE.sub("", normalize_ws(value)).strip()


def split_adres_ulasim(value: str) -> Tuple[str, Optional[str]]:
    m = ULASIM_IN_ADRES_RE.search(value or "")
    if not m:
        return value, None
    left = clean_field_value(value[: m.start()]).rstrip(" -–>")
    right = clean_field_value(value[m.end() :])
    return left, right or None


def add_pair(pairs: List[Tuple[str, str]], label: str, value: str) -> None:
    lab = clean_label(label)
    val = strip_html(value) if "<" in (value or "") else normalize_ws(value)
    if not lab or is_placeholder(lab):
        return
    if is_excluded_alan(lab):
        return
    if is_placeholder(val):
        return
    if not val:
        return
    pairs.append((lab, val))


def extract_pairs(html: str) -> Tuple[List[Tuple[str, str]], Optional[str]]:
    html = COMMENT_RE.sub(" ", html or "")
    pairs: List[Tuple[str, str]] = []
    page_eposta = extract_email_from_html(html)

    for m in SPAN_STAT_RE.finditer(html or ""):
        add_pair(pairs, m.group(1), m.group(2))

    for tr in TR_RE.finditer(html or ""):
        cells = [c for c in CELL_RE.findall(tr.group(1))]
        texts = [strip_html(c) for c in cells]
        if len(texts) >= 3 and texts[1] in (":", "："):
            add_pair(pairs, texts[0], texts[2])
        elif len(texts) >= 3:
            add_pair(pairs, texts[1], texts[2])
        elif len(texts) == 2:
            add_pair(pairs, texts[0], texts[1])

    for m in BOOTSTRAP_ROW_RE.finditer(html or ""):
        add_pair(pairs, m.group(1), m.group(2))

    for m in STRONG_RE.finditer(html or ""):
        add_pair(pairs, m.group(1), m.group(2))

    for m in DASH_CONTACT_RE.finditer(html or ""):
        add_pair(pairs, m.group(1), m.group(2))
    for m in ICON_LABEL_RE.finditer(html or ""):
        add_pair(pairs, m.group(1), m.group(2))
    for m in PHONE_ICON_RE.finditer(html or ""):
        add_pair(pairs, "Telefon", m.group(1))
    for m in FAX_ICON_RE.finditer(html or ""):
        add_pair(pairs, "Belgegeçer", m.group(1))
    for m in STRONG_BR_RE.finditer(html or ""):
        add_pair(pairs, m.group(1), m.group(2))

    for m in HOMEPAGE_STAT_RE.finditer(html or ""):
        add_pair(pairs, m.group(1), m.group(2))
    for m in HOMEPAGE_CARD_RE.finditer(html or ""):
        add_pair(pairs, m.group(1), m.group(2))

    return pairs, page_eposta


def apply_pairs(
    item: Dict[str, Any],
    pairs: List[Tuple[str, str]],
    page_eposta: Optional[str] = None,
) -> None:
    alanlar: Dict[str, str] = dict(item.get("alanlar") or {})
    seen_canon: set[str] = set()

    for label, value in pairs:
        key = CANONICAL_LABELS.get(fold_label(label))
        if key == "derslik_sayisi" or key == "ogretmen_sayisi" or key == "ogrenci_sayisi":
            if item.get(key) is not None:
                seen_canon.add(key)
                continue
            num = parse_int(value)
            if num is not None:
                item[key] = num
                seen_canon.add(key)
            continue
        if key == "telefon":
            phone = clean_phone(value)
            if phone and item.get("telefon") is None:
                item["telefon"] = phone
            continue
        if key == "belgegecer":
            fax = clean_phone(value)
            if fax and item.get("belgegecer") is None:
                item["belgegecer"] = fax
            continue
        if key == "adres":
            adres_part, _ = split_adres_ulasim(value)
            adres_part = clean_field_value(adres_part)
            if adres_part and item.get("adres") is None:
                item["adres"] = adres_part
            continue
        if key == "ulasim":
            continue
        if key == "eposta":
            if looks_like_email(value) and item.get("eposta") is None:
                item["eposta"] = value
            continue
        if is_excluded_alan(label):
            continue
        if label not in alanlar:
            alanlar[label] = value

    if page_eposta and looks_like_email(page_eposta) and item.get("eposta") is None:
        item["eposta"] = page_eposta
    if alanlar:
        item["alanlar"] = alanlar


def prune_item(item: Dict[str, Any]) -> None:
    item.pop("eposta_link", None)
    item.pop("ulasim", None)
    eposta = item.get("eposta")
    if eposta is not None and not looks_like_email(str(eposta)):
        item.pop("eposta", None)
    alanlar = item.get("alanlar")
    if isinstance(alanlar, dict):
        pruned = {k: v for k, v in alanlar.items() if not is_excluded_alan(k)}
        if pruned:
            item["alanlar"] = pruned
        else:
            item.pop("alanlar", None)


def has_core_stats(item: Dict[str, Any]) -> bool:
    return any(item.get(k) is not None for k in CORE_STATS)


def _valid_coord(lat: float, lng: float) -> bool:
    return 35.0 <= lat <= 43.5 and 25.0 <= lng <= 45.5


def extract_geo(html: str) -> Tuple[Optional[float], Optional[float]]:
    text = html_lib.unescape(html or "")
    for rx in (MAPS_Q_RE, LATLNG_JS_RE, AT_COORD_RE, LL_COORD_RE):
        m = rx.search(text)
        if not m:
            continue
        try:
            lat, lng = float(m.group(1)), float(m.group(2))
        except ValueError:
            continue
        if _valid_coord(lat, lng):
            return lat, lng
    mlat, mlng = DATA_LAT_RE.search(text), DATA_LNG_RE.search(text)
    if mlat and mlng:
        try:
            lat, lng = float(mlat.group(1)), float(mlng.group(1))
        except ValueError:
            return None, None
        if _valid_coord(lat, lng):
            return lat, lng
    return None, None


def apply_geo(item: Dict[str, Any], html: str) -> None:
    if item.get("enlem") is not None and item.get("boylam") is not None:
        return
    lat, lng = extract_geo(html)
    if lat is None or lng is None:
        return
    item["enlem"] = lat
    item["boylam"] = lng
    item["harita_url"] = f"https://www.google.com/maps?q={lat},{lng}"


def is_masked_name(ad: str) -> bool:
    text = normalize_ws(ad)
    if not text or text in (".", "..", "..."):
        return True
    return len(MASKED_DOTS_RE.findall(text)) >= 2


def is_principal_unvan(unvan: str) -> bool:
    folded = fold_label(unvan)
    if not folded:
        return False
    if "yard" in folded or "başyard" in folded or "basyard" in folded:
        return False
    return "müdür" in folded or "mudur" in folded


def split_ad_unvan(ad: str, unvan: str) -> Tuple[str, str]:
    name = normalize_ws(ad)
    title = normalize_ws(unvan)
    if title:
        if name and fold_label(name).endswith(fold_label(title)):
            name = name[: max(0, len(name) - len(title))].strip()
        return name, title
    m = UNVAN_SPLIT_RE.search(name)
    if not m or len(normalize_ws(m.group(1))) < 3:
        return name, title
    return normalize_ws(m.group(1)), normalize_ws(m.group(2))


def parse_kadro(html: str) -> List[Dict[str, Any]]:
    people: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str, int]] = set()
    for um in SEVIYE_UL_RE.finditer(html or ""):
        try:
            seviye = int(um.group(1))
        except ValueError:
            seviye = 0
        block = um.group(2)
        for am in ANCHOR_RE.finditer(block):
            attrs = {k.lower(): v for k, v in ATTR_RE.findall(am.group(1))}
            href = html_lib.unescape(attrs.get("href") or "")
            if "idari_personel" not in href.lower() and "idari-personel" not in href.lower():
                # yine de title+metin varsa al (bazı temalar farklı path)
                if not attrs.get("title"):
                    continue
            unvan = normalize_ws(attrs.get("title") or attrs.get("alt") or "")
            inner = am.group(2)
            sm = SPAN_UNVAN_RE.search(inner)
            if sm:
                span_unvan = strip_html(sm.group(1))
                if span_unvan and not unvan:
                    unvan = span_unvan
                inner = inner[: sm.start()]
            ad = strip_html(inner)
            ad, unvan = split_ad_unvan(ad, unvan)
            if ad in (".", "-", "–", "—"):
                ad = ""
            tel = None
            mail = None
            raw_inner = am.group(2) + " " + am.group(1)
            mail_m = EPOSTA_HREF_RE.search(raw_inner) or (
                re.search(r"mailto:([^\"'\s>]+)", raw_inner, re.I)
            )
            if mail_m:
                cand = html_lib.unescape(mail_m.group(1))
                if looks_like_email(cand):
                    mail = cand
            tel_m = re.search(r"(?:tel:|telefon)[^0-9]*([0-9\s\-+/()]{7,})", raw_inner, re.I)
            if tel_m:
                tel = clean_phone(tel_m.group(1))
            if not ad:
                continue
            masked = is_masked_name(ad)
            extra = bool(unvan or tel or mail)
            if masked and not extra:
                continue
            row: Dict[str, Any] = {}
            if ad:
                row["ad"] = ad
            if unvan:
                row["unvan"] = unvan
            if seviye:
                row["seviye"] = seviye
            if tel:
                row["telefon"] = tel
            if mail:
                row["eposta"] = mail
            key = (row.get("ad") or "", row.get("unvan") or "", seviye)
            if key in seen:
                continue
            seen.add(key)
            people.append(row)
    return people


def apply_teskilat(item: Dict[str, Any], html: str) -> None:
    kadro = parse_kadro(html)
    if kadro:
        item["kadro"] = kadro
    mudur = None
    for row in kadro:
        ad = row.get("ad") or ""
        if is_masked_name(ad):
            continue
        if is_principal_unvan(row.get("unvan") or ""):
            mudur = ad
            break
    if not mudur:
        for row in kadro:
            ad = row.get("ad") or ""
            if ad and not is_masked_name(ad):
                mudur = ad
                break
    if mudur:
        item["mudur"] = mudur


def try_fetch(url: str) -> Tuple[Optional[str], str]:
    """HTML veya (None, durum) — yok/hata."""
    try:
        return request_with_retry(url), "ok"
    except FetchError as exc:
        return None, "yok" if "404" in str(exc) else "hata"


def enrich_from_extra_pages(item: Dict[str, Any], web: str) -> None:
    iletisim_html, iletisim_durum = try_fetch(join_url(web, "tema/iletisim.php"))
    item["iletisim_durum"] = "ok" if iletisim_html else iletisim_durum
    if iletisim_html:
        pairs, page_eposta = extract_pairs(iletisim_html)
        apply_pairs(item, pairs, page_eposta)
        apply_geo(item, iletisim_html)
        if item.get("sablon") == "bilinmiyor":
            item["sablon"] = detect_sablon(iletisim_html)

    if item.get("enlem") is None:
        harita_html, _ = try_fetch(join_url(web, "tema/harita.php"))
        if harita_html:
            apply_geo(item, harita_html)

    teskilat_html, _ = try_fetch(join_url(web, "tema/teskilat.php"))
    if teskilat_html:
        apply_teskilat(item, teskilat_html)


def parse_page(html: str, web: str, kurum_kodu: str) -> Dict[str, Any]:
    item: Dict[str, Any] = {
        "kurum_kodu": kurum_kodu,
        "web": web,
        "sablon": detect_sablon(html),
    }
    pairs, page_eposta = extract_pairs(html)
    apply_pairs(item, pairs, page_eposta)
    return item


def _peer_cert(resp: Any) -> Optional[Dict[str, Any]]:
    try:
        sock = resp.fp.raw._sock  # http.client.HTTPResponse → SSLSocket
        if hasattr(sock, "getpeercert"):
            cert = sock.getpeercert()
            return cert if isinstance(cert, dict) else None
    except Exception:
        return None
    return None


def _dns_names(cert: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    for typ, val in cert.get("subjectAltName") or ():
        if str(typ).lower() == "dns" and val:
            names.append(str(val).lower().rstrip("."))
    if names:
        return names
    for rdn in cert.get("subject") or ():
        for key, val in rdn:
            if key == "commonName" and val:
                names.append(str(val).lower().rstrip("."))
    return names


def assert_cert_hostname(cert: Dict[str, Any], hostname: str) -> None:
    """Joker SAN eşlemesi; OpenSSL'in reddettiği '_' karakterine izin verir."""
    host = (hostname or "").lower().rstrip(".")
    names = _dns_names(cert)
    for name in names:
        if name == host:
            return
        if name.startswith("*.") and host.endswith(name[1:]):
            left = host[: -len(name[1:])]
            if left and "." not in left:
                return
    raise ssl.SSLCertVerificationError(
        f"hostname mismatch: {hostname!r} vs {names}"
    )


def ssl_context_for_host(hostname: str) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    # OpenSSL X509_check_host, DNS host adında '_' görünce joker *.meb.k12.tr
    # eşlemesini de reddeder. Tarayıcılar aynı sertifikayı kabul eder.
    if "_" in (hostname or ""):
        ctx.check_hostname = False
    return ctx


def http_get(url: str, timeout: int = HTTP_TIMEOUT) -> Tuple[int, str]:
    req_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    }
    host = urllib.parse.urlparse(url).hostname or ""
    ctx = ssl_context_for_host(host)
    req = urllib.request.Request(url, headers=req_headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            if "_" in host:
                cert = _peer_cert(resp)
                if cert:
                    assert_cert_hostname(cert, host)
            raw = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            html = raw.decode(charset, errors="replace")
            return int(resp.status), html
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            raw = exc.read()
            body = raw.decode("utf-8", errors="replace") if raw else ""
        except Exception:
            body = ""
        return int(exc.code), body


class FetchError(Exception):
    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


def request_with_retry(url: str) -> str:
    last_err: Optional[BaseException] = None
    last_kind = "http_hata"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            status, html = http_get(url)
            if status == 404:
                raise FetchError("http_hata", f"HTTP 404 {url}")
            if status >= 400:
                raise urllib.error.URLError(f"HTTP {status}")
            return html
        except FetchError:
            raise
        except urllib.error.HTTPError as exc:
            last_err = exc
            last_kind = "http_hata"
            if exc.code == 404:
                raise FetchError("http_hata", f"HTTP 404 {url}") from exc
        except TimeoutError as exc:
            last_err = exc
            last_kind = "zaman_asimi"
        except (urllib.error.URLError, ssl.SSLError, ConnectionError, OSError) as exc:
            last_err = exc
            reason = str(exc).lower()
            last_kind = "zaman_asimi" if "timed out" in reason or "timeout" in reason else "http_hata"
        wait = RETRY_BACKOFF * attempt
        print(
            f"  [WARN] {url} ({attempt}/{MAX_RETRIES}): {last_err}; {wait:.1f}s",
            file=sys.stderr,
        )
        time.sleep(wait)
    raise FetchError(last_kind, f"İstek başarısız: {url}: {last_err}") from last_err


def iter_kurumlar(
    data: Dict[str, Any],
    il_filter: Optional[str] = None,
    kod_filter: Optional[str] = None,
) -> List[Tuple[str, str, str]]:
    out: List[Tuple[str, str, str]] = []
    wanted_il = str(il_filter).strip() if il_filter else None
    wanted_kod = str(kod_filter).strip() if kod_filter else None
    iller = data.get("iller") or {}
    for il_kod, il_node in iller.items():
        if wanted_il and str(il_kod) != wanted_il:
            continue
        if not isinstance(il_node, dict):
            continue
        for ilce_node in (il_node.get("ilceler") or {}).values():
            if not isinstance(ilce_node, dict):
                continue
            for kurum in ilce_node.get("kurumlar") or []:
                if not isinstance(kurum, dict):
                    continue
                kod = str(kurum.get("kurum_kodu") or "").strip()
                web = str(kurum.get("web") or "").strip()
                if not kod or not web:
                    continue
                if wanted_kod and kod != wanted_kod:
                    continue
                out.append((kod, web, str(il_kod)))
    return out


def empty_payload() -> Dict[str, Any]:
    return {
        "kaynak": KAYNAK,
        "referans": REF_OKULLAR,
        "guncelleme": date.today().isoformat(),
        "sayi": 0,
        "kurumlar": {},
    }


def load_existing(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return empty_payload()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  [WARN] mevcut dosya okunamadı ({exc}); sıfırdan başlanacak", file=sys.stderr)
        return empty_payload()
    if not isinstance(data, dict):
        return empty_payload()
    kurumlar = data.get("kurumlar")
    if not isinstance(kurumlar, dict):
        data["kurumlar"] = {}
    return data


def write_payload(path: Path, payload: Dict[str, Any]) -> None:
    kurumlar = payload.get("kurumlar") or {}
    payload["kaynak"] = KAYNAK
    payload["referans"] = REF_OKULLAR
    payload["guncelleme"] = date.today().isoformat()
    payload["sayi"] = len(kurumlar)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    content = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    last_err: Optional[BaseException] = None
    for attempt in range(1, 8):
        try:
            tmp.replace(path)
            return
        except PermissionError as exc:
            last_err = exc
            time.sleep(0.5 * attempt)
    for attempt in range(1, 4):
        try:
            shutil.copy2(tmp, path)
            tmp.unlink(missing_ok=True)
            return
        except (PermissionError, OSError) as exc:
            last_err = exc
            time.sleep(1.0 * attempt)
    try:
        path.write_text(content, encoding="utf-8")
        tmp.unlink(missing_ok=True)
        return
    except PermissionError as exc:
        last_err = exc
    raise last_err  # type: ignore[misc]


def fetch_kurum(web: str, kurum_kodu: str) -> Dict[str, Any]:
    hakkinda = join_url(web, "tema/okulumuz_hakkinda.php")
    html = request_with_retry(hakkinda)
    item = parse_page(html, web, kurum_kodu)
    if not has_core_stats(item):
        home_html = request_with_retry(join_url(web, ""))
        home_item = parse_page(home_html, web, kurum_kodu)
        if item.get("sablon") == "bilinmiyor" and home_item.get("sablon"):
            item["sablon"] = home_item["sablon"]
        for key in (
            "derslik_sayisi",
            "ogretmen_sayisi",
            "ogrenci_sayisi",
            "telefon",
            "adres",
            "belgegecer",
            "eposta",
        ):
            if key not in item and home_item.get(key) is not None:
                item[key] = home_item[key]
        extra = home_item.get("alanlar") or {}
        if extra:
            apply_pairs(item, list(extra.items()), home_item.get("eposta"))
    if has_core_stats(item) or item.get("telefon") or item.get("adres") or item.get("alanlar"):
        item["durum"] = "ok"
    else:
        item["durum"] = "parse_eksik"
    enrich_from_extra_pages(item, web)
    return item


def summarize(kurumlar: Dict[str, Any]) -> str:
    durum: Dict[str, int] = {}
    sablon: Dict[str, int] = {}
    iletisim: Dict[str, int] = {}
    with_stats = 0
    with_enlem = 0
    with_mudur = 0
    with_kadro = 0
    for item in kurumlar.values():
        if not isinstance(item, dict):
            continue
        d = str(item.get("durum") or "?")
        durum[d] = durum.get(d, 0) + 1
        s = str(item.get("sablon") or "?")
        sablon[s] = sablon.get(s, 0) + 1
        if item.get("iletisim_durum"):
            idur = str(item.get("iletisim_durum"))
            iletisim[idur] = iletisim.get(idur, 0) + 1
        if has_core_stats(item):
            with_stats += 1
        if item.get("enlem") is not None:
            with_enlem += 1
        if item.get("mudur"):
            with_mudur += 1
        if item.get("kadro"):
            with_kadro += 1
    durum_s = ", ".join(f"{k}={v}" for k, v in sorted(durum.items()))
    sablon_s = ", ".join(f"{k}={v}" for k, v in sorted(sablon.items()))
    ilet_s = ", ".join(f"{k}={v}" for k, v in sorted(iletisim.items())) or "-"
    return (
        f"istatistikli={with_stats}; enlem={with_enlem}; mudur={with_mudur}; "
        f"kadro={with_kadro}; iletisim_durum: {ilet_s}; durum: {durum_s}; şablon: {sablon_s}"
    )


def reject_legacy_data_paths(*paths: Path) -> None:
    """_data/*.json Jekyll site.data'ya girer; büyük okul JSON'ları build'i kırar."""
    for path in paths:
        resolved = path.resolve()
        data_dir = (ROOT / "_data").resolve()
        try:
            resolved.relative_to(data_dir)
        except ValueError:
            continue
        raise SystemExit(
            f"Hata: {path} _data altına yazılamaz. "
            f"Kullanın: {CANONICAL['okullar_detay']} (veya --output docs/data/okullar_detay.json)"
        )


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="MEB okul sitelerinden detay meta verisini docs/data/okullar_detay.json olarak üretir"
    )
    parser.add_argument("--okullar", type=Path, default=OKULLAR_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--il", help="Yalnızca bu il kodu (ör. 1 veya 34)")
    parser.add_argument("--kurum-kodu", help="Yalnızca bu kurum kodu")
    parser.add_argument("--limit", type=int, default=0, help="En fazla N kurum (0 = tümü)")
    parser.add_argument("--delay", type=float, default=DELAY_SEC)
    parser.add_argument(
        "--force",
        action="store_true",
        help="hakkinda + iletisim + teskilat sayfalarını baştan çek",
    )
    parser.add_argument("--no-resume", action="store_true", help="Mevcut dosyayı yok say")
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Mevcut okullar_detay.json kayıtlarından gereksiz alanları ağ çekmeden temizle",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    reject_legacy_data_paths(args.output, args.okullar)

    if args.prune:
        payload = load_existing(args.output)
        existing = payload.setdefault("kurumlar", {})
        for item in existing.values():
            if isinstance(item, dict):
                prune_item(item)
        write_payload(args.output, payload)
        print(f"Temizlendi: {args.output} ({len(existing)} kurum)")
        from sync_site_data import sync

        sync()
        return 0

    if not args.okullar.is_file():
        print(f"okullar.json yok: {args.okullar}", file=sys.stderr)
        return 1

    print(f"Okunuyor: {args.okullar}")
    okullar = json.loads(args.okullar.read_text(encoding="utf-8"))
    targets = iter_kurumlar(okullar, il_filter=args.il, kod_filter=args.kurum_kodu)
    print(f"  aday kurum: {len(targets)}")

    payload = empty_payload() if args.no_resume else load_existing(args.output)
    existing: Dict[str, Any] = payload.setdefault("kurumlar", {})

    todo: List[Tuple[str, str, str, bool]] = []
    skipped = 0
    extra_only_n = 0
    for kod, web, il_kod in targets:
        prev = existing.get(kod)
        extra_only = (
            not args.force
            and isinstance(prev, dict)
            and prev.get("durum") == "ok"
            and not prev.get("iletisim_durum")
        )
        if (
            not args.force
            and isinstance(prev, dict)
            and prev.get("durum") == "ok"
            and prev.get("iletisim_durum")
        ):
            skipped += 1
            continue
        if extra_only:
            extra_only_n += 1
        todo.append((kod, web, il_kod, extra_only))
    if args.limit and args.limit > 0:
        todo = todo[: args.limit]
        extra_only_n = sum(1 for t in todo if t[3])
    print(
        f"  atlanan (resume): {skipped}; çekilecek: {len(todo)} "
        f"(yalnızca iletisim/teskilat: {extra_only_n})"
    )

    processed = 0
    try:
        for i, (kod, web, il_kod, extra_only) in enumerate(todo, start=1):
            mode = "ek" if extra_only else "tam"
            print(f"[{i}/{len(todo)}] [{mode}] {kod} {web}")
            try:
                if extra_only:
                    item = existing.get(kod) or {
                        "kurum_kodu": kod,
                        "web": web,
                        "durum": "ok",
                    }
                    enrich_from_extra_pages(item, web)
                else:
                    item = fetch_kurum(web, kod)
            except FetchError as exc:
                item = {
                    "kurum_kodu": kod,
                    "web": web,
                    "sablon": "bilinmiyor",
                    "durum": exc.kind,
                }
                print(f"  [HATA] {exc.kind}: {exc}", file=sys.stderr)
                enrich_from_extra_pages(item, web)
            prune_item(item)
            existing[kod] = item
            processed += 1
            if processed % CHECKPOINT_EVERY == 0:
                write_payload(args.output, payload)
                print(f"  [kayıt] {args.output} ({len(existing)} kurum)")
            if i < len(todo) and args.delay > 0:
                time.sleep(args.delay)
    except KeyboardInterrupt:
        print("\nKesildi; mevcut durum yazılıyor…", file=sys.stderr)
        write_payload(args.output, payload)
        print(f"Yazıldı: {args.output} ({summarize(existing)})")
        return 130

    write_payload(args.output, payload)
    print(f"Yazıldı: {args.output} ({len(existing)} kurum)")
    print(summarize(existing))
    from sync_site_data import sync

    sync()
    return 0


if __name__ == "__main__":
    sys.exit(main())
