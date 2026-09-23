#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从文献列表 JSON 抽取 TopN 下载目标，生成带安全文件名的 targets JSON。

输入 JSON 结构（兼容 cnki_survey_result.json）：
  list[dict]  或  dict{"results":[...]} / dict{"items":[...]} / dict{"data":[...]}
每条目字段：title, url, year, cited, downloads, type, authors, source ...

排序：
  --by cases  从标题正则 r"(\d+)\s*例" 提取例数（缺省 0）
  --by cited  按 cited 降序（缺省 0）
  --by year   按 year 降序
"""
import argparse, json, re

def safe_name(s, maxlen=60):
    s = re.sub(r'[\\/:*?"<>|]', '_', s or '')
    return s[:maxlen].strip()

def extract_cases(title):
    m = re.search(r'(\d+)\s*例', title or '')
    return int(m.group(1)) if m else 0

def load(path):
    d = json.load(open(path, encoding='utf-8'))
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        for k in ('results', 'items', 'data', 'papers', 'records'):
            if isinstance(d.get(k), list):
                return d[k]
    return []

def main():
    ap = argparse.ArgumentParser(description="抽取 TopN 下载目标")
    ap.add_argument('input', help='文献列表 JSON')
    ap.add_argument('--out', default='_download_targets.json')
    ap.add_argument('--top', type=int, default=20)
    ap.add_argument('--by', choices=['cases', 'cited', 'year'], default='cases')
    ap.add_argument('--min-cases', type=int, default=0)
    ap.add_argument('--type-filter', default='', help='仅保留 type 含此子串的条目')
    args = ap.parse_args()

    rows = load(args.input)
    items = []
    for x in rows:
        title = (x.get('title') or '').strip()
        url = x.get('url') or ''
        if not url:
            continue
        if args.type_filter and args.type_filter not in (x.get('type') or ''):
            continue
        cases = extract_cases(title) if args.by == 'cases' else 0
        if args.by == 'cases' and cases < args.min_cases:
            continue
        items.append({
            'title': title,
            'url': url,
            'year': x.get('year'),
            'cited': x.get('cited'),
            'cases': cases,
            'type': x.get('type'),
            'source': x.get('source'),
            'fname': safe_name(f"{title}_{x.get('source', '')}_{x.get('year', '')}"),
        })
    sort_key = (lambda r: r['cases']) if args.by == 'cases' else \
               (lambda r: r['cited'] or 0) if args.by == 'cited' else \
               (lambda r: r['year'] or 0)
    items.sort(key=sort_key, reverse=True)
    items = items[:args.top]
    for i, it in enumerate(items, 1):
        it['rank'] = i
    json.dump({'items': items}, open(args.out, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f"wrote {len(items)} targets -> {args.out}")
    for it in items[:5]:
        print(f"  {it['rank']:2d}. cases={it['cases']:5d} | {it['title'][:50]}")

if __name__ == '__main__':
    main()
