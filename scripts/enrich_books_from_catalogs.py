#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Katalog PDF metinlerinden _books hikaye kayıtlarını zenginleştir."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(r"c:/Git/damlaegitim")
BOOKS = ROOT / "_books"
EAN_DIR = ROOT / "assets" / "images" / "ean"
MANIFEST = ROOT / "_data" / "webp_manifest.yml"
ORTA_TXT = ROOT / "docs" / "_extract" / "ortaokul.txt"
ILK_TXT = ROOT / "docs" / "_extract" / "ilkokul.txt"
INVENTORY = ROOT / "docs" / "_extract" / "katalog-envanter.json"
REPORT = ROOT / "docs" / "_extract" / "katalog-eslesme.json"

TR = str.maketrans({
    "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "İ": "i", "I": "i",
    "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u",
    "â": "a", "Â": "a", "î": "i", "Î": "i", "û": "u", "Û": "u",
})

SKIP_IDS = {
    "9789786051741",
    "9789753814362",
    "97897538143620",
}

# Katalog ISBN/barkod → mevcut _books dosya adı (uzantısız)
ISBN_TO_SLUG = {
    "9786053836483": "etik-degerler-1",
    "9786254113215": "etkinliklerle-hacivat",
    "9786051742847": "dinozor-cagi",
    "9786053839446": "degerler-okyanusu",
    "9786051748047": "guclu-karakter",
    "869791122418": "iyilik-heryerde-serisi",
    "8697911223752": "duygularımı-kesfediyorum",
    "9786053837480": "etik-degerler-2",
    "9786053838340": "cilgin-dede-masal-makinesi",
    "9786053831303": "alicanin-gunlugu",
    "9786053831181": "erdemlerimizi-kesfedelim",
    "9786254110139": "meslek-oykuleri",
    "8697911223547": "robot-avcilari",
    "9786254112676": "hayat-bilgisi-oykuleri",
    "9786053831952": "cilgin-dede-icatlar-kesifler",
    "9786254114540": "cilgin-dede-turkiye-turu",
    "9786053832768": "atasozu-oykuleri",
    "9786053832874": "deyim-oykuleri",
    "9786254112775": "matematik-oykuleri",
    "8697911223042": "fen-oykuleri",
    "9786051745374": "engel-tanimayanlar",
    "9786053833413": "gizli-dedektiflik-burosu",
    "9786254112560": "istiklal-marsi-yazdiran-kahramanlar",
    "8697911223516": "o-bir-dahi",
    "9786053830726": "yesili-ozleyen-kiz",
    "9786254115493": "afacan-polisler-1",
    "9786254115974": "afacan-polisler-2",
    "9786254113017": "hacker-nine-1",
    "9786254115172": "hacker-nine-2",
    "9786051749600": "annemin-hikayesi",
    "9786053834458": "cilgin-dede-uygarlıklar",
    "9786053839620": "o-canavari-yakala",
    "9786053830498": "cevreci-karincalar",
    "9786051742694": "kucuk-cesur-mico-1",
    "9786051742700": "kucuk-cesur-mico-2",
    "9786254113826": "geri-donusum-holdingi",
    "9786254116469": "mucit-dede",
}

# Site barkodu → katalog ISBN-13 (ean güncellemesi)
BARCODE_TO_ISBN = {
    "8697911223851": "9786053836483",
    "8697911223875": "9786053837480",
    "8697911222991": "9786254110139",
    "8697911223028": "9786053831303",
    "8697911223004": "9786254112676",
    "8697911223066": "9786254112775",
    "8697911223080": "9786053833413",
    "8697911223974": "9786051745374",
    "8697911223943": "9786254114540",
    "8697911223530": "8697911223547",
}

TITLE_FIX = {
    "9786053836483": "Etik Değerler Eğitim Seti-1",
    "9786254113215": "Etkinliklerle Karagöz ile Hacivat",
    "9786051744155": "Cicim Masallarım",
    "9786051742847": "Dinozor Çağı (10 Kitap)",
    "9786053839446": "Değerler Okyanusu (10 Kitap)",
    "9786053839736": "Sosyal Becerilerim",
    "9786051748047": "Güçlü Karakter Serisi",
    "869791122418": "İyilik Her Yerde Serisi",
    "8697911223752": "Duygularımı Keşfediyorum",
    "9786053837480": "Etik Değerler Eğitim Seti-2",
    "9786053838340": "Çılgın Dedemin Masal Makinesi (10 Kitap)",
    "9786053831303": "Alican’ın Günlüğü",
    "9786053831181": "Erdemlerimizi Keşfedelim",
    "9786254110139": "Meslek Öyküleri (10 Kitap)",
    "8697911223547": "Robot Avcıları (10 Kitap)",
    "9786254112676": "Hayat Bilgisi Öyküleri",
    "9786053831952": "Çılgın Dedemin Zaman Makinesi-İcatlar ve Keşifler (10 Kitap)",
    "9786254114540": "Çılgın Dedemin Türkiye Turu (10 Kitap)",
    "9786053832768": "Atasözü Öyküleri (5 Kitap)",
    "9786053832874": "Deyim Öyküleri",
    "9786254113345": "Türkçe Öyküleri (10 Kitap)",
    "9786254112775": "Matematik Öyküleri (10 Kitap)",
    "8697911223042": "Fen Öyküleri",
    "9786051743134": "Derslerle Aram Çok İyi",
    "9786051745374": "Engel Tanımayanlar",
    "9786053833413": "Gizli Dedektiflik Bürosu",
    "9786254112560": "İstiklal Marşı Yazdıran Kahramanlar (10 Kitap)",
    "8697911223516": "O Bir Dahi",
    "9786051748146": "Evliya Çelebi’nin Maceraları",
    "9786053830726": "Yeşili Özleyen Kız",
    "9786254115493": "Afacan Polisler-1",
    "9786254115974": "Afacan Polisler-2",
    "9786254113017": "Hacker Nine-1",
    "9786254115172": "Hacker Nine-2",
    "9786254115004": "Uzaydaki Muz Ağacı",
    "9786254116148": "Sevimli Canavarlar Şatosu",
    "9786254115813": "Uçan Kitap",
    "9786254116131": "Penceredeki Mutluluk",
    "9786254115806": "Gizemli Sisin Peşinde",
    "9786254115103": "Kitabüs",
    "9786254113673": "İlham Piresi",
    "9786053834458": "Çılgın Dedemin Zaman Makinesi-Geçmişten Geleceğe Uygarlıklar",
    "9786053839620": "O Canavarı Yakala",
    "9786053830498": "Çevreci Karıncalar",
    "9786051742694": "Küçük Cesur Miço-1",
    "9786051742700": "Küçük Cesur Miço-2",
    "9786254113826": "Geri Dönüşüm Holdingi",
    "9786254116469": "Mucit Dede",
}

GARBAGE_TITLE = re.compile(
    r"www\.|Maarif Modeli|Bandrol|SORULARIN|ÇÖZÜMLERİ|OKUT",
    re.I,
)

THEME_STOP = {
    "ana temalar", "yazar", "isbn", "ebat", "sayfa", "sınıf", "tadımlık", "oku",
    "tadoikmulik",
}


def slugify(s: str) -> str:
    s = (s or "").translate(TR).lower()
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def yaml_scalar(value) -> str:
    if value is None or value == "":
        return '""'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    s = str(value)
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def yaml_list(items) -> str:
    if not items:
        return "[]"
    return "[" + ", ".join(yaml_scalar(x) for x in items) + "]"


def parse_fm(text: str):
    if not text.startswith("---"):
        raise ValueError("no fm")
    parts = text.split("---", 2)
    return parts[1], parts[2]


def fm_get(fm: str, key: str) -> str:
    m = re.search(rf"^{re.escape(key)}:\s*(.*)$", fm, re.M)
    return m.group(1).strip() if m else ""


def fm_set(fm: str, key: str, raw_value: str, after_key: str | None = None) -> str:
    line = f"{key}: {raw_value}"
    if re.search(rf"^{re.escape(key)}:", fm, re.M):
        return re.sub(rf"^{re.escape(key)}:.*$", line, fm, count=1, flags=re.M)
    if after_key and re.search(rf"^{re.escape(after_key)}:", fm, re.M):
        return re.sub(
            rf"^({re.escape(after_key)}:.*)$",
            rf"\1\n{line}",
            fm,
            count=1,
            flags=re.M,
        )
    return fm.rstrip() + "\n" + line + "\n"


def parse_yaml_list(raw: str):
    raw = (raw or "").strip()
    if not raw or raw == "[]":
        return []
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        out = []
        cur = ""
        in_q = False
        qch = ""
        for ch in inner:
            if ch in "\"'":
                if not in_q:
                    in_q = True
                    qch = ch
                    continue
                if ch == qch:
                    in_q = False
                    continue
            if ch == "," and not in_q:
                p = cur.strip().strip('"').strip("'")
                if p:
                    out.append(int(p) if re.fullmatch(r"-?\d+", p) else p)
                cur = ""
            else:
                cur += ch
        p = cur.strip().strip('"').strip("'")
        if p:
            out.append(int(p) if re.fullmatch(r"-?\d+", p) else p)
        return out
    return [raw.strip('"').strip("'")]


def merge_unique(primary, extra):
    seen = set()
    out = []
    for item in list(primary) + list(extra):
        if item is None:
            continue
        s = str(item).strip()
        if not s:
            continue
        key = s.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def clean_tokens(items) -> list[str]:
    out = []
    for item in items or []:
        s = clean_space(str(item))
        s = re.sub(r"\d{10,13}", "", s).strip(" -•")
        if not s or len(s) < 2 or len(s) > 80:
            continue
        if s.endswith("-") or "BASKI" in s:
            continue
        if s.casefold() in {"fe", "de", "da", "ve", "ile"}:
            continue
        if "sayfa" in s.lower() or s.startswith("Ì"):
            continue
        if s.casefold() in {"resimli sayfalar", "renkli kapak", "uygun", "kazanımlarına"}:
            continue
        out.append(s)
    return merge_unique(out, [])


def clean_space(s: str) -> str:
    s = re.sub(r"[-\u00ad]\n\s*", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def make_description(text: str, limit=155) -> str:
    t = clean_space(text)
    t = re.sub(r"^[\s•\-“”\"]+", "", t)
    if len(t) <= limit:
        return t
    cut = t[: limit - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "…"


def normalize_size(raw: str) -> str:
    if not raw:
        return ""
    m = re.search(r"(\d+[.,]\d+|\d+)\s*[x×]\s*(\d+[.,]\d+|\d+)\s*cm", raw, re.I)
    if not m:
        return raw.strip()
    a = m.group(1).replace(".", ",")
    b = m.group(2).replace(".", ",")
    return f"{a}x{b} cm"


def is_theme(s: str) -> bool:
    s = clean_space(s)
    if not s or len(s) < 3 or len(s) > 55:
        return False
    low = s.casefold()
    if low in THEME_STOP or any(x in low for x in ("isbn", "tadımlık", "sınıf")):
        return False
    if s.endswith((",", ".", "…", "-", ":", ";")):
        return False
    if s[:1].islower() or s[:1] in "“\"'":
        return False
    if len(s.split()) > 8:
        return False
    if re.search(r"\d{4,}", s):
        return False
    letters = re.sub(r"[^A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]", "", s)
    if letters and letters == letters.upper() and len(s.split()) <= 4:
        return False
    return True


def extract_ids(text: str) -> list[str]:
    found = []
    for m in re.finditer(r"97[89]\d{10,14}|8697911\d{5,8}", text):
        raw = m.group(0)
        if raw.startswith("978978") or raw in SKIP_IDS:
            continue
        if len(raw) > 13:
            raw = raw[:13]
        if raw in SKIP_IDS:
            continue
        if raw.startswith("978") and len(raw) == 13:
            found.append(raw)
        elif raw.startswith("869") and 12 <= len(raw) <= 13:
            found.append(raw)
    # unique preserve order
    out = []
    seen = set()
    for i in found:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def split_comma_items(block: str) -> list[str]:
    block = clean_space(block)
    block = re.sub(r"^[•\-\s]+", "", block)
    block = block.replace("•", ",")
    block = re.sub(r"\.\s+", ", ", block)
    parts = re.split(r"[,;]", block)
    out = []
    for p in parts:
        p = p.strip(" .")
        if 2 <= len(p) <= 90 and not GARBAGE_TITLE.search(p):
            out.append(p)
    return out


def title_case_tr(s: str) -> str:
    small = {"ve", "ile", "ile", "ya", "veya", "de", "da"}
    words = s.split()
    out = []
    for i, w in enumerate(words):
        wl = w.casefold()
        if i > 0 and wl in small:
            out.append(wl)
        else:
            out.append(w[:1].upper() + w[1:].lower() if w else w)
    return " ".join(out)


def field_and_rest(line: str, label: str) -> tuple[str, str]:
    raw = re.sub(rf"^{re.escape(label)}\s*:\s*", "", line.strip(), flags=re.I)
    parts = re.split(r"\s{2,}", raw, maxsplit=1)
    return parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")


def parse_orta_themes(post: str) -> tuple[list[str], list[str], list[str]]:
    themes, extra, blurb_parts = [], [], []
    m = re.search(r"ANA TEMALAR", post)
    if not m:
        return themes, extra, blurb_parts
    rest = post[m.end():]
    for ln in rest.splitlines():
        if re.match(r"^\s*\d+\s*$", ln) or re.match(r"^\s*Yazar\s*:", ln):
            break
        stripped = ln.strip()
        if not stripped:
            continue
        compact = re.sub(r"TADIMLIK|OKU|TADOIKMULIK", "", stripped, flags=re.I).strip()
        letters = re.sub(r"[^A-ZÇĞİÖŞÜÂÎÛ ]", "", compact)
        indent = len(ln) - len(ln.lstrip(" "))
        if compact and compact == compact.upper() and len(letters) >= 4:
            if themes:
                break
            continue
        parts = [p.strip() for p in re.split(r"\s{2,}", stripped) if p.strip()]
        if indent < 14:
            if parts and is_theme(parts[0]):
                themes.append(parts[0])
            for p in parts[1:]:
                if is_theme(p):
                    extra.append(p)
                elif len(p) > 35:
                    blurb_parts.append(p)
        else:
            theme_like = [p for p in parts if is_theme(p)]
            if theme_like and all(len(p) < 45 for p in theme_like):
                extra.extend(theme_like)
            elif len(stripped) > 35:
                blurb_parts.append(stripped)
    return themes, extra, blurb_parts


def parse_orta(text: str) -> list[dict]:
    items = []
    matches = list(re.finditer(r"^ISBN\s*:\s*(97[89]\d{10})", text, re.M))
    for m in matches:
        isbn = m.group(1)
        pre = text[max(0, m.start() - 900): m.start()]
        post = text[m.end(): m.end() + 1600]
        nxt = re.search(r"^Yazar\s*:", post, re.M)
        if nxt:
            post = post[: nxt.start()]

        author = size = page = ""
        grades = [5, 6, 7, 8]
        blurb_parts = []
        title_lines = []
        for ln in pre.splitlines():
            s = ln.strip()
            if s.startswith("Yazar"):
                author, rest = field_and_rest(s, "Yazar")
                if rest:
                    blurb_parts.append(rest)
            elif s.startswith("Ebat"):
                val, rest = field_and_rest(s, "Ebat")
                size = normalize_size(val + " " + rest)
            elif s.startswith("Sayfa"):
                val, rest = field_and_rest(s, "Sayfa")
                page = val
            elif s.startswith("Sınıf"):
                val, rest = field_and_rest(s, "Sınıf")
                nums = [int(x) for x in re.findall(r"[1-8]", val)]
                if nums:
                    grades = nums
            else:
                cleaned = re.sub(r"TADIMLIK|OKU|TADOIKMULIK", "", s, flags=re.I).strip()
                cleaned = re.split(r"\s{2,}", cleaned)[0].strip()
                if cleaned.upper().startswith("ISBN"):
                    continue
                letters = re.sub(r"[^A-ZÇĞİÖŞÜÂÎÛ]", "", cleaned)
                if cleaned and cleaned == cleaned.upper() and len(letters) >= 3:
                    if "ANA TEMALAR" not in cleaned and not cleaned.startswith("YAZAR"):
                        title_lines.append(cleaned)

        for ln in post.splitlines():
            s = ln.strip()
            if s.startswith("Ebat"):
                val, rest = field_and_rest(s, "Ebat")
                size = normalize_size(val)
                if rest and "cm" not in rest.lower():
                    blurb_parts.append(rest)
            elif s.startswith("Sayfa"):
                val, rest = field_and_rest(s, "Sayfa")
                page = val
                if rest and "sayfa" not in rest.lower():
                    blurb_parts.append(rest)
            elif s.startswith("Sınıf"):
                val, rest = field_and_rest(s, "Sınıf")
                nums = [int(x) for x in re.findall(r"[1-8]", val)]
                if nums:
                    grades = nums
                if rest:
                    blurb_parts.append(rest)
            elif "ANA TEMALAR" in s:
                break

        full_isbn_line = text[m.start(): text.find("\n", m.start())]
        _, isbn_rest = field_and_rest(full_isbn_line, "ISBN")
        if isbn_rest:
            blurb_parts.append(isbn_rest)

        themes, extra, theme_blurb = parse_orta_themes(post)
        blurb_parts.extend(theme_blurb)
        for ln in post.splitlines():
            if "ANA TEMALAR" in ln:
                rest = ln.split("ANA TEMALAR", 1)[1].strip()
                if rest:
                    blurb_parts.append(rest)
                break
            s = ln.strip()
            if s.startswith(("Ebat", "Sayfa", "Sınıf", "Yazar", "ISBN")):
                _, rest = field_and_rest(s, s.split(":")[0].strip())
                if rest:
                    blurb_parts.append(rest)
            elif len(s) > 50:
                blurb_parts.append(s)

        title = title_case_tr(" ".join(title_lines[-3:])) if title_lines else ""
        title = re.sub(r"\s+", " ", title).strip(" -")
        if isbn == "9786051744179":
            title = "Denizler Kâşifi Kraken"
            blurb = (
                "Denizlerde başlayan gizemli girdaplar ve kaybolan dalgıçlar, Kraken araştırma "
                "gemisini okyanusun en büyük sırrının peşine düşürür. Profesör Celalettin ve "
                "ekibi, suların altında insanlık dışı deneyler yürüten çılgın bilim insanı "
                "Profesör Black ile karşı karşıya gelir. Derinlerdeki Gölge; bilimsel etik, "
                "cesaret ve teknoloji dolu, nefes kesen bir sürükleyicilik sunuyor."
            )
        blurb = clean_space(" ".join(blurb_parts))
        items.append({
            "ean": isbn,
            "all_ids": [isbn],
            "title": title,
            "authors": [author] if author else [],
            "illustrators": [],
            "size": size,
            "page": page,
            "paper": "",
            "cover": "Karton Kapak",
            "grades": grades,
        "anatemalar": merge_unique(clean_tokens(themes[:6]), clean_tokens(extra[:8])),
            "tags": [],
            "kazanimlar": [],
            "blurb": blurb,
            "source": "ortaokul",
        })
    return items


SPEC_NOISE = re.compile(
    r"^(?:1\.|Kuşe|Karton|Renkli|Her biri|Amerikan|Kitap|Ciltli|ZIPLA|Maarif|Türkçe|Hayat|Uygun|Resimli|Kazanımlarına|\d+[.,]?\d*\s*x)",
    re.I,
)


def catalog_section_items(page: str, header: str, stops: list[str]) -> list[str]:
    idx = page.find(header)
    if idx < 0:
        return []
    rest = page[idx + len(header):]
    for st in stops:
        p = rest.find(st)
        if p >= 0:
            rest = rest[:p]
    items = []
    for m in re.finditer(r"•\s*([^\n•]+(?:\n[ \t]+[^\n•]+)*)", rest):
        chunk = clean_space(m.group(1))
        chunk = re.sub(r"Ì[^Î]*Î?", "", chunk)
        chunk = re.sub(r"\d{10,13}", "", chunk)
        chunk = clean_space(chunk)
        if not chunk or SPEC_NOISE.match(chunk):
            continue
        items.extend(split_comma_items(chunk))
    if not items:
        items = [x for x in split_comma_items(rest) if not SPEC_NOISE.match(x)]
    out = []
    for x in items:
        if SPEC_NOISE.match(x) or "KAZANIM" in x or len(x) > 90:
            continue
        out.append(x)
    return out[:16]


def extract_prose_blurb(page: str) -> str:
    text = re.sub(r"(\w)-\n\s*", r"\1", page)
    m = re.search(r"Yazan(?:-Resimleyen)?:[^\n]*\n(.*?)(?:\n•\s)", text, re.S)
    primary = clean_space(m.group(1) if m else "")
    primary = re.sub(r"Ì[^Î]*Î?", "", primary)
    primary = re.sub(r"\d{10,13}", "", primary)
    if len(primary) > 180 and "BASKI" not in primary and primary.count("Tuba Bozcan") < 2:
        return primary
    paras = []
    for raw in re.split(r"\n\s*\n", text):
        chunk = clean_space(raw)
        if "BASKI" in chunk or "Yazan:" in chunk or chunk.startswith("•"):
            continue
        if GARBAGE_TITLE.search(chunk):
            continue
        if len(chunk) > 160 and re.search(r"[.!?]", chunk):
            paras.append(chunk)
    paras.sort(key=len, reverse=True)
    return paras[0] if paras else primary


def parse_ilk_page(page: str) -> dict | None:
    ids = extract_ids(page)
    if "GÜÇLÜ KARAKTER" in page.upper() or "Güçlü Karakter" in page:
        ids = ["9786051748047"]
    if not ids:
        return None
    ean = ids[0]
    if ean in SKIP_IDS:
        return None
    lines = [ln.strip() for ln in page.splitlines() if ln.strip()]
    title = ""
    for ln in lines[:12]:
        if GARBAGE_TITLE.search(ln):
            continue
        if ln.startswith("Yazan") or ln.startswith("•") or re.fullmatch(r"[\d.]+", ln):
            continue
        if "Sınıf" in ln and len(ln) < 40:
            continue
        if 3 <= len(ln) <= 80:
            title = re.sub(r"\s+", " ", ln)
            break
    if ean in TITLE_FIX:
        title = TITLE_FIX[ean]
    elif len(title) > 70 or re.search(r"[A-Z]{4,}[a-z]+[A-Z]{4,}", title):
        title = TITLE_FIX.get(ean, title)

    yazan_ln = next((ln for ln in lines if "Yazan" in ln or "Yazan-Resimleyen" in ln), "")
    author = illustrator = ""
    m_au = re.search(r"Yazan(?:-Resimleyen)?:\s*([^|]+)", yazan_ln)
    if m_au:
        author = clean_space(m_au.group(1))
    m_il = re.search(r"Resimleyen:\s*([^|]+)", yazan_ln)
    if m_il:
        illustrator = clean_space(m_il.group(1))
    elif "Yazan-Resimleyen:" in yazan_ln and author:
        illustrator = author

    blob = page
    paper = cover = page_s = size = ""
    if re.search(r"1\.\s*Hamur", blob):
        paper = "1. Hamur"
    elif re.search(r"Kuşe", blob):
        paper = "Kuşe Kağıdı"
    elif re.search(r"Kitap\s+Kâğıd", blob):
        paper = "Kitap Kağıdı"
    if "Amerikan Cilt" in blob:
        cover = "Amerikan Cilt"
    elif "Karton Kapak" in blob:
        cover = "Karton Kapak"
    m_each = re.search(r"Her biri\s+(\d+)\s*[Ss]ayfa", blob)
    m_page = re.search(r"•\s*(\d+)\s*sayfa", blob, re.I)
    if m_each:
        page_s = f"Her Biri {m_each.group(1)}"
    elif m_page:
        page_s = f"{m_page.group(1)} sayfa"
    size = normalize_size(blob)

    temas = catalog_section_items(blob, "TEMALAR", ["KAZANIM", "ETİKET", "DEĞERLER"])
    kazan = catalog_section_items(blob, "KAZANIMLAR", ["ETİKET", "DEĞERLER"])
    if not kazan:
        kazan = catalog_section_items(blob, "KAZANIM", ["ETİKET", "DEĞERLER"])
    tags = catalog_section_items(blob, "ETİKETLER", ["DEĞERLER"])
    if not tags:
        tags = catalog_section_items(blob, "DEĞERLER", ["1. Sınıf", "2. Sınıf", "3. Sınıf"])

    grades = [1]
    if re.search(r"2-3\.?\s*Sınıf", blob):
        grades = [2, 3]
    elif re.search(r"3-4\.?\s*Sınıf", blob):
        grades = [3, 4]
    elif re.search(r"4\.?\s*Sınıf", blob) and not re.search(r"[123]\.?\s*Sınıf", blob):
        grades = [4]
    elif re.search(r"2\.?\s*Sınıf", blob) and not re.search(r"1\.?\s*Sınıf", blob):
        grades = [2]
    elif re.search(r"1\.?\s*Sınıf", blob):
        grades = [1]

    blurb = extract_prose_blurb(page)

    authors = []
    if author and author.casefold() not in {"anonim"}:
        authors = [author]

    return {
        "ean": ean,
        "all_ids": ids,
        "title": title,
        "authors": authors,
        "illustrators": [illustrator] if illustrator else [],
        "size": size,
        "page": page_s,
        "paper": paper,
        "cover": cover,
        "grades": grades,
        "anatemalar": clean_tokens(temas)[:10],
        "tags": clean_tokens(tags)[:20],
        "kazanimlar": clean_tokens(kazan)[:12],
        "blurb": blurb,
        "source": "ilkokul",
    }


def split_page_products(page: str) -> list[str]:
    starts = [m.start() for m in re.finditer(r"Yazan(?:-Resimleyen)?:", page)]
    ids = extract_ids(page)
    if len(starts) >= 2 and len(ids) >= 2:
        return [page[starts[0]:starts[1]], page[starts[1]:]]
    return [page]


def parse_ilk(text: str) -> list[dict]:
    items = []
    seen = set()
    pages = text.split("\f")
    held = ""
    merged_pages = []
    for i, page in enumerate(pages):
        has_id = bool(extract_ids(page)) or ("GÜÇLÜ KARAKTER" in page.upper())
        has_yazan = bool(re.search(r"Yazan(?:-Resimleyen)?:", page))
        if has_yazan and not has_id:
            held = page
            continue
        if has_id:
            block = page
            if held and not has_yazan:
                block = held + "\n" + page
            nxt = pages[i + 1] if i + 1 < len(pages) else ""
            if nxt and not extract_ids(nxt) and not re.search(r"Yazan(?:-Resimleyen)?:", nxt):
                if re.search(r"[.!]{1}.{40,}", nxt):
                    block += "\n" + nxt
            merged_pages.append(block)
            held = ""
        elif has_yazan:
            held = page
    for page in merged_pages:
        for slice_ in split_page_products(page):
            item = parse_ilk_page(slice_)
            if not item:
                continue
            if item["ean"] in seen or item["ean"] in SKIP_IDS:
                continue
            seen.add(item["ean"])
            items.append(item)
    return items


def load_books():
    books = []
    for path in sorted(BOOKS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm, body = parse_fm(text)
        books.append({
            "path": path,
            "slug": path.stem,
            "fm": fm,
            "body": body,
            "ean": fm_get(fm, "ean").strip('"'),
            "title": fm_get(fm, "title").strip('"').strip("'"),
            "genre": fm_get(fm, "genre"),
        })
    return books


def categories_for(grades):
    if grades and max(int(g) for g in grades) <= 0:
        return ["Hikaye", "Okul Öncesi"]
    if grades and max(int(g) for g in grades) <= 4:
        return ["Hikaye", "İlkokul"]
    return ["Hikaye", "Ortaokul"]


def rename_covers(old_ean: str, new_ean: str, report: list):
    if old_ean == new_ean:
        return
    for ext in (".jpg", ".webp", ".png"):
        src = EAN_DIR / f"{old_ean}{ext}"
        dst = EAN_DIR / f"{new_ean}{ext}"
        if src.exists() and not dst.exists():
            shutil.move(str(src), str(dst))
            report.append(f"cover {src.name} -> {dst.name}")
        elif src.exists() and dst.exists():
            src.unlink()
            report.append(f"cover drop duplicate {src.name}")
    if MANIFEST.exists():
        man = MANIFEST.read_text(encoding="utf-8")
        new_man = man.replace(f"ean/{old_ean}.", f"ean/{new_ean}.")
        if new_man != man:
            MANIFEST.write_text(new_man, encoding="utf-8")
            report.append(f"manifest {old_ean} -> {new_ean}")


def preserve_set_list(body: str) -> str:
    # keep numbered set contents if present
    m = re.search(r"((?:Setin İçerdiği|SETİN İÇERDİĞİ).*)", body, re.S | re.I)
    if not m:
        # numbered list after ETİKETLER
        m = re.search(r"((?:^|\n)\d+[-–.].*(?:\n\d+[-–.].*){3,})", body)
    if not m:
        return ""
    block = m.group(1)
    block = block.replace("Cömer ", "Cömert ").replace("Teyza", "Teyze")
    # drop trailing html comments
    block = re.split(r"<!--", block, maxsplit=1)[0].strip()
    return block


def build_ilkokul_body(item: dict, old_body: str = "") -> str:
    parts = []
    if item.get("blurb"):
        parts.append(item["blurb"])
        parts.append("")
    if item.get("anatemalar"):
        parts.append("**TEMALAR:** " + ", ".join(item["anatemalar"]))
        parts.append("")
    if item.get("kazanimlar"):
        parts.append("**KAZANIMLAR:** " + ", ".join(item["kazanimlar"]))
        parts.append("")
    if item.get("tags"):
        parts.append("**ETİKETLER:** " + ", ".join(item["tags"]))
        parts.append("")
    set_list = preserve_set_list(old_body)
    if set_list:
        parts.append(set_list)
        parts.append("")
    extra_html = ""
    if "<div" in old_body or "<style" in old_body:
        extra_html = old_body if "<div" in old_body else ""
        # keep only html islands
        html_bits = re.findall(r"(<style[\s\S]*?</style>|<div[\s\S]*?</div>)", old_body, re.I)
        extra_html = "\n".join(html_bits)
        if extra_html:
            parts.append(extra_html)
            parts.append("")
    parts.append("<!--more-->")
    parts.append("")
    return "\n".join(parts)


def target_ean(book_ean: str, item: dict) -> str:
    catalog = item["ean"]
    if book_ean in BARCODE_TO_ISBN:
        return BARCODE_TO_ISBN[book_ean]
    if book_ean.startswith("869") and catalog.startswith("978"):
        return catalog
    if book_ean.startswith("869") and catalog.startswith("869") and book_ean != catalog:
        return catalog
    if book_ean.startswith("978"):
        return book_ean  # already ISBN
    return catalog if catalog else book_ean


def apply_to_existing(book, item, report):
    fm = book["fm"]
    old_ean = book["ean"]
    skip_physical = bool(item.get("skip_physical"))
    new_ean = old_ean if skip_physical else target_ean(old_ean, item)
    if new_ean != old_ean:
        rename_covers(old_ean, new_ean, report)
        fm = fm_set(fm, "ean", new_ean)

    if item.get("authors") and not skip_physical:
        fm = fm_set(fm, "authors", yaml_list(item["authors"]), after_key="paper")
        if not re.search(r"^authors:", fm, re.M):
            fm = fm_set(fm, "authors", yaml_list(item["authors"]), after_key="damlaurl")
    if item.get("illustrators") and not skip_physical:
        fm = fm_set(fm, "illustrators", yaml_list(item["illustrators"]), after_key="authors")
        if not re.search(r"^illustrators:", fm, re.M):
            fm = fm_set(fm, "illustrators", yaml_list(item["illustrators"]), after_key="paper")
    if item.get("size") and not skip_physical:
        fm = fm_set(fm, "size", yaml_scalar(item["size"]))
    if item.get("page") and not skip_physical:
        fm = fm_set(fm, "page", yaml_scalar(item["page"]))
    if item.get("paper") and not skip_physical:
        fm = fm_set(fm, "paper", yaml_scalar(item["paper"]), after_key="damlaurl")
        if not re.search(r"^paper:", fm, re.M):
            fm = fm_set(fm, "paper", yaml_scalar(item["paper"]), after_key="authors")
    if item.get("cover") and not skip_physical:
        cur = fm_get(fm, "cover").strip('"')
        if not cur or item["source"] == "ilkokul":
            fm = fm_set(fm, "cover", yaml_scalar(item["cover"]))
    if item["source"] == "ortaokul":
        cur = fm_get(fm, "cover").strip('"')
        if not cur:
            fm = fm_set(fm, "cover", yaml_scalar("Karton Kapak"))

    existing_ana = parse_yaml_list(fm_get(fm, "anatemalar"))
    if not skip_physical:
        merged = merge_unique(clean_tokens(item.get("anatemalar") or []), clean_tokens(existing_ana))
        if merged:
            fm = fm_set(fm, "anatemalar", yaml_list(merged))
        if item.get("tags"):
            existing_tags = parse_yaml_list(fm_get(fm, "tags"))
            fm = fm_set(fm, "tags", yaml_list(merge_unique(clean_tokens(item["tags"]), clean_tokens(existing_tags))))
    else:
        cleaned = clean_tokens(existing_ana)
        if cleaned != existing_ana:
            fm = fm_set(fm, "anatemalar", yaml_list(cleaned))
    blurb = item.get("blurb") or ""
    blurb_ok = len(blurb) > 70 and "BASKI" not in blurb and not re.match(r"^\d{10,}", blurb)
    if blurb_ok and not skip_physical:
        fm = fm_set(fm, "description", yaml_scalar(make_description(blurb)), after_key="title")
    elif blurb_ok and skip_physical:
        desc = fm_get(fm, "description").strip('"')
        if not desc:
            fm = fm_set(fm, "description", yaml_scalar(make_description(blurb)), after_key="title")

    body = book["body"]
    replace_body = (
        item["source"] == "ilkokul"
        and not skip_physical
        and (item.get("blurb") or item.get("anatemalar") or item.get("kazanimlar"))
    )
    if replace_body:
        body = "\n" + build_ilkokul_body(item, book["body"])

    book["path"].write_text("---" + fm + "---" + body, encoding="utf-8")
    book["fm"] = fm
    book["ean"] = new_ean
    book["body"] = body
    report.append(f"update {book['path'].name} ean={new_ean}")


def write_new_book(item, report):
    ean = item["ean"]
    if not re.fullmatch(r"\d{12,13}", ean):
        report.append(f"skip new invalid ean {ean} {item.get('title')}")
        return
    title = item.get("title") or f"Kitap {ean}"
    if GARBAGE_TITLE.search(title) or len(title) < 3 or title.upper().startswith("ISBN"):
        report.append(f"skip new bad title {ean} {title!r}")
        return
    slug = slugify(title) or ean
    path = BOOKS / f"{slug}.md"
    n = 2
    while path.exists():
        path = BOOKS / f"{slug}-{n}.md"
        n += 1
    grades = item.get("grades") or ([5, 6, 7, 8] if item["source"] == "ortaokul" else [1])
    cats = categories_for(grades)
    desc = make_description(item.get("blurb") or title)
    fm_lines = [
        "layout: book",
        f"title:  {yaml_scalar(title)}",
        f"description: {yaml_scalar(desc)}",
        f"categories: {yaml_list(cats)}",
        f"tags: {yaml_list(item.get('tags') or [])}",
        "",
        "# Standart Book Attributes",
        f"ean: {ean}",
        'languages: ["Türkçe"]',
        f"page: {yaml_scalar(item.get('page') or '')}",
        f"size: {yaml_scalar(item.get('size') or '')}",
        'publish-number: ""',
        f"cover: {yaml_scalar(item.get('cover') or 'Karton Kapak')}",
        'examlink: ""',
        f'preview_link: "https://cdn.e-damla.com.tr/PUBLIC/ornek-sayfalar/{ean}/index.html"',
        'damlaurl: ""',
        f"paper: {yaml_scalar(item.get('paper') or '')}",
        f"authors: {yaml_list(item.get('authors') or [])}",
    ]
    if item.get("illustrators"):
        fm_lines.append(f"illustrators: {yaml_list(item['illustrators'])}")
    fm_lines += [
        "",
        "# Spesific Filterable Attributes",
        "genre: story",
        f"grades: {yaml_list(grades)}",
        "kavramlar: []",
        f"anatemalar: {yaml_list(item.get('anatemalar') or [])}",
        "",
        "# Social Media Attributes",
        "youtube:",
        "",
        "# For adding excerpt add <!--more--> and break the line",
    ]
    if item["source"] == "ilkokul":
        body = "\n" + build_ilkokul_body(item)
    else:
        body = "\n" + (item.get("blurb") or "") + "\n\n<!--more-->\n"
    path.write_text("---\n" + "\n".join(fm_lines) + "\n---" + body, encoding="utf-8")
    report.append(f"NEW {path.name} ean={ean}")


def match_book(books_by_ean, books_by_slug, item):
    ean = item["ean"]
    if ean in books_by_ean:
        return books_by_ean[ean]
    for alt in item.get("all_ids") or []:
        if alt in books_by_ean:
            return books_by_ean[alt]
    # reverse barcode map
    for bar, isbn in BARCODE_TO_ISBN.items():
        if isbn == ean and bar in books_by_ean:
            return books_by_ean[bar]
        if ean == bar and isbn in books_by_ean:
            return books_by_ean[isbn]
    slug = ISBN_TO_SLUG.get(ean)
    if slug and slug in books_by_slug:
        return books_by_slug[slug]
    islug = slugify(item.get("title") or "")
    if islug in books_by_slug:
        b = books_by_slug[islug]
        if b["genre"] == "story":
            return b
    return None


def verify_utf8(text: str, label: str):
    missing = []
    if "öğrenci" not in text and "Öğrenci" not in text:
        missing.append("öğrenci")
    if "çocuk" not in text.lower() and "Çocuk" not in text:
        missing.append("çocuk")
    if "MAARİF" not in text and "Maarif" not in text:
        missing.append("Maarif")
    if "Hikâye" not in text and "hikâye" not in text and "HİKÂYE" not in text:
        missing.append("Hikâye")
    if missing:
        raise SystemExit(f"UTF-8 doğrulama başarısız ({label}): {missing}")


def main():
    orta_text = ORTA_TXT.read_text(encoding="utf-8")
    ilk_text = ILK_TXT.read_text(encoding="utf-8")
    verify_utf8(orta_text, "ortaokul")
    verify_utf8(ilk_text, "ilkokul")
    if "TÜRKİYE’NİN İLK MAARİF MODELİNE UYGUN" not in orta_text:
        raise SystemExit("ortaokul başlık bozulmuş")
    if "İlkokul" not in ilk_text and "1. Sınıflar" not in ilk_text:
        raise SystemExit("ilkokul metin beklenmedik")

    orta = parse_orta(orta_text)
    ilk = parse_ilk(ilk_text)
    INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY.write_text(
        json.dumps({"ortaokul": orta, "ilkokul": ilk}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    books = load_books()
    books_by_ean = {b["ean"]: b for b in books if b["ean"]}
    books_by_slug = {b["slug"]: b for b in books}
    report = []
    match_log = {"ortaokul": [], "ilkokul": []}

    for item in orta:
        b = match_book(books_by_ean, books_by_slug, item)
        if b and b["genre"] == "story":
            apply_to_existing(b, item, report)
            books_by_ean[b["ean"]] = b
            match_log["ortaokul"].append({"ean": item["ean"], "file": b["path"].name, "status": "update"})
        elif b and b["genre"] != "story":
            match_log["ortaokul"].append({"ean": item["ean"], "file": b["path"].name, "status": "skip-education"})
        else:
            if any(b["ean"] == item["ean"] for b in books_by_ean.values()):
                match_log["ortaokul"].append({"ean": item["ean"], "status": "exists"})
            else:
                write_new_book(item, report)
                match_log["ortaokul"].append({"ean": item["ean"], "title": item["title"], "status": "new"})

    # reload ean index after orta (new files + ean changes)
    books = load_books()
    books_by_ean = {b["ean"]: b for b in books if b["ean"]}
    books_by_slug = {b["slug"]: b for b in books}

    for item in ilk:
        b = match_book(books_by_ean, books_by_slug, item)
        if b and b["genre"] == "story":
            existing_grades = parse_yaml_list(fm_get(b["fm"], "grades"))
            nums = [int(g) for g in existing_grades if str(g).lstrip("-").isdigit()]
            if nums and max(nums) >= 5:
                item = dict(item)
                item["grades"] = nums
                item["skip_physical"] = True
            apply_to_existing(b, item, report)
            books_by_ean.pop(b.get("ean"), None)
            books_by_ean[fm_get(b["path"].read_text(encoding="utf-8").split("---", 2)[1], "ean")] = b
            match_log["ilkokul"].append({"ean": item["ean"], "file": b["path"].name, "status": "update"})
        elif b and b["genre"] != "story":
            match_log["ilkokul"].append({"ean": item["ean"], "file": b["path"].name, "status": "skip-education"})
        else:
            if item["ean"] in books_by_ean:
                match_log["ilkokul"].append({"ean": item["ean"], "status": "exists"})
            else:
                write_new_book(item, report)
                match_log["ilkokul"].append({"ean": item["ean"], "title": item["title"], "status": "new"})

    REPORT.write_text(json.dumps(match_log, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "docs" / "_extract" / "katalog-uygulama.log").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    print("orta", len(orta), "ilk", len(ilk), "ops", len(report))
    print("NEW", sum(1 for x in report if x.startswith("NEW")))
    print("update", sum(1 for x in report if x.startswith("update")))


if __name__ == "__main__":
    main()
