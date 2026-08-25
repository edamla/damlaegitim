#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MEB TYMM Chart API → docs/data/tymm/*/api-response.json"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from data_paths import CANONICAL, DOCS_TYMM, REF_TYMM_HAM
from parse_erdem_deger import fetch_erdem_html, parse_erdem_deger_html, validate_tree
from parse_tymm_beceri import (
    BECERI_PAGES,
    EGILIMLER_BASLIK,
    EGILIMLER_SLUG,
    count_nodes,
    fetch_beceri_html,
    parse_beceri_html,
    validate_beceri_payload,
)

API_BASE = "https://tymm.meb.gov.tr/Chart/GetStackCharts"
USER_AGENT = (
    "Mozilla/5.0 (compatible; damlaegitim-fetch-tymm/1.0; +https://damlaokul.com)"
)
MAX_RETRIES = 4
RETRY_BACKOFF = 2.0
DELAY_SEC = 0.4

PROGRAMS: Tuple[Tuple[str, str, Path, int], ...] = (
    (
        "ilkokul-turkce",
        "ilkokul-turkce-dersi",
        CANONICAL["tymm_ilkokul_api"],
        4,
    ),
    (
        "ortaokul-turkce",
        "ortaokul-turkce-dersi",
        CANONICAL["tymm_ortaokul_api"],
        4,
    ),
)


def http_get(url: str, timeout: int = 120) -> bytes:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://tymm.meb.gov.tr/ogretim-programlari/ders/",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read()


def fetch_chart(slug: str) -> Dict[str, Any]:
    url = f"{API_BASE}?url={slug}"
    last_err: Optional[BaseException] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = http_get(url)
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                raise RuntimeError(f"Beklenmeyen yanıt türü: {type(payload)}")
            return payload
        except (urllib.error.URLError, TimeoutError, ssl.SSLError, json.JSONDecodeError, RuntimeError) as exc:
            last_err = exc
            wait = RETRY_BACKOFF * attempt
            print(f"  [WARN] {slug} ({attempt}/{MAX_RETRIES}): {exc}; {wait:.1f}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"TYMM API başarısız: {slug}") from last_err


def validate_payload(payload: Dict[str, Any], expected_charts: int, label: str) -> List[str]:
    charts = payload.get("stackedChart")
    if not isinstance(charts, list):
        raise RuntimeError(f"{label}: stackedChart listesi yok")
    if len(charts) != expected_charts:
        raise RuntimeError(
            f"{label}: {len(charts)} grafik (beklenen {expected_charts})"
        )
    return [str(c.get("name", "")) for c in charts]


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


def copy_vendor(src: Path, dest: Path) -> Dict[str, Any]:
    if not src.is_file():
        raise FileNotFoundError(f"Vendor dosyası yok: {src}")
    payload = json.loads(src.read_text(encoding="utf-8"))
    write_json(dest, payload)
    return payload


def fetch_cerceveler(today: str, from_vendor: bool) -> Dict[str, Any]:
    output_path = CANONICAL["tymm_cerceveler"]
    print(f"[cerceveler] -> {output_path.relative_to(DOCS_TYMM.parent.parent)}")
    if from_vendor:
        if not output_path.is_file():
            raise FileNotFoundError(f"Vendor dosyası yok: {output_path}")
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    else:
        degerler = parse_erdem_deger_html(fetch_erdem_html())
        validate_tree(degerler)

        beceriler: Dict[str, Any] = {}
        for slug, key, baslik in BECERI_PAGES:
            beceri = parse_beceri_html(fetch_beceri_html(slug), slug, baslik)
            validate_beceri_payload(beceri)
            beceriler[key] = {
                "baslik": beceri["baslik"],
                "kaynak": beceri["kaynak"],
                "slug": beceri["slug"],
                "gruplar": beceri["gruplar"],
            }
            grup, alt, surec = count_nodes(beceri["gruplar"])
            print(f"  [{key}] {grup} grup, {alt} alt, {surec} süreç")

        egilimler_raw = parse_beceri_html(
            fetch_beceri_html(EGILIMLER_SLUG), EGILIMLER_SLUG, EGILIMLER_BASLIK
        )
        validate_beceri_payload(egilimler_raw)
        egilimler = {
            "baslik": egilimler_raw["baslik"],
            "kaynak": egilimler_raw["kaynak"],
            "slug": egilimler_raw["slug"],
            "gruplar": egilimler_raw["gruplar"],
        }
        eg_grup, eg_alt, _ = count_nodes(egilimler["gruplar"])

        payload = {
            "guncelleme": today,
            "degerler": degerler,
            "beceriler": beceriler,
            "egilimler": egilimler,
        }
        alt_count = sum(len(d.get("alt_kavramlar") or []) for d in degerler["degerler"])
        surec_count = sum(
            len(a.get("surec_bilesenleri") or [])
            for d in degerler["degerler"]
            for a in (d.get("alt_kavramlar") or [])
        )
        print(
            f"  [degerler] {len(degerler['degerler'])} değer, "
            f"{alt_count} alt, {surec_count} süreç"
        )
        print(f"  [egilimler] {eg_grup} grup, {eg_alt} eğilim")

    for section in ("degerler", "beceriler", "egilimler"):
        if section not in payload:
            raise RuntimeError(f"cerceveler.json eksik bölüm: {section}")

    write_json(output_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="MEB TYMM müfredat grafik verisini çeker.")
    parser.add_argument(
        "--cerceveler",
        action="store_true",
        help=f"Değerler + beceriler + eğilimler → {CANONICAL['tymm_cerceveler'].name}",
    )
    parser.add_argument(
        "--degerler",
        action="store_true",
        help="--cerceveler ile aynı (geriye dönük)",
    )
    parser.add_argument(
        "--egilimler",
        action="store_true",
        help="--cerceveler ile aynı (geriye dönük)",
    )
    parser.add_argument(
        "--beceriler",
        action="store_true",
        help="--cerceveler ile aynı (geriye dönük)",
    )
    parser.add_argument(
        "--beceri",
        choices=[p[0] for p in BECERI_PAGES],
        help="Yoksayıldı; --cerceveler tümünü çeker.",
    )
    parser.add_argument(
        "--from-vendor",
        action="store_true",
        help="Ağ çekmeden mevcut dosyaları doğrula (yolları değiştirmez).",
    )
    parser.add_argument(
        "--only",
        choices=[p[0] for p in PROGRAMS],
        help="Yalnızca seçilen Türkçe programını çek.",
    )
    args = parser.parse_args()

    today = date.today().isoformat()
    framework = (
        args.cerceveler
        or args.degerler
        or args.beceriler
        or args.beceri
        or args.egilimler
    )

    if framework:
        fetch_cerceveler(today, args.from_vendor)

    if framework and not args.only:
        print("Tamamlandı.")
        return 0

    selected = [p for p in PROGRAMS if not args.only or p[0] == args.only]
    if not selected:
        if not framework:
            parser.error("En az bir işlem seçin")
        print("Tamamlandı.")
        return 0

    for folder, slug, output_path, expected in selected:
        label = folder
        print(f"[{label}] -> {output_path.relative_to(DOCS_TYMM.parent.parent)}")
        if args.from_vendor:
            if not output_path.is_file():
                raise FileNotFoundError(f"Vendor yok: {output_path}")
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        else:
            payload = fetch_chart(slug)
            meta = {
                "kaynak": API_BASE,
                "url": slug,
                "referans": REF_TYMM_HAM,
                "guncelleme": today,
            }
            payload["_meta"] = meta
            write_json(output_path, payload)
            time.sleep(DELAY_SEC)

        names = validate_payload(payload, expected, label)
        print(f"  OK — {expected} sınıf: {', '.join(names)}")

    print("Tamamlandı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
