#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kanonik (docs/data) ve site türetilmiş veri yolları."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DATA = ROOT / "docs" / "data"
DOCS_TYMM = DOCS_DATA / "tymm"
DOCS_TYMM_BECERILER = DOCS_TYMM / "beceriler"

CANONICAL = {
    "turkiye_adres": DOCS_DATA / "turkiye_adres.json",
    "turkiye_geodata": DOCS_DATA / "turkiye_geodata.json",
    "okullar": DOCS_DATA / "okullar.json",
    "okullar_detay": DOCS_DATA / "okullar_detay.json",
    "population": DOCS_DATA / "population.json",
    "tymm_cerceveler": DOCS_TYMM / "cerceveler.json",
    "tymm_ilkokul_api": DOCS_TYMM / "ilkokul-turkce" / "api-response.json",
    "tymm_ortaokul_api": DOCS_TYMM / "ortaokul-turkce" / "api-response.json",
}

VENDOR_TURKIYEAPI = DOCS_DATA / "reference" / "turkiyeapi"
VENDOR_HDX = DOCS_DATA / "reference" / "hdx"
VENDOR_TUIK = DOCS_DATA / "reference" / "tuik"

SITE = {
    "turkiye_adres_il_ilce": ROOT / "_data" / "turkiye_adres_il_ilce.json",
    "okullar": ROOT / "assets" / "data" / "okullar.json",
    "geodata_dir": ROOT / "assets" / "data" / "geodata",
    "okullar_harita_dir": ROOT / "assets" / "data" / "okullar-harita",
    "tymm": ROOT / "_data" / "tymm.json",
}

# JSON meta alanlarında kullanılan repo-kök göreli yollar
REF_TURKIYE_ADRES = "docs/data/turkiye_adres.json"
REF_OKULLAR = "docs/data/okullar.json"
REF_POPULATION = "docs/data/population.json"
REF_TYMM_HAM = "docs/data/tymm/"
