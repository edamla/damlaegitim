#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HDX COD-AB → docs/data/turkiye_geodata.json (ülke + il + ilçe sınır poligonları)"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.request
import zipfile
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from data_paths import CANONICAL, VENDOR_HDX

ROOT = Path(__file__).resolve().parents[1]
ADRES_PATH = CANONICAL["turkiye_adres"]
OUTPUT_PATH = CANONICAL["turkiye_geodata"]
VENDOR_DIR = VENDOR_HDX

HDX_URL = (
    "https://data.humdata.org/dataset/cod-ab-tur/resource/"
    "470bd810-2240-4ce0-b5c4-17434112ce41/download/tur_admin_boundaries.geojson.zip"
)
ZIP_NAME = "tur_admin_boundaries.geojson.zip"
ZIP_SHA256 = "6d45f15de76d53da057312dfaedb60248141a1828ce6a5c7cbfeedc7f51714c3"

GEOJSON_MEMBERS = (
    "tur_admin0.geojson",
    "tur_admin1.geojson",
    "tur_admin2.geojson",
)

USER_AGENT = (
    "Mozilla/5.0 (compatible; damlaegitim-fetch-geodata/1.0; +https://damlaokul.com)"
)
MAX_RETRIES = 4
RETRY_BACKOFF = 2.0
DELAY_SEC = 0.3

TR_BBOX = (25.0, 35.5, 45.5, 42.5)


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
            "Â": "a",
            "â": "a",
            "Î": "i",
            "î": "i",
            "Û": "u",
            "û": "u",
        }
    )
    return text.translate(table).lower()


def strip_combining_marks(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn"
    )


def fold_match_key(text: str) -> str:
    """HDX / TurkiyeAPI ad eşleştirmesi (birleştirici işaret + ASCII katlama)."""
    folded = fold_tr(strip_combining_marks(text))
    folded = folded.translate(
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
    return re.sub(r"[^a-z0-9]+", "", folded)


def http_get(url: str, timeout: int = 300) -> bytes:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read()


def fetch_bytes(url: str) -> bytes:
    last_err: Optional[BaseException] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return http_get(url)
        except (urllib.error.URLError, TimeoutError, ssl.SSLError) as exc:
            last_err = exc
            wait = RETRY_BACKOFF * attempt
            print(f"  [WARN] {url} ({attempt}/{MAX_RETRIES}): {exc}; {wait:.1f}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"İstek başarısız: {url}") from last_err


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_zip_bytes(vendor_dir: Optional[Path]) -> bytes:
    local = (vendor_dir or VENDOR_DIR) / ZIP_NAME
    if vendor_dir and local.is_file():
        print(f"  yerel: {local}")
        return local.read_bytes()
    if vendor_dir is None and local.is_file():
        print(f"  önbellek: {local}")
        data = local.read_bytes()
        if sha256_bytes(data) == ZIP_SHA256:
            return data
        print("  [WARN] önbellek SHA-256 uyuşmuyor; yeniden indiriliyor", file=sys.stderr)
    print(f"  indiriliyor: {HDX_URL}")
    data = fetch_bytes(HDX_URL)
    time.sleep(DELAY_SEC)
    digest = sha256_bytes(data)
    if digest != ZIP_SHA256:
        raise RuntimeError(f"SHA-256 uyuşmuyor: beklenen={ZIP_SHA256}, gelen={digest}")
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_bytes(data)
    return data


def vendor_zip(vendor_dir: Path, data: bytes) -> None:
    vendor_dir.mkdir(parents=True, exist_ok=True)
    path = vendor_dir / ZIP_NAME
    path.write_bytes(data)
    print(f"  snapshot: {path}")


def read_geojson_member(zf: zipfile.ZipFile, member: str) -> Dict[str, Any]:
    if member not in zf.namelist():
        raise RuntimeError(f"ZIP içinde {member} yok")
    payload = json.loads(zf.read(member).decode("utf-8"))
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise RuntimeError(f"Beklenmeyen GeoJSON: {member}")
    return payload


def pcode_to_plate(pcode: str) -> int:
    code = (pcode or "").strip().upper()
    if code.startswith("TUR"):
        return int(code[3:])
    raise ValueError(f"Bilinmeyen il pcode: {pcode!r}")


def parse_center(props: Dict[str, Any]) -> Optional[List[float]]:
    lon = props.get("center_lon")
    lat = props.get("center_lat")
    if lon is None or lat is None:
        return None
    try:
        return [float(lon), float(lat)]
    except (TypeError, ValueError):
        return None


def bbox_from_coords(coords: Any, bbox: Optional[List[float]]) -> List[float]:
    if isinstance(coords, (int, float)):
        return bbox or []
    if len(coords) >= 2 and isinstance(coords[0], (int, float)):
        lon, lat = float(coords[0]), float(coords[1])
        if bbox is None:
            return [lon, lat, lon, lat]
        return [
            min(bbox[0], lon),
            min(bbox[1], lat),
            max(bbox[2], lon),
            max(bbox[3], lat),
        ]
    out = bbox
    for part in coords:
        out = bbox_from_coords(part, out)
    return out or []


def bbox_from_geometry(geometry: Dict[str, Any]) -> List[float]:
    coords = geometry.get("coordinates")
    if not coords:
        return []
    return bbox_from_coords(coords, None)


def validate_geometry(geometry: Dict[str, Any], label: str) -> None:
    gtype = geometry.get("type")
    if gtype not in ("Polygon", "MultiPolygon"):
        raise RuntimeError(f"{label}: desteklenmeyen geometri tipi {gtype!r}")
    bbox = bbox_from_geometry(geometry)
    if len(bbox) != 4:
        raise RuntimeError(f"{label}: bbox hesaplanamadı")
    min_lon, min_lat, max_lon, max_lat = bbox
    if not (TR_BBOX[0] <= min_lon <= TR_BBOX[2] and TR_BBOX[0] <= max_lon <= TR_BBOX[2]):
        raise RuntimeError(f"{label}: boylam Türkiye dışı {bbox}")
    if not (TR_BBOX[1] <= min_lat <= TR_BBOX[3] and TR_BBOX[1] <= max_lat <= TR_BBOX[3]):
        raise RuntimeError(f"{label}: enlem Türkiye dışı {bbox}")


def load_adres_indexes(path: Path) -> Tuple[Dict[int, Dict[str, Any]], Dict[Tuple[int, str], Dict[str, Any]], Dict[int, Dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    iller = data.get("iller")
    if not isinstance(iller, list):
        raise RuntimeError(f"Beklenmeyen adres şeması: {path}")

    il_by_kod: Dict[int, Dict[str, Any]] = {}
    ilce_by_key: Dict[Tuple[int, str], Dict[str, Any]] = {}
    merkez_by_il: Dict[int, Dict[str, Any]] = {}

    for il in iller:
        il_kod = int(il["kod"])
        il_by_kod[il_kod] = il
        for ilce in il.get("ilceler") or []:
            key = (il_kod, fold_match_key(ilce["ad"]))
            ilce_by_key[key] = ilce
            if fold_match_key(ilce["ad"]) == "merkez":
                merkez_by_il[il_kod] = ilce

    return il_by_kod, ilce_by_key, merkez_by_il


def resolve_ilce(
    il_kod: int,
    hdx_name: str,
    il_by_kod: Dict[int, Dict[str, Any]],
    ilce_by_key: Dict[Tuple[int, str], Dict[str, Any]],
    merkez_by_il: Dict[int, Dict[str, Any]],
) -> Dict[str, Any]:
    key = (il_kod, fold_match_key(hdx_name))
    ilce = ilce_by_key.get(key)
    if ilce:
        return ilce

    il_node = il_by_kod.get(il_kod)
    if il_node and fold_match_key(hdx_name) == fold_match_key(il_node["ad"]):
        merkez = merkez_by_il.get(il_kod)
        if merkez:
            return merkez

    raise KeyError(f"ilçe eşleşmedi: il={il_kod}, ad={hdx_name!r}")


def build_payload(
    admin0: Dict[str, Any],
    admin1: Dict[str, Any],
    admin2: Dict[str, Any],
    adres_path: Path,
) -> Dict[str, Any]:
    il_by_kod, ilce_by_key, merkez_by_il = load_adres_indexes(adres_path)

    iller_out: Dict[str, Dict[str, Any]] = {}
    for il in il_by_kod.values():
        kod = int(il["kod"])
        iller_out[str(kod)] = {
            "kod": kod,
            "ad": il["ad"],
            "ilceler": {},
        }

    matched_il = 0
    for feature in admin1.get("features") or []:
        props = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        pcode = props.get("adm1_pcode") or ""
        il_kod = pcode_to_plate(pcode)
        il_node = iller_out.get(str(il_kod))
        if not il_node:
            name = props.get("adm1_name1") or props.get("adm1_name") or ""
            for il in il_by_kod.values():
                if fold_match_key(il["ad"]) == fold_match_key(name):
                    il_kod = int(il["kod"])
                    il_node = iller_out[str(il_kod)]
                    break
        if not il_node:
            raise RuntimeError(f"HDX il eşleşmedi: {pcode} {props.get('adm1_name1')}")

        validate_geometry(geometry, f"il {il_kod}")
        il_node["pcode"] = pcode
        il_node["geometry"] = geometry
        il_node["bbox"] = bbox_from_geometry(geometry)
        center = parse_center(props)
        if center:
            il_node["merkez"] = center
        area = props.get("area_sqkm")
        if area is not None:
            il_node["alan_km2"] = area
        matched_il += 1

    matched_ilce = 0
    unmatched: List[str] = []
    for feature in admin2.get("features") or []:
        props = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        il_kod = pcode_to_plate(props.get("adm1_pcode") or "")
        hdx_name = props.get("adm2_name1") or props.get("adm2_name") or ""
        try:
            ilce = resolve_ilce(il_kod, hdx_name, il_by_kod, ilce_by_key, merkez_by_il)
        except KeyError:
            unmatched.append(f"{il_kod}:{hdx_name}")
            continue

        il_node = iller_out[str(il_kod)]
        ilce_kod = int(ilce["kod"])
        label = f"ilçe {il_kod}/{ilce_kod} {ilce['ad']}"
        validate_geometry(geometry, label)

        il_node["ilceler"][str(ilce_kod)] = {
            "kod": ilce_kod,
            "ad": ilce["ad"],
            "pcode": props.get("adm2_pcode"),
            "geometry": geometry,
            "bbox": bbox_from_geometry(geometry),
        }
        center = parse_center(props)
        if center:
            il_node["ilceler"][str(ilce_kod)]["merkez"] = center
        area = props.get("area_sqkm")
        if area is not None:
            il_node["ilceler"][str(ilce_kod)]["alan_km2"] = area
        matched_ilce += 1

    if unmatched:
        for line in unmatched[:20]:
            print(f"  [UYARI] eşleşmeyen ilçe: {line}", file=sys.stderr)
        raise RuntimeError(f"ilçe eşleşmesi başarısız: {len(unmatched)} kayıt")

    feats0 = admin0.get("features") or []
    if len(feats0) != 1:
        raise RuntimeError(f"ADM0 feature sayısı beklenmiyor: {len(feats0)}")
    ulke_props = feats0[0].get("properties") or {}
    ulke_geom = feats0[0].get("geometry") or {}
    validate_geometry(ulke_geom, "ülke")

    expected_il = len(il_by_kod)
    expected_ilce = sum(len(il.get("ilceler") or []) for il in il_by_kod.values())
    print(f"  doğrulama: 1 ülke, {matched_il} il, {matched_ilce} ilçe (beklenen {expected_il}/{expected_ilce})")
    if matched_il != expected_il or matched_ilce != expected_ilce:
        missing_il = [k for k, v in iller_out.items() if "geometry" not in v]
        missing_ilce = []
        for il_kod, il_node in iller_out.items():
            have = set(il_node["ilceler"])
            for ilce in il_by_kod[int(il_kod)]["ilceler"]:
                if str(ilce["kod"]) not in have:
                    missing_ilce.append(f"{il_kod}:{ilce['ad']}")
        if missing_il:
            print(f"  [UYARI] geometrisiz il: {missing_il}", file=sys.stderr)
        if missing_ilce:
            print(f"  [UYARI] geometrisiz ilçe (ilk 10): {missing_ilce[:10]}", file=sys.stderr)
        raise RuntimeError("il/ilçe geometri sayısı tam değil")

    valid_on = ulke_props.get("valid_on")
    return {
        "meta": {
            "kaynak": "https://data.humdata.org/dataset/cod-ab-tur",
            "kaynak_dosya": ZIP_NAME,
            "kaynak_url": HDX_URL,
            "lisans": "CC BY-IGO",
            "EPSG": 4326,
            "referans": str(adres_path.relative_to(ROOT)).replace("\\", "/"),
            "guncelleme": date.today().isoformat(),
            "valid_on": valid_on,
            "kaynak_inceleme": "2025-01-16",
            "katmanlar": ["ulke", "il", "ilce"],
            "sayi": {"ulke": 1, "il": matched_il, "ilce": matched_ilce},
        },
        "ulke": {
            "pcode": ulke_props.get("adm0_pcode"),
            "ad": ulke_props.get("adm0_name1") or ulke_props.get("adm0_name") or "Türkiye",
            "geometry": ulke_geom,
            "bbox": bbox_from_geometry(ulke_geom),
            **({"merkez": parse_center(ulke_props)} if parse_center(ulke_props) else {}),
            **({"alan_km2": ulke_props.get("area_sqkm")} if ulke_props.get("area_sqkm") is not None else {}),
        },
        "iller": iller_out,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="HDX COD-AB idari sınır verisini docs/data/turkiye_geodata.json olarak üretir"
    )
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--adres", type=Path, default=ADRES_PATH)
    parser.add_argument(
        "--vendor",
        type=Path,
        nargs="?",
        const=VENDOR_DIR,
        default=None,
        help="Ham ZIP dosyasını kaydet (docs/data/reference/hdx)",
    )
    parser.add_argument(
        "--from-vendor",
        type=Path,
        default=None,
        help="İndirme yerine bu klasördeki ZIP snapshot'ını kullan",
    )
    args = parser.parse_args(argv)

    if not args.adres.is_file():
        print(f"Hata: {args.adres} bulunamadı (önce fetch_turkiyeadres.py)", file=sys.stderr)
        return 1

    vendor_src = args.from_vendor
    zip_data = load_zip_bytes(vendor_src)
    if args.vendor:
        vendor_zip(args.vendor, zip_data)

    print("GeoJSON işleniyor…")
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        admin0 = read_geojson_member(zf, GEOJSON_MEMBERS[0])
        admin1 = read_geojson_member(zf, GEOJSON_MEMBERS[1])
        admin2 = read_geojson_member(zf, GEOJSON_MEMBERS[2])

    payload = build_payload(admin0, admin1, admin2, args.adres)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    size_mb = args.output.stat().st_size / (1024 * 1024)
    print(f"Yazıldı: {args.output} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
