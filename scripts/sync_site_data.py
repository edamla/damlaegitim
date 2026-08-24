#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""docs/data kanonik JSON → site türetilmiş dosyalar (_data, assets/data)."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from data_paths import CANONICAL, ROOT, SITE

# Eski mimariden kalan büyük JSON'lar — Jekyll _data/*.json olarak yükler, build kırılır
STALE_DATA_FILES = (
    ROOT / "_data" / "okullar_detay.json",
    ROOT / "_data" / "okullar.json",
    ROOT / "_data" / "turkiye_adres.json",
    ROOT / "_data" / "turkiye_geodata.json",
)

DETAY_FIELDS = (
    "telefon",
    "belgegecer",
    "adres",
    "eposta",
    "enlem",
    "boylam",
    "harita_url",
    "ogrenci_sayisi",
    "ogretmen_sayisi",
    "derslik_sayisi",
    "mudur",
)


def slim_il_ilce(adres_path: Path) -> Dict[str, Any]:
    data = json.loads(adres_path.read_text(encoding="utf-8"))
    iller = data.get("iller")
    if not isinstance(iller, list):
        raise RuntimeError(f"Beklenmeyen adres şeması: {adres_path}")

    slim_iller: List[Dict[str, Any]] = []
    for il in iller:
        ilce_list: List[Dict[str, Any]] = []
        for ilce in il.get("ilceler") or []:
            ilce_list.append({"kod": ilce["kod"], "ad": ilce["ad"]})
        slim_iller.append({"kod": il["kod"], "ad": il["ad"], "ilceler": ilce_list})

    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    return {
        "meta": {
            "kaynak": meta.get("kaynak"),
            "guncelleme": meta.get("guncelleme"),
            "referans": str(adres_path.relative_to(ROOT)).replace("\\", "/"),
        },
        "iller": slim_iller,
    }


def _okul_sayilari(okullar: Dict[str, Any]) -> Tuple[Dict[str, int], Dict[Tuple[str, str], int]]:
    il_counts: Dict[str, int] = {}
    ilce_counts: Dict[Tuple[str, str], int] = {}
    iller = okullar.get("iller")
    if not isinstance(iller, dict):
        return il_counts, ilce_counts
    for il_kod, il in iller.items():
        total = 0
        for ilce_kod, ilce in (il.get("ilceler") or {}).items():
            n = len(ilce.get("kurumlar") or [])
            ilce_counts[(str(il_kod), str(ilce_kod))] = n
            total += n
        il_counts[str(il_kod)] = total
    return il_counts, ilce_counts


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def cleanup_stale_data() -> int:
    """Eski _data büyük JSON kalıntılarını sil (Jekyll site.data yüklemesini önler)."""
    removed = 0
    for path in STALE_DATA_FILES:
        if not path.is_file():
            continue
        path.unlink()
        print(f"Silindi (eski kalıntı): {path.relative_to(ROOT)}")
        removed += 1
    return removed


def _kurum_il_index(okullar: Dict[str, Any]) -> Dict[str, str]:
    """kurum_kodu → il_kod (okullar.json üzerinden)."""
    index: Dict[str, str] = {}
    iller = okullar.get("iller")
    if not isinstance(iller, dict):
        return index
    for il_kod, il in iller.items():
        il_kod_s = str(il_kod)
        if not isinstance(il, dict):
            continue
        for ilce in (il.get("ilceler") or {}).values():
            if not isinstance(ilce, dict):
                continue
            for kurum in ilce.get("kurumlar") or []:
                if not isinstance(kurum, dict):
                    continue
                kod = kurum.get("kurum_kodu")
                if kod:
                    index[str(kod)] = il_kod_s
    return index


def _bucket_detay_by_il(
    detay_path: Path,
    kurum_il: Dict[str, str],
) -> Dict[str, Dict[str, Any]]:
    """Monolit okullar_detay.json → il_kod → { kurum_kodu → detay }."""
    detay_root = json.loads(detay_path.read_text(encoding="utf-8"))
    kurumlar = detay_root.get("kurumlar") or {}
    if not isinstance(kurumlar, dict):
        kurumlar = {}

    by_il: Dict[str, Dict[str, Any]] = {}
    orphan = 0
    for kod, detay in kurumlar.items():
        if not isinstance(detay, dict):
            continue
        il_kod = kurum_il.get(str(kod))
        if not il_kod:
            orphan += 1
            continue
        by_il.setdefault(il_kod, {})[str(kod)] = detay

    if orphan:
        print(
            f"  [UYARI] detay: {orphan} kurum okullar.json'da eşleşmedi (atlandı)",
            file=sys.stderr,
        )
    return by_il


def sync_geodata_chunks(geodata_path: Path, okullar_path: Path, out_dir: Path) -> int:
    geodata = json.loads(geodata_path.read_text(encoding="utf-8"))
    okullar = json.loads(okullar_path.read_text(encoding="utf-8"))
    il_counts, ilce_counts = _okul_sayilari(okullar)

    ulke = geodata.get("ulke") or {}
    index_iller: List[Dict[str, Any]] = []
    il_dir = out_dir / "il"
    iller = geodata.get("iller") or {}

    for il_kod, il in iller.items():
        il_kod_s = str(il_kod)
        ilce_out: Dict[str, Any] = {}
        for ilce_kod, ilce in (il.get("ilceler") or {}).items():
            ilce_kod_s = str(ilce_kod)
            ilce_out[ilce_kod_s] = {
                "kod": ilce.get("kod", ilce_kod),
                "ad": ilce.get("ad"),
                "pcode": ilce.get("pcode"),
                "geometry": ilce.get("geometry"),
                "bbox": ilce.get("bbox"),
                "merkez": ilce.get("merkez"),
                "okul_sayisi": ilce_counts.get((il_kod_s, ilce_kod_s), 0),
            }

        il_payload = {
            "kod": il.get("kod", il_kod),
            "ad": il.get("ad"),
            "pcode": il.get("pcode"),
            "geometry": il.get("geometry"),
            "bbox": il.get("bbox"),
            "merkez": il.get("merkez"),
            "alan_km2": il.get("alan_km2"),
            "okul_sayisi": il_counts.get(il_kod_s, 0),
            "ilceler": ilce_out,
        }
        _write_json(il_dir / f"{il_kod_s}.json", il_payload)

        index_iller.append(
            {
                "kod": il_payload["kod"],
                "ad": il_payload["ad"],
                "bbox": il_payload.get("bbox"),
                "merkez": il_payload.get("merkez"),
                "okul_sayisi": il_payload["okul_sayisi"],
                "geometry": il_payload.get("geometry"),
            }
        )

    index_iller.sort(key=lambda x: int(x["kod"]) if str(x["kod"]).isdigit() else 0)
    meta = geodata.get("meta") if isinstance(geodata.get("meta"), dict) else {}
    index = {
        "meta": {
            "referans": str(geodata_path.relative_to(ROOT)).replace("\\", "/"),
            "guncelleme": date.today().isoformat(),
            "kaynak": meta.get("kaynak"),
            "lisans": meta.get("lisans"),
        },
        "ulke": {
            "ad": ulke.get("ad"),
            "bbox": ulke.get("bbox"),
            "geometry": ulke.get("geometry"),
        },
        "iller": index_iller,
    }
    _write_json(out_dir / "index.json", index)
    return len(index_iller)


def _merge_kurum(
    kurum: Dict[str, Any],
    il_kod: str,
    il_ad: str,
    ilce_kod: str,
    ilce_ad: str,
    detay_map: Dict[str, Any],
) -> Dict[str, Any]:
    rec: Dict[str, Any] = {
        "ilce_kod": ilce_kod,
        "ilce_ad": ilce_ad,
        "ad": kurum.get("ad"),
        "tur": kurum.get("tur"),
    }
    if kurum.get("ozel"):
        rec["ozel"] = True
        if kurum.get("adres"):
            rec["adres"] = kurum["adres"]
        if kurum.get("telefon"):
            rec["telefon"] = kurum["telefon"]
        return rec

    kod = kurum.get("kurum_kodu")
    if kod:
        rec["kurum_kodu"] = kod
    if kurum.get("web"):
        rec["web"] = kurum["web"]

    detay = detay_map.get(str(kod)) if kod else None
    if isinstance(detay, dict):
        for key in DETAY_FIELDS:
            val = detay.get(key)
            if val is not None and val != "":
                rec[key] = val
        if rec.get("adres") is None and kurum.get("adres"):
            rec["adres"] = kurum["adres"]
        if rec.get("telefon") is None and kurum.get("telefon"):
            rec["telefon"] = kurum["telefon"]
    else:
        if kurum.get("adres"):
            rec["adres"] = kurum["adres"]
        if kurum.get("telefon"):
            rec["telefon"] = kurum["telefon"]
    return rec


def sync_okullar_harita(
    okullar_path: Path,
    detay_path: Path,
    out_dir: Path,
) -> Tuple[int, int]:
    okullar = json.loads(okullar_path.read_text(encoding="utf-8"))
    kurum_il = _kurum_il_index(okullar)
    detay_by_il = _bucket_detay_by_il(detay_path, kurum_il)

    tur_set: Set[str] = set()
    total = 0
    coords = 0
    iller = okullar.get("iller") or {}

    for il_kod, il in iller.items():
        il_kod_s = str(il_kod)
        detay_map = detay_by_il.get(il_kod_s, {})
        kurumlar: List[Dict[str, Any]] = []
        for ilce_kod, ilce in (il.get("ilceler") or {}).items():
            ilce_kod_s = str(ilce_kod)
            ilce_ad = ilce.get("ad", "")
            for kurum in ilce.get("kurumlar") or []:
                merged = _merge_kurum(
                    kurum, il_kod_s, il.get("ad", ""), ilce_kod_s, ilce_ad, detay_map
                )
                kurumlar.append(merged)
                total += 1
                if kurum.get("tur"):
                    tur_set.add(str(kurum["tur"]))
                if merged.get("enlem") is not None and merged.get("boylam") is not None:
                    coords += 1

        kurumlar.sort(key=lambda k: (k.get("ilce_ad") or "", k.get("ad") or ""))
        payload = {
            "il_kod": il_kod_s,
            "il_ad": il.get("ad"),
            "kurumlar": kurumlar,
        }
        _write_json(out_dir / f"{il_kod_s}.json", payload)

    meta = {
        "referans_okullar": str(okullar_path.relative_to(ROOT)).replace("\\", "/"),
        "referans_detay": str(detay_path.relative_to(ROOT)).replace("\\", "/"),
        "guncelleme": date.today().isoformat(),
        "sayi": total,
        "koordinatli": coords,
        "turler": sorted(tur_set),
    }
    _write_json(out_dir / "meta.json", meta)
    return total, coords


def sync(strict: bool = False) -> int:
    warnings: List[str] = []
    wrote = 0

    cleanup_stale_data()

    adres_src = CANONICAL["turkiye_adres"]
    il_ilce_dst = SITE["turkiye_adres_il_ilce"]
    if adres_src.is_file():
        slim = slim_il_ilce(adres_src)
        il_ilce_dst.parent.mkdir(parents=True, exist_ok=True)
        il_ilce_dst.write_text(
            json.dumps(slim, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        size_kb = il_ilce_dst.stat().st_size / 1024
        print(f"Yazıldı: {il_ilce_dst} ({size_kb:.0f} KB, {len(slim['iller'])} il)")
        wrote += 1
    else:
        warnings.append(f"kaynak yok: {adres_src}")

    okullar_src = CANONICAL["okullar"]
    okullar_dst = SITE["okullar"]
    if okullar_src.is_file():
        okullar_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(okullar_src, okullar_dst)
        size_mb = okullar_dst.stat().st_size / (1024 * 1024)
        print(f"Kopyalandı: {okullar_dst} ({size_mb:.1f} MB)")
        wrote += 1
    else:
        warnings.append(f"kaynak yok: {okullar_src}")

    geodata_src = CANONICAL["turkiye_geodata"]
    geodata_dir = SITE["geodata_dir"]
    if geodata_src.is_file() and okullar_src.is_file():
        n_il = sync_geodata_chunks(geodata_src, okullar_src, geodata_dir)
        print(f"Yazıldı: {geodata_dir}/index.json + {n_il} il parçası")
        wrote += 1
    else:
        if not geodata_src.is_file():
            warnings.append(f"harita geodata atlandı: kaynak yok: {geodata_src}")
        elif not okullar_src.is_file():
            warnings.append("harita geodata atlandı: okullar.json yok")

    detay_src = CANONICAL["okullar_detay"]
    harita_dir = SITE["okullar_harita_dir"]
    if okullar_src.is_file() and detay_src.is_file():
        total, coords = sync_okullar_harita(okullar_src, detay_src, harita_dir)
        print(
            f"Yazıldı: {harita_dir}/meta.json + il dosyaları "
            f"({total} kurum, {coords} koordinatlı)"
        )
        wrote += 1
    else:
        if not okullar_src.is_file():
            warnings.append("okullar-harita atlandı: okullar.json yok")
        elif not detay_src.is_file():
            warnings.append(f"okullar-harita atlandı: kaynak yok: {detay_src}")

    for msg in warnings:
        print(f"  [UYARI] {msg}", file=sys.stderr)

    cleanup_stale_data()

    if warnings and strict:
        return 1
    if not wrote and strict:
        return 1
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "docs/data → _data/turkiye_adres_il_ilce.json + assets/data "
            "(okullar, geodata, okullar-harita)"
        )
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Kaynak eksikse exit 1 (varsayılan: uyarı + exit 0)",
    )
    parser.add_argument(
        "--cleanup-only",
        action="store_true",
        help="Yalnızca _data büyük JSON kalıntılarını sil (Jekyll öncesi)",
    )
    args = parser.parse_args(argv)
    if args.cleanup_only:
        return 0 if cleanup_stale_data() >= 0 else 1
    return sync(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
