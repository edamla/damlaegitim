#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TurkiyeAPI v2 → _data/turkiye_adres.json (il → ilçe → mahalle / köy)"""

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
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "_data" / "turkiye_adres.json"
VENDOR_DIR = ROOT / "_data" / "reference" / "turkiyeapi"

API_BASE = "https://api.turkiyeapi.dev/v2"
DATASETS = ("provinces.json", "districts.json", "neighborhoods.json", "villages.json")

USER_AGENT = (
    "Mozilla/5.0 (compatible; damlaegitim-fetch-turkiyeadres/1.0; +https://damlaokul.com)"
)
MAX_RETRIES = 4
RETRY_BACKOFF = 2.0
DELAY_SEC = 0.3


def fold_tr_key(text: str) -> str:
    return (text or "").casefold()


def http_get(url: str, timeout: int = 120) -> bytes:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
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


def fetch_meta() -> Dict[str, Any]:
    payload = fetch_json(f"{API_BASE}/meta")
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload if isinstance(payload, dict) else {}


def load_dataset(name: str, vendor_dir: Optional[Path]) -> List[Dict[str, Any]]:
    if vendor_dir:
        local = vendor_dir / name
        if local.is_file():
            print(f"  yerel: {local}")
            data = json.loads(local.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
    url = f"{API_BASE}/datasets/{name}"
    print(f"  indiriliyor: {url}")
    data = fetch_json(url)
    time.sleep(DELAY_SEC)
    if not isinstance(data, list):
        raise RuntimeError(f"Beklenmeyen dataset yanıtı: {name}")
    return data


def vendor_datasets(vendor_dir: Path, datasets: Dict[str, List[Dict[str, Any]]]) -> None:
    vendor_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in datasets.items():
        path = vendor_dir / name
        path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        print(f"  snapshot: {path}")


def build_tree(
    provinces: List[Dict[str, Any]],
    districts: List[Dict[str, Any]],
    neighborhoods: List[Dict[str, Any]],
    villages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    district_nodes: Dict[int, Dict[str, Any]] = {}
    province_nodes: Dict[int, Dict[str, Any]] = {}

    for prov in provinces:
        pid = int(prov["id"])
        province_nodes[pid] = {
            "kod": pid,
            "ad": prov["name"],
            "ilceler": [],
        }

    for dist in districts:
        did = int(dist["id"])
        pid = int(dist["provinceId"])
        if pid not in province_nodes:
            print(f"  [WARN] ilçe {did} için bilinmeyen il: {pid}", file=sys.stderr)
            continue
        node = {
            "kod": did,
            "ad": dist["name"],
            "mahalleler": [],
            "koyler": [],
        }
        district_nodes[did] = node
        province_nodes[pid]["ilceler"].append(node)

    orphan_mahalle = 0
    for nb in neighborhoods:
        did = int(nb["districtId"])
        target = district_nodes.get(did)
        if not target:
            orphan_mahalle += 1
            continue
        target["mahalleler"].append({"kod": int(nb["id"]), "ad": nb["name"]})

    orphan_koy = 0
    for vil in villages:
        did = int(vil["districtId"])
        target = district_nodes.get(did)
        if not target:
            orphan_koy += 1
            continue
        target["koyler"].append({"kod": int(vil["id"]), "ad": vil["name"]})

    if orphan_mahalle:
        print(f"  [WARN] eşleşmeyen mahalle: {orphan_mahalle}", file=sys.stderr)
    if orphan_koy:
        print(f"  [WARN] eşleşmeyen köy: {orphan_koy}", file=sys.stderr)

    iller = sorted(province_nodes.values(), key=lambda x: x["kod"])
    for il in iller:
        il["ilceler"].sort(key=lambda x: fold_tr_key(x["ad"]))
        for ilce in il["ilceler"]:
            ilce["mahalleler"].sort(key=lambda x: fold_tr_key(x["ad"]))
            ilce["koyler"].sort(key=lambda x: fold_tr_key(x["ad"]))
    return iller


def validate(
    iller: List[Dict[str, Any]],
    expected: Dict[str, int],
) -> None:
    il_count = len(iller)
    ilce_count = sum(len(il["ilceler"]) for il in iller)
    mahalle_count = sum(len(ilce["mahalleler"]) for il in iller for ilce in il["ilceler"])
    koy_count = sum(len(ilce["koyler"]) for il in iller for ilce in il["ilceler"])

    checks = {
        "il": il_count,
        "ilce": ilce_count,
        "mahalle": mahalle_count,
        "koy": koy_count,
    }
    print(
        f"  doğrulama: {il_count} il, {ilce_count} ilçe, "
        f"{mahalle_count} mahalle, {koy_count} köy"
    )
    for key, got in checks.items():
        want = expected.get(key)
        if want is not None and got != want:
            raise RuntimeError(f"{key} sayısı uyuşmuyor: beklenen={want}, üretilen={got}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="TurkiyeAPI v2 idari adres verisini _data/turkiye_adres.json olarak üretir"
    )
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument(
        "--vendor",
        type=Path,
        nargs="?",
        const=VENDOR_DIR,
        default=None,
        help="Ham dataset dosyalarını kaydet (_data/reference/turkiyeapi)",
    )
    parser.add_argument(
        "--from-vendor",
        type=Path,
        default=None,
        help="API yerine bu klasördeki snapshot dosyalarını kullan",
    )
    args = parser.parse_args(argv)

    print("TurkiyeAPI metadata…")
    meta_api = fetch_meta()
    dataset_version = meta_api.get("datasetVersion", "2025")
    last_updated = meta_api.get("lastUpdated")

    vendor_src = args.from_vendor
    raw: Dict[str, List[Dict[str, Any]]] = {}
    for name in DATASETS:
        raw[name] = load_dataset(name, vendor_src)

    if args.vendor:
        vendor_datasets(args.vendor, raw)

    provinces = raw["provinces.json"]
    districts = raw["districts.json"]
    neighborhoods = raw["neighborhoods.json"]
    villages = raw["villages.json"]

    print("Ağaç oluşturuluyor…")
    iller = build_tree(provinces, districts, neighborhoods, villages)
    validate(
        iller,
        {
            "il": len(provinces),
            "ilce": len(districts),
            "mahalle": len(neighborhoods),
            "koy": len(villages),
        },
    )

    payload = {
        "meta": {
            "kaynak": "https://docs.turkiyeapi.dev/tr/",
            "api": API_BASE,
            "datasetVersion": dataset_version,
            "guncelleme": date.today().isoformat(),
        },
        "iller": iller,
    }
    if last_updated:
        payload["meta"]["lastUpdated"] = last_updated

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Yazıldı: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
