#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验下载目录中的 PDF 合法性，可选搬进项目目录，隔离异常文件（不删）。

用法:
  python verify_pdfs.py --src D:/download --move-to "项目/下载原文" --keep-src
"""
import argparse, os, shutil

def is_pdf(path):
    try:
        with open(path, 'rb') as f:
            return f.read(5) == b'%PDF-'
    except Exception:
        return False

def main():
    ap = argparse.ArgumentParser(description="校验并搬运下载的 PDF")
    ap.add_argument('--src', required=True, help='下载目录')
    ap.add_argument('--move-to', default='', help='合法 PDF 搬往目录')
    ap.add_argument('--keep-src', action='store_true', help='保留下载目录原件')
    args = ap.parse_args()

    files = [f for f in os.listdir(args.src) if f.lower().endswith('.pdf')]
    ok, bad = [], []
    for f in files:
        p = os.path.join(args.src, f)
        (ok if is_pdf(p) else bad).append(f)

    print(f"合法 PDF: {len(ok)} | 异常(非PDF): {len(bad)}")
    for f in bad:
        print(f"  [异常-不删] {f}")

    if args.move_to:
        os.makedirs(args.move_to, exist_ok=True)
        for f in ok:
            src = os.path.join(args.src, f)
            dst = os.path.join(args.move_to, f)
            if args.keep_src:
                shutil.copy(src, dst)
            else:
                shutil.move(src, dst)
        print(f"已搬 {len(ok)} 篇 -> {args.move_to}"
              + (" (保留原件)" if args.keep_src else " (移动)"))

    print("\n合法文件清单:")
    for f in ok:
        print("  ", f)

if __name__ == '__main__':
    main()
