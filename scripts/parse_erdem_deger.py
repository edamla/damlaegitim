#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MEB Erdem-Değer-Eylem sayfası HTML → hiyerarşik JSON."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from parse_tymm_beceri import (
    beceri_url,
    fetch_beceri_html,
    parse_node_block,
    split_top_level_li_blocks,
)
from parse_tymm_beceri import extract_body_html

ERDEM_SLUG = "erdem-deger-eylem-cercevesi"
ERDEM_URL = beceri_url(ERDEM_SLUG)

CATI_DEGERLER = ["Adalet", "Saygı", "Sorumluluk"]
ALANLAR: Dict[str, List[str]] = {
    "kisisel": [
        "Tasarruf",
        "Sabır",
        "Mahremiyet",
        "Mütevazılık",
        "Sağlıklı Yaşam",
        "Çalışkanlık",
    ],
    "aile_ve_sosyal": [
        "Sevgi",
        "Dostluk",
        "Özgürlük",
        "Dürüstlük",
        "Vatanseverlik",
        "Yardımseverlik",
        "Aile Bütünlüğü",
    ],
    "fiziksel_cevre": ["Temizlik", "Duyarlılık", "Estetik", "Merhamet"],
}


def alan_for_ad(ad: str) -> Optional[str]:
    for key, names in ALANLAR.items():
        if ad in names:
            return key
    return None


def parse_deger_block(block: str) -> Dict[str, Any]:
    item = parse_node_block(block)
    kod = item.get("kod", "")
    if not kod or not kod.startswith("D") or kod.count(".") != 0:
        raise RuntimeError(f"beklenmeyen üst düzey değer kodu: {kod!r}")

    ad = item["ad"]
    if ad in CATI_DEGERLER:
        item["cati"] = True
    alan = alan_for_ad(ad)
    if alan:
        item["alan"] = alan
    return item


def fetch_erdem_html() -> str:
    return fetch_beceri_html(ERDEM_SLUG)


def parse_erdem_deger_html(html: str) -> Dict[str, Any]:
    body = extract_body_html(html)
    degerler = [parse_deger_block(block) for block in split_top_level_li_blocks(body)]
    if len(degerler) != 20:
        raise RuntimeError(f"20 değer bekleniyordu, {len(degerler)} bulundu")
    return {
        "kaynak": ERDEM_URL,
        "baslik": "Erdem-Değer-Eylem Çerçevesi — Değerler",
        "cati_degerler": CATI_DEGERLER,
        "alanlar": ALANLAR,
        "degerler": degerler,
    }


def validate_tree(payload: Dict[str, Any]) -> None:
    degerler = payload.get("degerler")
    if not isinstance(degerler, list) or len(degerler) != 20:
        raise RuntimeError("degerler listesi geçersiz")
    for idx, deger in enumerate(degerler, start=1):
        expected = f"D{idx}"
        if deger.get("kod") != expected:
            raise RuntimeError(f"sıra hatası: {deger.get('kod')} != {expected}")
        alt = deger.get("alt_kavramlar") or []
        if not alt:
            raise RuntimeError(f"{expected} alt_kavramlar boş")
        for alt_item in alt:
            surec = alt_item.get("surec_bilesenleri") or []
            if not surec:
                raise RuntimeError(f"{alt_item.get('kod')} surec_bilesenleri boş")
