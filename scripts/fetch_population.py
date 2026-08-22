#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TurkiyeAPI + TÜİK ADNKS → docs/data/population.json (il/ilçe nüfus ve çocuk sayıları)"""

from __future__ import annotations

import argparse
import csv
import json
import re
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from data_paths import CANONICAL, REF_POPULATION, REF_TURKIYE_ADRES, VENDOR_TUIK

ROOT = Path(__file__).resolve().parents[1]
ADRES_PATH = CANONICAL["turkiye_adres"]
OUTPUT_PATH = CANONICAL["population"]
VENDOR_DIR = VENDOR_TUIK

API_BASE = "https://api.turkiyeapi.dev/v2"
DATASETS = ("provinces.json", "districts.json")

USER_AGENT = (
    "Mozilla/5.0 (compatible; damlaegitim-fetch-population/1.0; +https://damlaokul.com)"
)
TUIK_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
MAX_RETRIES = 4
RETRY_BACKOFF = 2.0
DELAY_SEC = 0.3

EONER_ERKEK_URL = (
    "https://raw.githubusercontent.com/eoner/ADNKSVerileri/master/"
    "{year}_ilce_erkek_yas_combined.csv"
)
EONER_KADIN_URL = (
    "https://raw.githubusercontent.com/eoner/ADNKSVerileri/master/"
    "{year}_ilce_kadin_yas_combined.csv"
)

BANDS_0_14 = ("0-4", "5-9", "10-14")
BAND_15_17 = "15-17"
BAND_15_19 = "15-19"

IL_ALIASES = {
    "afyon": "Afyonkarahisar",
}

ILCE_ALIASES = {
    "ondokuzmayis": "19 mayıs",
    "19mayis": "19 mayıs",
    "dogubeyazit": "Doğubayazıt",
    "poturge": "Pütürge",
    "cagliyancerit": "Çağlayancerit",
    "kazan": "Kahramankazan",
    "eyup": "Eyüpsultan",
}


def fold_tr(text: str) -> str:
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
        }
    )
    return text.translate(table).casefold()


def fold_ascii(text: str) -> str:
    t = fold_tr(text).translate(
        str.maketrans(
            {
                "ş": "s",
                "ğ": "g",
                "ü": "u",
                "ö": "o",
                "ç": "c",
                "ı": "i",
            }
        )
    )
    return re.sub(r"[^a-z0-9]+", "", t)


def strip_combining_marks(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text or "") if unicodedata.category(c) != "Mn")


def fold_match_key(text: str) -> str:
    folded = fold_tr(strip_combining_marks(text))
    folded = folded.translate(
        str.maketrans(
            {
                "ş": "s",
                "ğ": "g",
                "ü": "u",
                "ö": "o",
                "ç": "c",
                "ı": "i",
            }
        )
    )
    folded = re.sub(r"[\s\-_'’.]+", "", folded)
    return re.sub(r"[^a-z0-9]+", "", folded)


def http_get(url: str, timeout: int = 120, user_agent: str = USER_AGENT) -> bytes:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json,text/csv,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read()


def fetch_json(url: str) -> Any:
    last_err: Optional[BaseException] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = http_get(url)
            return json.loads(raw.decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ssl.SSLError, json.JSONDecodeError) as exc:
            last_err = exc
            wait = RETRY_BACKOFF * attempt
            print(f"  [WARN] {url} ({attempt}/{MAX_RETRIES}): {exc}; {wait:.1f}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"İstek başarısız: {url}") from last_err


def download_file(url: str, dest: Path) -> None:
    last_err: Optional[BaseException] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = http_get(url, user_agent=TUIK_USER_AGENT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
            return
        except (urllib.error.URLError, TimeoutError, ssl.SSLError) as exc:
            last_err = exc
            wait = RETRY_BACKOFF * attempt
            print(f"  [WARN] {url} ({attempt}/{MAX_RETRIES}): {exc}; {wait:.1f}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"İndirme başarısız: {url}") from last_err


def load_dataset(name: str, vendor_dir: Optional[Path]) -> List[Dict[str, Any]]:
    if vendor_dir:
        local = vendor_dir / name
        if local.is_file():
            print(f"  vendor: {local}")
            return json.loads(local.read_text(encoding="utf-8"))
    url = f"{API_BASE}/datasets/{name}"
    print(f"  GET {url}")
    time.sleep(DELAY_SEC)
    payload = fetch_json(url)
    if not isinstance(payload, list):
        raise RuntimeError(f"Beklenmeyen dataset yanıtı: {name}")
    return payload


class AdresLookup:
    def __init__(self, adres: Dict[str, Any]) -> None:
        self.iller: List[Dict[str, Any]] = adres.get("iller") or []
        self.il_by_key: Dict[str, Tuple[int, str]] = {}
        self.ilce_by_key: Dict[Tuple[int, str], Tuple[int, str]] = {}
        for il in self.iller:
            il_kod = int(il["kod"])
            il_ad = il["ad"]
            for key in (fold_tr(il_ad), fold_ascii(il_ad), fold_match_key(il_ad)):
                self.il_by_key.setdefault(key, (il_kod, il_ad))
            for ilce in il.get("ilceler") or []:
                ilce_kod = int(ilce["kod"])
                ilce_ad = ilce["ad"]
                for key in (
                    fold_tr(ilce_ad),
                    fold_ascii(ilce_ad),
                    fold_match_key(ilce_ad),
                ):
                    self.ilce_by_key[(il_kod, key)] = (ilce_kod, ilce_ad)

    def resolve_il(self, name: str) -> Optional[Tuple[int, str]]:
        folded = fold_tr(name)
        ascii_name = fold_ascii(name)
        match_key = fold_match_key(name)
        for alias_key, alias_val in IL_ALIASES.items():
            if folded == fold_tr(alias_key) or ascii_name == alias_key:
                hit = self.il_by_key.get(fold_tr(alias_val)) or self.il_by_key.get(fold_ascii(alias_val))
                if hit:
                    return hit
        for key in (folded, ascii_name, match_key):
            hit = self.il_by_key.get(key)
            if hit:
                return hit
        return None

    def resolve_ilce(self, il_kod: int, name: str) -> Optional[Tuple[int, str]]:
        folded = fold_tr(name)
        ascii_name = fold_ascii(name)
        match_key = fold_match_key(name)
        for alias_key, alias_val in ILCE_ALIASES.items():
            if fold_tr(name) == fold_tr(alias_key) or fold_ascii(name) == alias_key:
                folded = fold_tr(alias_val)
                ascii_name = fold_ascii(alias_val)
                match_key = fold_match_key(alias_val)
                break
        for key in (folded, ascii_name, match_key):
            hit = self.ilce_by_key.get((il_kod, key))
            if hit:
                return hit
        return None


def parse_int(value: Any) -> int:
    if value is None:
        return 0
    text = str(value).strip().replace(".", "").replace(",", "")
    if not text:
        return 0
    return int(float(text))


def is_age_band(header: str) -> bool:
    return bool(re.fullmatch(r"\d{1,3}-\d{1,3}", header.strip())) or header.strip() in ("90+", "100+")


def is_single_age(header: str) -> bool:
    return header.strip().isdigit()


def sum_bands(row: Dict[str, str], bands: Tuple[str, ...]) -> int:
    total = 0
    for band in bands:
        if band in row:
            total += parse_int(row.get(band))
    return total


def compute_cocuk_from_bands(bands: Dict[str, int]) -> Tuple[int, int, str]:
    cocuk_0_14 = sum(bands.get(b, 0) for b in BANDS_0_14)
    note_parts: List[str] = []
    if BAND_15_17 in bands:
        cocuk_0_17 = cocuk_0_14 + bands[BAND_15_17]
    elif BAND_15_19 in bands:
        share = round(bands[BAND_15_19] * 3 / 5)
        cocuk_0_17 = cocuk_0_14 + share
        note_parts.append("0_17:15-19_oran")
    else:
        cocuk_0_17 = cocuk_0_14
        note_parts.append("0_17:15-19_yok")
    return cocuk_0_14, cocuk_0_17, ",".join(note_parts)


def compute_cocuk_from_ages(ages: Dict[int, int]) -> Tuple[int, int, str]:
    cocuk_0_14 = sum(ages.get(a, 0) for a in range(15))
    cocuk_0_17 = sum(ages.get(a, 0) for a in range(18))
    return cocuk_0_14, cocuk_0_17, ""


def parse_band_csv(path: Path) -> Dict[Tuple[str, str], Dict[str, int]]:
    rows: Dict[Tuple[str, str], Dict[str, int]] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise RuntimeError(f"Boş CSV: {path}")
        for raw in reader:
            il_name = (raw.get("Il") or raw.get("il") or raw.get("IL") or "").strip()
            ilce_name = (raw.get("Ilce") or raw.get("ilce") or raw.get("ILCE") or "").strip()
            if not il_name or not ilce_name:
                continue
            key = (il_name, ilce_name)
            bucket = rows.setdefault(key, {})
            for col, val in raw.items():
                if col in ("Il", "il", "IL", "Ilce", "ilce", "ILCE"):
                    continue
                header = (col or "").strip()
                if is_age_band(header) or header in ("90+", "100+"):
                    bucket[header] = bucket.get(header, 0) + parse_int(val)
    return rows


def parse_tidy_csv(path: Path) -> Dict[Tuple[str, str], Dict[str, Any]]:
    ages_by_place: Dict[Tuple[str, str], Dict[int, int]] = {}
    bands_by_place: Dict[Tuple[str, str], Dict[str, int]] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise RuntimeError(f"Boş CSV: {path}")
        fields = {fold_tr(h): h for h in reader.fieldnames if h}
        il_col = fields.get("il")
        ilce_col = fields.get("ilce") or fields.get("ilçe")
        yas_col = fields.get("yas") or fields.get("yaş")
        nufus_col = fields.get("nufus") or fields.get("nüfus")
        if not il_col or not ilce_col:
            raise RuntimeError(f"il/ilce sütunu bulunamadı: {path}")
        for raw in reader:
            il_name = (raw.get(il_col) or "").strip()
            ilce_name = (raw.get(ilce_col) or "").strip()
            if not il_name or not ilce_name:
                continue
            key = (il_name, ilce_name)
            if yas_col and nufus_col:
                age = parse_int(raw.get(yas_col))
                ages = ages_by_place.setdefault(key, {})
                ages[age] = ages.get(age, 0) + parse_int(raw.get(nufus_col))
            else:
                bucket = bands_by_place.setdefault(key, {})
                for col, val in raw.items():
                    if col in (il_col, ilce_col):
                        continue
                    header = (col or "").strip()
                    if is_age_band(header) or is_single_age(header):
                        if is_single_age(header):
                            ages = ages_by_place.setdefault(key, {})
                            ages[int(header)] = ages.get(int(header), 0) + parse_int(val)
                        else:
                            bucket[header] = bucket.get(header, 0) + parse_int(val)

    out: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for key, ages in ages_by_place.items():
        c14, c17, note = compute_cocuk_from_ages(ages)
        out[key] = {"cocuk_0_14": c14, "cocuk_0_17": c17, "note": note}
    for key, bands in bands_by_place.items():
        if key in out:
            continue
        c14, c17, note = compute_cocuk_from_bands(bands)
        out[key] = {"cocuk_0_14": c14, "cocuk_0_17": c17, "note": note}
    return out


def merge_band_pair(erkek: Dict[Tuple[str, str], Dict[str, int]], kadin: Dict[Tuple[str, str], Dict[str, int]]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    keys = set(erkek) | set(kadin)
    out: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for key in keys:
        merged: Dict[str, int] = {}
        for src in (erkek.get(key, {}), kadin.get(key, {})):
            for band, val in src.items():
                merged[band] = merged.get(band, 0) + val
        c14, c17, note = compute_cocuk_from_bands(merged)
        out[key] = {"cocuk_0_14": c14, "cocuk_0_17": c17, "note": note}
    return out


def find_vendor_files(vendor_dir: Path, yil: int) -> Tuple[str, List[Path]]:
    tidy = vendor_dir / f"adnks_il_ilce_yas_{yil}.csv"
    if tidy.is_file():
        return "tidy", [tidy]
    erkek_names = (
        vendor_dir / f"adnks_il_ilce_yas_{yil}_erkek.csv",
        vendor_dir / f"{yil}_ilce_erkek_yas_combined.csv",
    )
    kadin_names = (
        vendor_dir / f"adnks_il_ilce_yas_{yil}_kadin.csv",
        vendor_dir / f"{yil}_ilce_kadin_yas_combined.csv",
    )
    erkek = next((p for p in erkek_names if p.is_file()), None)
    kadin = next((p for p in kadin_names if p.is_file()), None)
    if erkek and kadin:
        return "band_pair", [erkek, kadin]
    raise FileNotFoundError(
        f"TÜİK vendor dosyası bulunamadı ({vendor_dir}, yıl={yil}). "
        f"Beklenen: {tidy.name} veya erkek+kadin CSV çifti."
    )


def bootstrap_vendor(vendor_dir: Path, yil: int) -> None:
    erkek_dest = vendor_dir / f"{yil}_ilce_erkek_yas_combined.csv"
    kadin_dest = vendor_dir / f"{yil}_ilce_kadin_yas_combined.csv"
    if erkek_dest.is_file() and kadin_dest.is_file():
        print(f"  vendor mevcut: {erkek_dest.name}, {kadin_dest.name}")
        return
    print(f"TÜİK vendor indiriliyor (eoner/ADNKSVerileri {yil})…")
    download_file(EONER_ERKEK_URL.format(year=yil), erkek_dest)
    download_file(EONER_KADIN_URL.format(year=yil), kadin_dest)


def load_cocuk_vendor(vendor_dir: Path, yil: int) -> Tuple[Dict[Tuple[int, int], Dict[str, Any]], List[Dict[str, str]], str]:
    mode, paths = find_vendor_files(vendor_dir, yil)
    if mode == "tidy":
        raw = parse_tidy_csv(paths[0])
    else:
        erkek = parse_band_csv(paths[0])
        kadin = parse_band_csv(paths[1])
        raw = merge_band_pair(erkek, kadin)

    lookup = AdresLookup(json.loads(ADRES_PATH.read_text(encoding="utf-8")))
    mapped: Dict[Tuple[int, int], Dict[str, Any]] = {}
    unmatched: List[Dict[str, str]] = []
    for (il_name, ilce_name), stats in raw.items():
        il_hit = lookup.resolve_il(il_name)
        if not il_hit:
            unmatched.append({"il": il_name, "ilce": ilce_name, "neden": "il_eslesmedi"})
            continue
        il_kod, _il_ad = il_hit
        ilce_hit = lookup.resolve_ilce(il_kod, ilce_name)
        if not ilce_hit:
            unmatched.append({"il": il_name, "ilce": ilce_name, "neden": "ilce_eslesmedi"})
            continue
        ilce_kod, _ilce_ad = ilce_hit
        mapped[(il_kod, ilce_kod)] = stats
    return mapped, unmatched, mode


def fetch_toplam_nufus(vendor_dir: Optional[Path]) -> Tuple[Dict[int, int], Dict[Tuple[int, int], int], str, Optional[str]]:
    provinces = load_dataset("provinces.json", vendor_dir)
    districts = load_dataset("districts.json", vendor_dir)
    il_nufus: Dict[int, int] = {}
    ilce_nufus: Dict[Tuple[int, int], int] = {}
    for prov in provinces:
        il_nufus[int(prov["id"])] = int(prov.get("population") or 0)
    for dist in districts:
        ilce_nufus[(int(dist["provinceId"]), int(dist["id"]))] = int(dist.get("population") or 0)
    dataset_version = "2025"
    last_updated: Optional[str] = None
    try:
        meta = fetch_json(f"{API_BASE}/meta")
        if isinstance(meta, dict) and "data" in meta:
            meta = meta["data"]
        if isinstance(meta, dict):
            dataset_version = str(meta.get("datasetVersion") or dataset_version)
            last_updated = meta.get("lastUpdated")
    except RuntimeError:
        pass
    return il_nufus, ilce_nufus, dataset_version, last_updated


def impute_missing_ilceler(
    cocuk: Dict[Tuple[int, int], Dict[str, Any]],
    il_nufus: Dict[int, int],
    ilce_nufus: Dict[Tuple[int, int], int],
    adres: Dict[str, Any],
) -> Tuple[Dict[Tuple[int, int], Dict[str, Any]], List[Dict[str, Any]]]:
    imputed: List[Dict[str, Any]] = []
    out = dict(cocuk)
    for il in adres.get("iller") or []:
        il_kod = int(il["kod"])
        known_14 = 0
        known_17 = 0
        known_nufus = 0
        missing_keys: List[Tuple[int, int, str]] = []
        for ilce in il.get("ilceler") or []:
            ilce_kod = int(ilce["kod"])
            key = (il_kod, ilce_kod)
            if key in out:
                known_14 += out[key]["cocuk_0_14"]
                known_17 += out[key]["cocuk_0_17"]
                known_nufus += ilce_nufus.get(key, 0)
            else:
                missing_keys.append((il_kod, ilce_kod, ilce["ad"]))
        if not missing_keys or known_nufus <= 0:
            continue
        ratio_14 = known_14 / known_nufus
        ratio_17 = known_17 / known_nufus
        for il_k, ilce_k, ilce_ad in missing_keys:
            nufus = ilce_nufus.get((il_k, ilce_k), 0)
            if nufus <= 0:
                continue
            c14 = max(1, round(nufus * ratio_14))
            c17 = max(c14, round(nufus * ratio_17))
            out[(il_k, ilce_k)] = {
                "cocuk_0_14": c14,
                "cocuk_0_17": c17,
                "note": "impute_il_oran",
            }
            imputed.append(
                {
                    "il_kod": il_k,
                    "ilce_kod": ilce_k,
                    "ilce_ad": ilce_ad,
                    "yontem": "il_ici_kardes_oran",
                }
            )
    return out, imputed


def build_payload(
    yil: int,
    dataset_version: str,
    last_updated: Optional[str],
    vendor_mode: str,
    vendor_yil: int,
    il_nufus: Dict[int, int],
    ilce_nufus: Dict[Tuple[int, int], int],
    cocuk_map: Dict[Tuple[int, int], Dict[str, Any]],
    unmatched: List[Dict[str, str]],
    imputed: List[Dict[str, Any]],
) -> Dict[str, Any]:
    adres = json.loads(ADRES_PATH.read_text(encoding="utf-8"))
    turkiye_nufus = 0
    turkiye_c14 = 0
    turkiye_c17 = 0
    iller_out: Dict[str, Any] = {}

    for il in adres.get("iller") or []:
        il_kod = int(il["kod"])
        il_key = str(il_kod)
        il_node: Dict[str, Any] = {
            "kod": il_kod,
            "ad": il["ad"],
            "nufus": il_nufus.get(il_kod, 0),
            "cocuk_0_14": 0,
            "cocuk_0_17": 0,
            "ilceler": {},
        }
        sum_c14 = 0
        sum_c17 = 0
        for ilce in il.get("ilceler") or []:
            ilce_kod = int(ilce["kod"])
            key = (il_kod, ilce_kod)
            cocuk = cocuk_map.get(key)
            if not cocuk:
                raise RuntimeError(f"Çocuk verisi eksik: {il['ad']} / {ilce['ad']} ({il_kod}/{ilce_kod})")
            nufus = ilce_nufus.get(key, 0)
            c14 = int(cocuk["cocuk_0_14"])
            c17 = int(cocuk["cocuk_0_17"])
            il_node["ilceler"][str(ilce_kod)] = {
                "kod": ilce_kod,
                "ad": ilce["ad"],
                "nufus": nufus,
                "cocuk_0_14": c14,
                "cocuk_0_17": c17,
            }
            sum_c14 += c14
            sum_c17 += c17
        il_node["cocuk_0_14"] = sum_c14
        il_node["cocuk_0_17"] = sum_c17
        iller_out[il_key] = il_node
        turkiye_nufus += il_node["nufus"]
        turkiye_c14 += sum_c14
        turkiye_c17 += sum_c17

    meta: Dict[str, Any] = {
        "kaynak": {
            "toplam_nufus": "https://api.turkiyeapi.dev/v2 (TÜİK MEDAS)",
            "cocuk_nufus": "TÜİK ADNKS — il/ilçe yaş-cinsiyet tablosu (vendor CSV)",
        },
        "referans": REF_TURKIYE_ADRES,
        "yil": yil,
        "vendor_yil": vendor_yil,
        "vendor_mode": vendor_mode,
        "datasetVersion": dataset_version,
        "guncelleme": date.today().isoformat(),
        "tanimlar": {
            "cocuk_0_14": "ADNKS yaş bağımlılık oranı çocuk tanımı (0–14)",
            "cocuk_0_17": "BM / İstatistiklerle Çocuk tanımı (0–17)",
        },
    }
    if last_updated:
        meta["lastUpdated"] = last_updated
    if unmatched:
        meta["eslesmeyen"] = unmatched
    if imputed:
        meta["impute_edilen_ilceler"] = imputed

    return {
        "meta": meta,
        "turkiye": {
            "nufus": turkiye_nufus,
            "cocuk_0_14": turkiye_c14,
            "cocuk_0_17": turkiye_c17,
        },
        "iller": iller_out,
    }


def validate_payload(payload: Dict[str, Any]) -> None:
    adres = json.loads(ADRES_PATH.read_text(encoding="utf-8"))
    expected_il = len(adres.get("iller") or [])
    expected_ilce = sum(len(il.get("ilceler") or []) for il in adres.get("iller") or [])
    iller = payload.get("iller") or {}
    if len(iller) != expected_il:
        raise RuntimeError(f"İl sayısı uyuşmuyor: {len(iller)} != {expected_il}")
    ilce_count = sum(len(il.get("ilceler") or {}) for il in iller.values())
    if ilce_count != expected_ilce:
        raise RuntimeError(f"İlçe sayısı uyuşmuyor: {ilce_count} != {expected_ilce}")

    for il_kod, il in iller.items():
        il_nufus = int(il.get("nufus") or 0)
        sum_ilce_nufus = 0
        sum_c14 = 0
        sum_c17 = 0
        for ilce in (il.get("ilceler") or {}).values():
            nufus = int(ilce.get("nufus") or 0)
            c14 = int(ilce.get("cocuk_0_14") or 0)
            c17 = int(ilce.get("cocuk_0_17") or 0)
            if nufus <= 0:
                raise RuntimeError(f"nufus <= 0: il={il_kod} ilce={ilce.get('kod')}")
            if c14 <= 0 or c17 <= 0:
                raise RuntimeError(f"çocuk <= 0: il={il_kod} ilce={ilce.get('kod')}")
            if not (c14 <= c17 <= nufus):
                raise RuntimeError(
                    f"cocuk_0_14 <= cocuk_0_17 <= nufus ihlali: "
                    f"il={il_kod} ilce={ilce.get('kod')} ({c14}/{c17}/{nufus})"
                )
            sum_ilce_nufus += nufus
            sum_c14 += c14
            sum_c17 += c17
        if abs(sum_ilce_nufus - il_nufus) > max(2, round(il_nufus * 0.002)):
            print(
                f"  [WARN] il {il_kod} nufus toplamı ilçe toplamından farklı: "
                f"il={il_nufus} ilce_toplam={sum_ilce_nufus}",
                file=sys.stderr,
            )
        if abs(sum_c14 - int(il.get("cocuk_0_14") or 0)) > 2:
            raise RuntimeError(f"İl cocuk_0_14 toplamı uyuşmuyor: il={il_kod}")
        if abs(sum_c17 - int(il.get("cocuk_0_17") or 0)) > 2:
            raise RuntimeError(f"İl cocuk_0_17 toplamı uyuşmuyor: il={il_kod}")

    print(f"  doğrulama: {expected_il} il, {expected_ilce} ilçe OK")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="TurkiyeAPI + TÜİK ADNKS vendor → docs/data/population.json"
    )
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--yil", type=int, default=2024, help="Meta yıl (ADNKS referans yılı)")
    parser.add_argument(
        "--vendor-yil",
        type=int,
        default=None,
        help="TÜİK vendor dosya yılı (varsayılan: --yil)",
    )
    parser.add_argument(
        "--tuik-vendor",
        type=Path,
        default=VENDOR_DIR,
        help="TÜİK ADNKS vendor CSV klasörü",
    )
    parser.add_argument(
        "--turkiyeapi-vendor",
        type=Path,
        default=None,
        help="TurkiyeAPI snapshot (docs/data/reference/turkiyeapi)",
    )
    parser.add_argument(
        "--bootstrap-vendor",
        action="store_true",
        help="eoner/ADNKSVerileri GitHub'dan vendor CSV indir (yalnızca 2013–2014)",
    )
    parser.add_argument(
        "--impute-new-ilce",
        action="store_true",
        help="Vendor'da olmayan yeni ilçeler için il içi kardeş oran ile çocuk nüfus tahmini",
    )
    args = parser.parse_args(argv)

    if not ADRES_PATH.is_file():
        raise SystemExit(f"Önkoşul eksik: {ADRES_PATH}")

    vendor_yil = args.vendor_yil if args.vendor_yil is not None else args.yil
    vendor_dir = args.tuik_vendor
    vendor_dir.mkdir(parents=True, exist_ok=True)

    if args.bootstrap_vendor:
        if vendor_yil not in (2013, 2014):
            raise SystemExit("--bootstrap-vendor yalnızca 2013 veya 2014 için desteklenir")
        bootstrap_vendor(vendor_dir, vendor_yil)

    print("TurkiyeAPI toplam nüfus…")
    il_nufus, ilce_nufus, dataset_version, last_updated = fetch_toplam_nufus(args.turkiyeapi_vendor)

    print(f"TÜİK çocuk nüfusu (vendor yıl={vendor_yil})…")
    cocuk_map, unmatched, vendor_mode = load_cocuk_vendor(vendor_dir, vendor_yil)
    if unmatched:
        print(f"  [WARN] eşleşmeyen vendor satırı: {len(unmatched)}", file=sys.stderr)

    imputed: List[Dict[str, Any]] = []
    if args.impute_new_ilce:
        adres_data = json.loads(ADRES_PATH.read_text(encoding="utf-8"))
        cocuk_map, imputed = impute_missing_ilceler(cocuk_map, il_nufus, ilce_nufus, adres_data)
        if imputed:
            print(f"  impute edilen ilçe: {len(imputed)}", file=sys.stderr)

    payload = build_payload(
        yil=args.yil,
        dataset_version=dataset_version,
        last_updated=last_updated,
        vendor_mode=vendor_mode,
        vendor_yil=vendor_yil,
        il_nufus=il_nufus,
        ilce_nufus=ilce_nufus,
        cocuk_map=cocuk_map,
        unmatched=unmatched,
        imputed=imputed,
    )
    validate_payload(payload)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Yazıldı: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
