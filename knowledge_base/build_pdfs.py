"""Render the knowledge-base Markdown sources (_src/*.md) into the PDF files the
project brief asks for (section 10). Run after editing any source doc:

    python3 knowledge_base/build_pdfs.py

Requires: pip install markdown xhtml2pdf
"""
from __future__ import annotations

from pathlib import Path

import markdown
from xhtml2pdf import pisa

HERE = Path(__file__).resolve().parent
SRC = HERE / "_src"

# md stem -> the PascalCase PDF name from the brief
NAMES = {
    "faq": "FAQ",
    "refund_policy": "RefundPolicy",
    "shipping_policy": "ShippingPolicy",
    "warranty": "Warranty",
    "pricing": "Pricing",
    "products": "Products",
    "installation_guide": "InstallationGuide",
    "user_manual": "UserManual",
}

CSS = """
@page { size: A4; margin: 2.2cm 2cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 10.5pt; color: #1f2937; line-height: 1.5; }
h1 { font-size: 20pt; color: #4f46e5; border-bottom: 2px solid #e5e7eb; padding-bottom: 6px; margin: 0 0 14px; }
h2 { font-size: 13pt; color: #6d28d9; margin: 18px 0 6px; }
h3 { font-size: 11pt; color: #374151; margin: 12px 0 4px; }
p, li { font-size: 10.5pt; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; }
th, td { border: 1px solid #d1d5db; padding: 5px 8px; text-align: left; font-size: 10pt; }
th { background: #eef2ff; color: #3730a3; }
.brandbar { color: #9ca3af; font-size: 8.5pt; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px; }
"""


def build() -> None:
    made = 0
    for md in sorted(SRC.glob("*.md")):
        name = NAMES.get(md.stem, md.stem.title())
        body = markdown.markdown(md.read_text(encoding="utf-8"), extensions=["tables", "sane_lists"])
        html = (
            f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>"
            f"<div class='brandbar'>TechMart Electronics &middot; Knowledge Base</div>"
            f"{body}</body></html>"
        )
        out = HERE / f"{name}.pdf"
        with open(out, "wb") as f:
            result = pisa.CreatePDF(html, dest=f, encoding="utf-8")
        if result.err:
            print(f"  !! error rendering {md.name}")
        else:
            print(f"  wrote {out.name}  ({out.stat().st_size // 1024} KB)")
            made += 1
    print(f"\nBuilt {made} PDFs in {HERE}")


if __name__ == "__main__":
    build()
