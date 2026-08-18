#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Commit 0dbecf1 öncesi kitap açıklamalarını geri yükler (description + gövde özeti)."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKS = ROOT / "_books"
SOURCE_COMMIT = "0dbecf1^"

# Gövde + description geri yüklenecek dosyalar (26)
BODY_RESTORE = [
    "_books/alicanin-gunlugu.md",
    "_books/atasozu-oykuleri.md",
    "_books/cilgin-dede-icatlar-kesifler.md",
    "_books/cilgin-dede-masal-makinesi.md",
    "_books/cilgin-dede-turkiye-turu.md",
    "_books/cilgin-dede-uygarlıklar.md",
    "_books/degerler-okyanusu.md",
    "_books/deyim-oykuleri.md",
    "_books/dinozor-cagi.md",
    "_books/duygularımı-kesfediyorum.md",
    "_books/engel-tanimayanlar.md",
    "_books/erdemlerimizi-kesfedelim.md",
    "_books/etik-degerler-1.md",
    "_books/etik-degerler-2.md",
    "_books/etkinliklerle-hacivat.md",
    "_books/fen-oykuleri.md",
    "_books/gizli-dedektiflik-burosu.md",
    "_books/guclu-karakter.md",
    "_books/hayat-bilgisi-oykuleri.md",
    "_books/istiklal-marsi-yazdiran-kahramanlar.md",
    "_books/iyilik-heryerde-serisi.md",
    "_books/kral-egitim-seti-4.md",
    "_books/matematik-oykuleri.md",
    "_books/meslek-oykuleri.md",
    "_books/o-bir-dahi.md",
    "_books/robot-avcilari.md",
]

# Yalnızca description düzeltilecek (3)
DESC_ONLY = [
    "_books/asik-suratli-cocuk-1.md",
    "_books/aya-seyahat.md",
    "_books/baba-evi.md",
]

META_START = re.compile(r"\n\*\*TEMALAR\*\*", re.IGNORECASE)
CURRENT_META = re.compile(
    r"(\n\*\*TEMALAR:\*\*.*?)(?=\n<!--more-->|\Z)",
    re.DOTALL | re.IGNORECASE,
)


def git_show(path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{path}"],
        cwd=ROOT,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", "replace")


def split_frontmatter(text: str) -> tuple[str, str, str]:
    if not text.startswith("---"):
        raise ValueError("Front matter bulunamadı")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Geçersiz front matter")
    return parts[0], parts[1], parts[2]


def get_description(fm: str) -> str | None:
    for line in fm.split("\n"):
        if line.startswith("description:"):
            match = re.match(r'description:\s*"?(.+?)"?\s*$', line)
            if match:
                return match.group(1).strip('"')
            return ""
    return None


def set_description(fm: str, description: str | None) -> str:
    lines = fm.split("\n")
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("description:"):
            replaced = True
            if description is not None:
                escaped = description.replace('"', '\\"')
                out.append(f'description: "{escaped}"')
            continue
        out.append(line)
    if not replaced and description is not None:
        inserted = False
        new_lines: list[str] = []
        for line in out:
            new_lines.append(line)
            if not inserted and line.startswith("title:"):
                escaped = description.replace('"', '\\"')
                new_lines.append(f'description: "{escaped}"')
                inserted = True
        out = new_lines
    return "\n".join(out)


def split_body(body: str) -> tuple[str, str, str]:
    more = ""
    if "<!--more-->" in body:
        idx = body.index("<!--more-->")
        more = body[idx:]
        body = body[:idx]
    meta_match = CURRENT_META.search(body)
    meta = meta_match.group(1).strip() if meta_match else ""
    excerpt = body[: meta_match.start()] if meta_match else body
    return excerpt.strip(), meta, more


def extract_old_prose(body: str) -> str:
    body = body.split("<!--more-->")[0]
    match = META_START.search(body)
    if not match:
        return body.strip()

    before = body[: match.start()].strip()
    after_block = body[match.start() :]

    etiket = re.search(r"\*\*ETİKETLER\*\*:?", after_block, re.IGNORECASE)
    if not etiket:
        return before

    rest = after_block[etiket.end() :]
    lines = rest.split("\n")
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped == "" or stripped.startswith("•") or stripped.startswith("-"):
            index += 1
            continue
        break
    after = "\n".join(lines[index:]).strip()
    if after:
        return f"{before}\n\n{after}".strip()
    return before


def rebuild_file(
    current_text: str,
    old_text: str,
    *,
    restore_body: bool,
) -> str:
    _, cur_fm, cur_body = split_frontmatter(current_text)
    _, old_fm, old_body = split_frontmatter(old_text)

    new_fm = set_description(cur_fm, get_description(old_fm))

    cur_excerpt, cur_meta, cur_more = split_body(cur_body)
    old_excerpt = extract_old_prose(old_body)

    excerpt = old_excerpt if restore_body else cur_excerpt
    parts = [excerpt]
    if cur_meta:
        parts.append("")
        parts.append(cur_meta)
    if cur_more:
        parts.append("")
        parts.append(cur_more.rstrip())
    elif not cur_more:
        parts.append("")
        parts.append("<!--more-->")

    new_body = "\n".join(parts)
    if not new_body.endswith("\n"):
        new_body += "\n"
    return f"---{new_fm}---\n{new_body}"


def restore_file(rel_path: str, *, restore_body: bool) -> None:
    path = ROOT / rel_path
    current = path.read_text(encoding="utf-8")
    old = git_show(rel_path)
    if old is None:
        raise FileNotFoundError(f"Git geçmişinde bulunamadı: {rel_path}")
    updated = rebuild_file(current, old, restore_body=restore_body)
    path.write_text(updated, encoding="utf-8", newline="\n")
    print(f"OK {rel_path}")


def main() -> None:
    for rel in BODY_RESTORE:
        restore_file(rel, restore_body=True)
    for rel in DESC_ONLY:
        restore_file(rel, restore_body=False)
    print(f"\nToplam {len(BODY_RESTORE) + len(DESC_ONLY)} dosya geri yüklendi.")


if __name__ == "__main__":
    main()
