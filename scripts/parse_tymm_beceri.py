#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MEB TYMM beceri sayfaları (accordion HTML) → hiyerarşik JSON."""

from __future__ import annotations

import re
import ssl
import urllib.request
from html import unescape
from typing import Any, Dict, List, Optional, Tuple

USER_AGENT = "Mozilla/5.0 (compatible; damlaegitim-parse-tymm-beceri/1.0)"
LI_OPEN = '<li class="beceri-accordion-item">'
SUREC_TD_RE = re.compile(
    r"<td>([A-Z]{1,6}[\d.]+(?:\.SB\d+)?)\.\s*([^<]+)</td>",
    re.S,
)

BECERI_PAGES: Tuple[Tuple[str, str, str], ...] = (
    ("kavramsal-beceriler", "kavramsal", "Kavramsal Beceriler"),
    ("alan-becerileri", "alan", "Alan Becerileri"),
    (
        "sosyal-duygusal-ogrenme-becerileri",
        "sosyal_duygusal",
        "Sosyal-Duygusal Öğrenme Becerileri",
    ),
    (
        "sosyal-bilimler-alan-becerileri",
        "sosyal_bilimler",
        "Sosyal Bilimler Alan Becerileri",
    ),
    ("okuryazarlik-becerileri", "okuryazarlik", "Okuryazarlık Becerileri"),
)

EGILIMLER_SLUG = "egilimler"
EGILIMLER_BASLIK = "Eğilimler"


def beceri_url(slug: str) -> str:
    return f"https://tymm.meb.gov.tr/beceriler/{slug}"


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text or "")).strip()


def parse_trigger_text(raw: str) -> Tuple[Optional[str], str]:
    text = normalize_ws(raw)
    match = re.match(r"^([A-Z]{1,6}[\d.]+)\.(.+)$", text)
    if match:
        return match.group(1).rstrip("."), match.group(2).strip()
    match = re.match(r"^(.+?)\s*\(([A-Z]{1,6}\d*)\)\s*$", text)
    if match:
        return match.group(2), match.group(1).strip()
    return None, text


def find_accordion_ul_inner(parent_html: str, class_fragment: str) -> Optional[str]:
    match = re.search(rf'<ul class="beceri-accordion {class_fragment}">', parent_html)
    if not match:
        return None
    pos = match.end()
    depth = 1
    j = pos
    while j < len(parent_html):
        if parent_html.startswith("<ul", j):
            depth += 1
            j += 3
            continue
        if parent_html.startswith("</ul>", j):
            depth -= 1
            if depth == 0:
                return parent_html[pos:j]
            j += 5
            continue
        j += 1
    return None


def find_accordion_child_list_inner(parent_html: str) -> Optional[str]:
    match = re.search(r'<ul class="beceri-accordion child-list-\d+">', parent_html)
    if not match:
        return None
    pos = match.end()
    depth = 1
    j = pos
    while j < len(parent_html):
        if parent_html.startswith("<ul", j):
            depth += 1
            j += 3
            continue
        if parent_html.startswith("</ul>", j):
            depth -= 1
            if depth == 0:
                return parent_html[pos:j]
            j += 5
            continue
        j += 1
    return None


def is_li_open(html: str, pos: int) -> bool:
    if not html.startswith("<li", pos):
        return False
    next_ch = html[pos + 3] if pos + 3 < len(html) else ""
    return next_ch in (" ", ">", "\n", "\r", "\t", "/") or next_ch == ""


def split_li_blocks(html: str) -> List[str]:
    blocks: List[str] = []
    pos = 0
    while True:
        idx = html.find(LI_OPEN, pos)
        if idx < 0:
            break
        depth = 0
        j = idx
        while j < len(html):
            if is_li_open(html, j):
                depth += 1
                gt = html.find(">", j)
                if gt < 0:
                    break
                j = gt + 1
                continue
            if html.startswith("</li>", j):
                depth -= 1
                if depth == 0:
                    blocks.append(html[idx : j + 5])
                    pos = j + 5
                    break
                j += 5
                continue
            j += 1
        else:
            break
    return blocks


def split_top_level_li_blocks(html: str) -> List[str]:
    inner = find_accordion_ul_inner(html, "main-list")
    if inner is None:
        raise RuntimeError("main-list bulunamadı")
    return split_li_blocks(inner)


def split_child_li_blocks(parent_html: str) -> List[str]:
    inner = find_accordion_child_list_inner(parent_html)
    if not inner:
        return []
    return split_li_blocks(inner)


def parse_surec_bilesenleri(block: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for raw_code, raw_text in SUREC_TD_RE.findall(block):
        rows.append({"kod": raw_code.rstrip("."), "ad": normalize_ws(raw_text)})
    return rows


def parse_node_block(block: str) -> Dict[str, Any]:
    trigger = re.search(r'<span class="trigger-text">([^<]+)</span>', block)
    if not trigger:
        raise RuntimeError("trigger-text bulunamadı")
    kod, ad = parse_trigger_text(trigger.group(1))

    desc_match = re.search(r'<p class="beceri-desc">([^<]*)</p>', block)
    aciklama = normalize_ws(desc_match.group(1)) if desc_match else ""

    alt_kavramlar = [parse_node_block(child) for child in split_child_li_blocks(block)]
    surec_bilesenleri = parse_surec_bilesenleri(block)

    item: Dict[str, Any] = {"ad": ad}
    if kod:
        item["kod"] = kod
    if aciklama:
        item["aciklama"] = aciklama
    if alt_kavramlar:
        item["alt_kavramlar"] = alt_kavramlar
    if surec_bilesenleri:
        item["surec_bilesenleri"] = surec_bilesenleri
    return item


def extract_body_html(html: str) -> str:
    start = html.find('class="beceri-children-body"')
    if start < 0:
        raise RuntimeError("beceri-children-body bulunamadı")
    end = html.find('class="beceri-footer"', start)
    if end < 0:
        end = len(html)
    return html[start:end]


def fetch_beceri_html(slug: str) -> str:
    url = beceri_url(slug)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
        return resp.read().decode("utf-8")


def parse_beceri_html(html: str, slug: str, baslik: str) -> Dict[str, Any]:
    body = extract_body_html(html)
    gruplar = [parse_node_block(block) for block in split_top_level_li_blocks(body)]
    if not gruplar:
        raise RuntimeError(f"{slug}: gruplar boş")
    return {
        "kaynak": beceri_url(slug),
        "slug": slug,
        "baslik": baslik,
        "gruplar": gruplar,
    }


def count_nodes(nodes: List[Dict[str, Any]]) -> Tuple[int, int, int]:
    """grup, alt_kavram, surec sayıları."""
    grup = len(nodes)
    alt = 0
    surec = 0

    def walk(node: Dict[str, Any], depth: int) -> None:
        nonlocal alt, surec
        if depth > 0:
            alt += 1
        surec += len(node.get("surec_bilesenleri") or [])
        for child in node.get("alt_kavramlar") or []:
            walk(child, depth + 1)

    for node in nodes:
        walk(node, 0)
    return grup, alt, surec


def validate_beceri_payload(payload: Dict[str, Any]) -> None:
    gruplar = payload.get("gruplar")
    if not isinstance(gruplar, list) or not gruplar:
        raise RuntimeError("gruplar geçersiz")
