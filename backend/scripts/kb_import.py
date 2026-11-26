"""Bulk-import a folder of PDFs/images into an installer's knowledge base (Admin -> Knowledge).

The worker then indexes them in the background (needs OPENAI_API_KEY). Duplicates are skipped.

  docker compose -p solar run --rm --no-deps -v "C:\\path\\to\\folder:/import:ro" api \
      python scripts/kb_import.py --installer demo --dir /import
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import session_scope  # noqa: E402
from app.models import Installer  # noqa: E402
from app.services import kb  # noqa: E402

EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
SKIP_DIRS = {"_duplicates", "09_videos", "10_misc"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--installer", default="demo", help="installer slug")
    ap.add_argument("--dir", required=True)
    args = ap.parse_args()

    with session_scope(None, bypass=True) as db:
        inst = db.scalar(select(Installer).where(Installer.slug == args.installer))
        if inst is None:
            sys.exit(f"Installer '{args.installer}' not found")
        iid = inst.id

    files = sorted(p for p in Path(args.dir).rglob("*")
                   if p.is_file() and p.suffix.lower() in EXTS and not (set(x.lower() for x in p.parts) & SKIP_DIRS))
    added = skipped = 0
    for p in files:
        with session_scope(iid) as db:
            doc, reason = kb.save_document(db, p.read_bytes(), p.name, uploaded_by=None)
        if doc:
            added += 1
            print(f"added    {p.relative_to(args.dir)}")
        else:
            skipped += 1
            print(f"skipped  {p.relative_to(args.dir)}  ({reason})")
    print(f"\n{added} added, {skipped} skipped. The worker indexes new documents in the background.")


if __name__ == "__main__":
    main()
