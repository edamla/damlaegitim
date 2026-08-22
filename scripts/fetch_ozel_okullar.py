#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OOKGM özel okullar → mevcut docs/data/okullar.json birleştirme."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlencode

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from fetch_okullar import (
    DELAY_SEC,
    OUTPUT_PATH,
    fold_tr,
    load_adres_lookup,
    parse_iller_from_index,
    request_with_retry,
    sort_iller,
    strip_html,
    title_tr,
)
from data_paths import REF_TURKIYE_ADRES

KAYNAK_OZEL = "https://ookgm.meb.gov.tr/kurumlar.php?tur=okul"
INDEX_URL = "https://ookgm.meb.gov.tr/kurumlar.php?tur=okul"
PAGE_URL = "https://ookgm.meb.gov.tr/kurumlar.php"

COUNT_RE = re.compile(r"(\d+)\s*adet\s+kurum\s+bulundu", re.I)
SAIFA_RE = re.compile(r"[?&]sayfa=(\d+)", re.I)
SKIP_LABELS = {
    "ilçe",
    "ilce",
    "kurum adı",
    "kurum adi",
    "kurum türü",
    "kurum turu",
    "adres",
    "telefon",
    "tüm türler",
    "tum turler",
}


def upper_tr(text: str) -> str:
    out: List[str] = []
    for ch in text or "":
        if ch == "i":
            out.append("İ")
        elif ch == "ı":
            out.append("I")
        else:
            out.append(ch.upper())
    return "".join(out)


def decode_html(raw: bytes) -> str:
    for enc in ("utf-8", "iso-8859-9", "windows-1254"):
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError:
            continue
        if "Kurum" in text or "kurum" in text or "İL" in text or "İl" in text:
            return text
    return raw.decode("utf-8", errors="replace")


def normalize_phone(text: str, href: str = "") -> str:
    if href.lower().startswith("tel:"):
        digits = re.sub(r"\D", "", href.split(":", 1)[1])
        if digits:
            return digits
    digits = re.sub(r"\D", "", text or "")
    return digits


class KurumTableParser(HTMLParser):
    """OOKGM kurumlar.php HTML tablosundan satır toplar."""

    def __init__(self) -> None:
        super().__init__()
        self._in_td = False
        self._in_tr = False
        self._cell_text: List[str] = []
        self._cell_href = ""
        self._row_cells: List[str] = []
        self._row_hrefs: List[str] = []
        self.rows: List[Dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        ad = dict(attrs)
        if tag == "tr":
            self._in_tr = True
            self._row_cells = []
            self._row_hrefs = []
        elif tag == "td" and self._in_tr:
            self._in_td = True
            self._cell_text = []
            self._cell_href = ""
        elif tag == "a" and self._in_td:
            href = (ad.get("href") or "").strip()
            if href.lower().startswith("tel:"):
                self._cell_href = href

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._in_td:
            text = strip_html(" ".join(self._cell_text))
            self._row_cells.append(text)
            self._row_hrefs.append(self._cell_href)
            self._in_td = False
        elif tag == "tr" and self._in_tr:
            self._in_tr = False
            parsed = _row_from_cells(self._row_cells, self._row_hrefs)
            if parsed:
                self.rows.append(parsed)

    def handle_data(self, data: str) -> None:
        if self._in_td:
            self._cell_text.append(data)


def _row_from_cells(cells: List[str], hrefs: List[str]) -> Optional[Dict[str, str]]:
    if len(cells) < 5:
        return None
    # Sütunlar: [#] ilçe ad tür adres telefon  — ilk hücre sıra numarası olabilir.
    offset = 1 if cells[0].strip().isdigit() else 0
    if len(cells) - offset < 5:
        return None
    ilce = cells[offset].strip()
    ad = cells[offset + 1].strip()
    tur = cells[offset + 2].strip()
    adres = cells[offset + 3].strip()
    tel_idx = offset + 4
    telefon_raw = cells[tel_idx] if tel_idx < len(cells) else ""
    href = hrefs[tel_idx] if tel_idx < len(hrefs) else ""
    if not ad or not ilce:
        return None
    if fold_tr(ilce) in SKIP_LABELS or fold_tr(ad) in SKIP_LABELS:
        return None
    if fold_tr(tur).startswith("tüm tür") or fold_tr(tur).startswith("tum tur"):
        return None
    item = {
        "ilce": ilce,
        "ad": ad,
        "tur": tur,
        "adres": adres,
        "telefon": normalize_phone(telefon_raw, href),
    }
    return item


def parse_count(html: str) -> Optional[int]:
    match = COUNT_RE.search(html)
    if not match:
        return None
    return int(match.group(1))


def parse_table(html: str) -> List[Dict[str, str]]:
    parser = KurumTableParser()
    parser.feed(html)
    return parser.rows


def fetch_html(il_value: str, sayfa: int) -> str:
    # Sitedeki sıra: sayfa=&tur=okul&il=&tur2=0 (sayfa=1 dahil).
    query = urlencode(
        [("sayfa", str(sayfa)), ("tur", "okul"), ("il", il_value), ("tur2", "0")],
        encoding="utf-8",
    )
    url = f"{PAGE_URL}?{query}"
    raw = request_with_retry(url)
    return decode_html(raw)


def parse_max_page(html: str) -> int:
    nums = [int(x) for x in SAIFA_RE.findall(html)]
    return max(nums) if nums else 1


def parse_selected_il(html: str) -> Optional[str]:
    match = re.search(
        r'<select[^>]*\bname=["\']il["\'][^>]*>(.*?)</select>',
        html,
        flags=re.I | re.S,
    )
    if not match:
        return None
    for opt in re.finditer(r"<option\b([^>]*)>", match.group(1), flags=re.I):
        attrs = opt.group(1)
        if not re.search(r"\bselected\b", attrs, flags=re.I):
            continue
        vm = re.search(r'\bvalue=["\']([^"\']*)["\']', attrs, flags=re.I)
        if vm and vm.group(1).strip():
            return vm.group(1).strip()
    return None


def fetch_il_kurumlar(il_value: str, delay: float) -> Tuple[List[Dict[str, str]], Optional[int]]:
    collected: List[Dict[str, str]] = []
    seen: set[Tuple[str, str, str]] = set()
    html = fetch_html(il_value, 1)
    selected = parse_selected_il(html)
    if selected and fold_tr(selected) != fold_tr(il_value):
        print(
            f"    [UYARI] istek il={il_value}, sunucu seçili il={selected}; atlandı",
            file=sys.stderr,
        )
        return [], None
    expected = parse_count(html)
    max_page = parse_max_page(html)
    page = 1
    while page <= max(max_page, 1):
        if page > 1:
            html = fetch_html(il_value, page)
            page_count = parse_count(html)
            if page_count:
                expected = max(expected or 0, page_count)
            max_page = max(max_page, parse_max_page(html))
        rows = parse_table(html)
        new_rows = 0
        for row in rows:
            key = (fold_tr(row["ilce"]), fold_tr(row["ad"]), fold_tr(row["tur"]))
            if key in seen:
                continue
            seen.add(key)
            collected.append(row)
            new_rows += 1
        print(
            f"    sayfa={page}/{max_page} satır={len(rows)} yeni={new_rows} "
            f"biriken={len(collected)} beklenen={expected or '?'}"
        )
        if page >= max_page:
            break
        page += 1
        if delay > 0:
            time.sleep(delay)
    return collected, expected


def strip_ozel(iller: Dict[str, Any], only_il_kods: Optional[set[str]]) -> int:
    removed = 0
    for il_kod, il_node in list(iller.items()):
        if only_il_kods is not None and str(il_kod) not in only_il_kods:
            continue
        if not isinstance(il_node, dict):
            continue
        for ilce_node in (il_node.get("ilceler") or {}).values():
            if not isinstance(ilce_node, dict):
                continue
            old = ilce_node.get("kurumlar") or []
            kept = [k for k in old if not (isinstance(k, dict) and k.get("ozel") is True)]
            removed += len(old) - len(kept)
            ilce_node["kurumlar"] = kept
    return removed


def prune_empty_unknown_ilce(iller: Dict[str, Any]) -> None:
    for il_node in iller.values():
        if not isinstance(il_node, dict):
            continue
        ilceler = il_node.get("ilceler")
        if not isinstance(ilceler, dict):
            continue
        for kod in list(ilceler):
            node = ilceler.get(kod)
            if kod == "0" and isinstance(node, dict) and not (node.get("kurumlar") or []):
                del ilceler[kod]


def count_kurumlar(iller: Dict[str, Any]) -> Tuple[int, int]:
    total = 0
    ozel = 0
    for il_node in iller.values():
        if not isinstance(il_node, dict):
            continue
        for ilce_node in (il_node.get("ilceler") or {}).values():
            if not isinstance(ilce_node, dict):
                continue
            for kurum in ilce_node.get("kurumlar") or []:
                if not isinstance(kurum, dict):
                    continue
                total += 1
                if kurum.get("ozel") is True:
                    ozel += 1
    return total, ozel


def public_name_keys(iller: Dict[str, Any]) -> set[Tuple[str, str, str]]:
    keys: set[Tuple[str, str, str]] = set()
    for il_kod, il_node in iller.items():
        if not isinstance(il_node, dict):
            continue
        for ilce_kod, ilce_node in (il_node.get("ilceler") or {}).items():
            if not isinstance(ilce_node, dict):
                continue
            for kurum in ilce_node.get("kurumlar") or []:
                if not isinstance(kurum, dict) or kurum.get("ozel") is True:
                    continue
                ad = fold_tr(str(kurum.get("ad") or ""))
                if ad:
                    keys.add((str(il_kod), str(ilce_kod), ad))
    return keys


def fallback_iller_from_adres() -> List[Tuple[str, str]]:
    from fetch_okullar import ADRES_PATH

    data = json.loads(ADRES_PATH.read_text(encoding="utf-8"))
    rows: List[Tuple[str, str]] = []
    for il in data.get("iller") or []:
        ad = str(il.get("ad") or "").strip()
        if ad:
            rows.append((upper_tr(ad), ad))
    return rows


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="OOKGM özel okullarını mevcut docs/data/okullar.json içine birleştirir"
    )
    parser.add_argument("--il", help="Yalnızca bu il (ör. ANKARA veya 6)")
    parser.add_argument("--delay", type=float, default=DELAY_SEC)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--okullar", type=Path, default=OUTPUT_PATH, help="Mevcut okullar.json")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.okullar.is_file():
        print(f"okullar.json yok: {args.okullar}", file=sys.stderr)
        return 1

    print(f"Okunuyor: {args.okullar}")
    payload = json.loads(args.okullar.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("iller"), dict):
        print("okullar.json beklenen hiyerarşide değil", file=sys.stderr)
        return 1
    iller_tree: Dict[str, Any] = payload["iller"]

    print("OOKGM il listesi alınıyor…")
    try:
        index_html = decode_html(request_with_retry(INDEX_URL))
        ookgm_iller = parse_iller_from_index(index_html)
    except Exception as exc:
        print(f"  [WARN] kurumlar.php okunamadı ({exc}); adres listesi kullanılacak", file=sys.stderr)
        ookgm_iller = []
    if not ookgm_iller:
        ookgm_iller = fallback_iller_from_adres()
        print(f"  yedek il listesi: {len(ookgm_iller)}")
    else:
        have = {fold_tr(value) for value, _label in ookgm_iller}
        have |= {fold_tr(label) for _value, label in ookgm_iller}
        extra = [
            pair
            for pair in fallback_iller_from_adres()
            if fold_tr(pair[0]) not in have and fold_tr(pair[1]) not in have
        ]
        if extra:
            ookgm_iller.extend(extra)
            print(f"  {len(ookgm_iller) - len(extra)} il + {len(extra)} adres yedeği")
        else:
            print(f"  {len(ookgm_iller)} il bulundu")

    adres = load_adres_lookup()
    wanted = str(args.il).strip() if args.il else ""
    if wanted:
        ookgm_iller = [
            pair
            for pair in ookgm_iller
            if fold_tr(pair[0]) == fold_tr(wanted)
            or fold_tr(pair[1]) == fold_tr(wanted)
            or str(adres.resolve_il(pair[1])[0]) == wanted
            or str(adres.resolve_il(pair[0])[0]) == wanted
        ]
        if not ookgm_iller:
            print(f"İl bulunamadı: {args.il}", file=sys.stderr)
            return 1

    target_il_kods: Optional[set[str]] = None
    if wanted:
        target_il_kods = {adres.resolve_il(label or value)[0] for value, label in ookgm_iller}
        target_il_kods |= {adres.resolve_il(value)[0] for value, _label in ookgm_iller}

    removed = strip_ozel(iller_tree, target_il_kods)
    print(f"  silinen eski özel kayıt: {removed}")
    public_keys = public_name_keys(iller_tree)

    added = 0
    skipped_dup = 0
    for i, (value, label) in enumerate(ookgm_iller, start=1):
        il_param = value or upper_tr(label)
        print(f"[{i}/{len(ookgm_iller)}] {label} ({il_param})")
        try:
            rows, expected = fetch_il_kurumlar(il_param, delay=args.delay)
        except Exception as exc:
            print(f"  [HATA] {label}: {exc}", file=sys.stderr)
            continue
        if expected is not None and len(rows) != expected:
            print(
                f"  [UYARI] {label}: sitede {expected} adet yazıyor, "
                f"ayrıştırılan benzersiz satır {len(rows)} (kaynak sayacı yanıltıcı olabilir)",
                file=sys.stderr,
            )
        il_kod, il_ad = adres.resolve_il(label or il_param)
        if il_kod == "0":
            il_kod, il_ad = adres.resolve_il(il_param)
        for row in rows:
            ilce_kod, ilce_ad = adres.resolve_ilce(il_kod, row["ilce"])
            ad = title_tr(row["ad"])
            tur = row["tur"].strip() or "Diğer"
            key = (il_kod, ilce_kod, fold_tr(ad))
            if key in public_keys:
                skipped_dup += 1
                continue
            item: Dict[str, Any] = {
                "ad": ad,
                "tur": tur,
                "ozel": True,
            }
            if row.get("adres"):
                item["adres"] = row["adres"]
            if row.get("telefon"):
                item["telefon"] = row["telefon"]
            il_node = iller_tree.setdefault(il_kod, {"ad": il_ad, "ilceler": {}})
            il_node["ad"] = il_ad
            ilce_node = il_node["ilceler"].setdefault(ilce_kod, {"ad": ilce_ad, "kurumlar": []})
            ilce_node["ad"] = ilce_ad
            ilce_node["kurumlar"].append(item)
            public_keys.add(key)
            added += 1
        if args.delay > 0:
            time.sleep(args.delay)

    if adres.unmatched_il or adres.unmatched_ilce:
        print(
            f"  [UYARI] eşleşmeyen il: {adres.unmatched_il}, ilçe: {adres.unmatched_ilce}",
            file=sys.stderr,
        )
    if skipped_dup:
        print(
            f"  [UYARI] aynı il/ilçe+ad çakışması atlandı: {skipped_dup}",
            file=sys.stderr,
        )

    payload["iller"] = sort_iller(iller_tree)
    prune_empty_unknown_ilce(payload["iller"])
    total, ozel_count = count_kurumlar(payload["iller"])
    payload["kaynak_ozel"] = KAYNAK_OZEL
    payload["sayi_ozel"] = ozel_count
    payload["sayi"] = total
    payload["guncelleme"] = date.today().isoformat()
    payload["referans"] = payload.get("referans") or REF_TURKIYE_ADRES

    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(f"Yazıldı: {args.output} (toplam={total}, özel={ozel_count}, eklenen={added})")
    if args.output.resolve() == OUTPUT_PATH.resolve():
        from sync_site_data import sync

        sync()
    return 0 if added or ozel_count else 1


if __name__ == "__main__":
    sys.exit(main())
