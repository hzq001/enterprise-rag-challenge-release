"""show.py —— 把 PDF 指定页渲染为高清图片，供展示给用户（无需先建索引）。

用法：
  python show.py <pdf> --pages 6,7 [--dpi 220] [--out pdf-vision-out]
"""
import argparse
import sys
from pathlib import Path

import fitz

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MAX_SIDE_PX = 4096


def main():
    ap = argparse.ArgumentParser(description="Render PDF pages to images")
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--pages", required=True, help="页码，逗号分隔，如 6,7 或 6-9")
    ap.add_argument("--dpi", type=int, default=220)
    ap.add_argument("--out", type=Path, default=Path("pdf-vision-out"))
    args = ap.parse_args()

    pdf = args.pdf.resolve()
    if not pdf.is_file():
        sys.exit(f"PDF not found: {pdf}")

    pages = set()
    for part in args.pages.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            if "-" in part:
                a, b = part.split("-", 1)
                pages.update(range(int(a), int(b) + 1))
            else:
                pages.add(int(part))
        except ValueError:
            ap.error(f"无法解析页码: {part!r}（格式如 6,7 或 6-9）")

    try:
        doc = fitz.open(str(pdf))
    except Exception as e:                       # 损坏/格式不支持
        sys.exit(f"无法打开 PDF（可能已损坏）: {pdf}\n  {type(e).__name__}: {e}")
    if doc.needs_pass:                           # 加密 PDF 打开成功但访问页时才会报错
        doc.close()
        sys.exit(f"PDF 已加密，无法渲染（需先解密）: {pdf}")

    stem = pdf.name.rsplit(".", 1)[0]
    args.out.mkdir(exist_ok=True)
    rendered = 0
    for p in sorted(pages):
        if not 1 <= p <= len(doc):
            print(f"[skip] page {p} out of range (1-{len(doc)})")
            continue
        page = doc[p - 1]
        long_side_in = max(page.rect.width, page.rect.height) / 72
        dpi = max(72, min(args.dpi, int(MAX_SIDE_PX / long_side_in)))
        dst = args.out / f"{stem}_p{p}.png"
        page.get_pixmap(dpi=dpi).save(str(dst))
        print(dst.resolve())
        rendered += 1
    if rendered == 0:
        sys.exit(f"没有渲染任何页面: --pages {args.pages!r} 均不在 1-{len(doc)} 范围内")


if __name__ == "__main__":
    main()
