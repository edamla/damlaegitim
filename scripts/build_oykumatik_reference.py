#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse Öykümatik xlsx → JSON for build_oykumatik_reference.rb"""

import glob
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XLSX_DIR = ROOT / 'docs' / 'oykumatik-kazanimlar'
OUT_YML = ROOT / '_data' / 'oykumatik-kazanimlari.yml'
OUT_CSV = ROOT / 'docs' / 'oykumatikkazanimlar.csv'

KAVRAMSAL = {
    'Olay Örgüsü': 1,
    'Zaman ve Mekân': 2,
    'Şahıs ve Varlık Kadrosu': 3,
    'Dil ve Anlatım': 4,
}

BILISSEL_NAMES = {
    1: 'Hatırlama Anlama',
    2: 'Uygulama',
    3: 'Çözümleme',
    4: 'Değerlendirme',
}

KAVRAMSAL_NAMES = {v: k for k, v in KAVRAMSAL.items()}


def read_xlsx_rows(path):
    z = zipfile.ZipFile(path)
    ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    ss = ET.fromstring(z.read('xl/sharedStrings.xml'))
    strings = []
    for si in ss.findall(f'{ns}si'):
        strings.append(''.join(n.text or '' for n in si.iter(f'{ns}t')))

    sheet = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    rows = {}
    for row in sheet.findall(f'.//{ns}row'):
        r = int(row.get('r'))
        cells = {}
        for c in row.findall(f'{ns}c'):
            ref = c.get('r', '')
            col = re.match(r'([A-Z]+)', ref).group(1)
            v = c.find(f'{ns}v')
            if v is None:
                continue
            val = strings[int(v.text)] if c.get('t') == 's' else v.text
            cells[col] = val
        rows[r] = cells
    return rows


def parse_codes(rows):
    kavramsal = 1
    bilissel = 0
    codes = {}

    for r in sorted(rows):
        c = rows[r]
        if 'B' in c:
            name = c['B'].strip()
            if name in KAVRAMSAL:
                kavramsal = KAVRAMSAL[name]
        if 'C' in c and re.match(r'\d+-B', c['C']):
            bilissel = int(c['C'].split('-')[0])
        if 'D' not in c or 'E' not in c:
            continue

        no = int(c['D'])
        label = c['E'].strip()
        grades = []
        for col, g in zip('FGHIJKLMN', list(range(1, 9)) + ['lise']):
            if c.get(col) == 'X':
                grades.append(g)

        code = f'H.{kavramsal}.{bilissel}.{no}'
        codes[code] = {
            'label': label,
            'kavramsal': KAVRAMSAL_NAMES[kavramsal],
            'bilissel': BILISSEL_NAMES[bilissel],
            'grades': grades,
        }

    return codes


def write_yaml(by_code, path):
    lines = ['by_code:']
    for code in sorted(by_code):
        entry = by_code[code]
        lines.append(f'  {code}:')
        lines.append(f'    label: {json.dumps(entry["label"], ensure_ascii=False)}')
        lines.append(f'    kavramsal: {json.dumps(entry["kavramsal"], ensure_ascii=False)}')
        lines.append(f'    bilissel: {json.dumps(entry["bilissel"], ensure_ascii=False)}')
        grades = entry['grades']
        inner = ', '.join(json.dumps(g, ensure_ascii=False) for g in grades)
        lines.append(f'    grades: [{inner}]')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_csv(by_code, path):
    lines = ['kod;kazanim']
    for code in sorted(by_code):
        label = by_code[code]['label'].replace(';', ',')
        lines.append(f'{code};{label}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    xlsx_files = list(XLSX_DIR.glob('*.xlsx'))
    if not xlsx_files:
        print('xlsx bulunamadı', file=sys.stderr)
        sys.exit(1)

    rows = read_xlsx_rows(xlsx_files[0])
    by_code = parse_codes(rows)
    write_yaml(by_code, OUT_YML)
    write_csv(by_code, OUT_CSV)
    print(f'Yazıldı: {OUT_YML} ({len(by_code)} kod)')
    print(f'Yazıldı: {OUT_CSV} ({len(by_code)} satır + başlık)')


if __name__ == '__main__':
    main()
