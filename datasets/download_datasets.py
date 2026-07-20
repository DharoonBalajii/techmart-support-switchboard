"""Download the public datasets referenced in the project brief (section 9).

Fetches reliably-sized samples/files into subfolders under datasets/. The very
large sources (full CFPB database, full MS MARCO) are sampled — links to the
complete downloads are in datasets/README.md.

Run:  python3 datasets/download_datasets.py
"""
from __future__ import annotations

import csv
import io
import json
import os
import ssl
import subprocess
import urllib.request
from json import JSONDecoder
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CTX = ssl.create_default_context()
HDRS = {"User-Agent": "Mozilla/5.0 (dataset-fetch)"}


def _get(url: str, timeout: int = 90, cap: int | None = None) -> bytes:
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read(cap) if cap else r.read()


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    print(f"   saved {path.relative_to(ROOT)}  ({len(data)/1024:.0f} KB)")


def banking77() -> None:
    print("B. Banking77 — intent classification (77 intents)")
    base = "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data"
    try:
        for name in ("train.csv", "test.csv", "categories.json"):
            _write(ROOT / "banking77" / name, _get(f"{base}/{name}"))
        # quick stats
        rows = list(csv.DictReader(io.StringIO((ROOT / "banking77" / "train.csv").read_text())))
        print(f"   -> {len(rows)} training utterances")
    except Exception as e:
        print(f"   !! failed: {e}")


def squad() -> None:
    print("D. SQuAD v2.0 — question answering")
    base = "https://raw.githubusercontent.com/rajpurkar/SQuAD-explorer/master/dataset"
    try:
        _write(ROOT / "squad" / "dev-v2.0.json", _get(f"{base}/dev-v2.0.json"))
        n = len(json.loads((ROOT / "squad" / "dev-v2.0.json").read_text())["data"])
        print(f"   -> dev set: {n} topics (train-v2.0.json is ~40 MB — see README)")
    except Exception as e:
        print(f"   !! failed: {e}")


def ms_marco(sample: int = 100) -> None:
    print(f"E. MS MARCO — passage QA (sampling {sample} rows)")
    url = (
        "https://datasets-server.huggingface.co/rows?dataset=microsoft/ms_marco"
        f"&config=v1.1&split=validation&offset=0&length={sample}"
    )
    try:
        payload = json.loads(_get(url))
        rows = [r["row"] for r in payload.get("rows", [])]
        _write(ROOT / "ms_marco" / "validation_sample.json", json.dumps(rows, indent=2).encode())
        print(f"   -> {len(rows)} rows (full set is tens of GB — see README)")
    except Exception as e:
        print(f"   !! failed: {e}")


def cfpb(sample: int = 250) -> None:
    print(f"A. CFPB — consumer complaints (sampling {sample} with narratives)")
    # The API blocks some clients and ignores `size`, streaming a large JSON
    # array. curl fetches it reliably; we cap the read and tolerantly parse the
    # first `sample` complete records, ignoring the truncated tail.
    url = (
        "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
        "?no_aggs=true&format=json&has_narrative=true&field=complaint_what_happened"
    )
    tmp = ROOT / "cfpb" / "_raw.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["curl", "-s", "--max-time", "60", url, "-o", str(tmp)],
            check=True,
        )
        raw = tmp.read_text(encoding="utf-8", errors="ignore")
        dec, i, out = JSONDecoder(), raw.find("{"), []
        while len(out) < sample and i != -1:
            while i < len(raw) and raw[i] in " \n\r\t,":
                i += 1
            if i >= len(raw) or raw[i] == "]":
                break
            try:
                obj, i = dec.raw_decode(raw, i)
            except ValueError:
                break
            out.append(obj)
        recs = []
        for h in out:
            s = h.get("_source", h)
            recs.append(
                {
                    "product": s.get("product"),
                    "issue": s.get("issue"),
                    "sub_issue": s.get("sub_issue"),
                    "company": s.get("company"),
                    "state": s.get("state"),
                    "date_received": s.get("date_received"),
                    "narrative": (s.get("complaint_what_happened") or "").strip(),
                }
            )
        tmp.unlink(missing_ok=True)
        if not recs:
            print("   !! API returned no parseable records (rate-limited?); keeping existing sample")
            return
        _write(ROOT / "cfpb" / "complaints_sample.json", json.dumps(recs, indent=2).encode())
        print(f"   -> {len(recs)} complaints (full DB updates daily — see README)")
    except Exception as e:
        print(f"   !! failed: {e} (keeping existing sample if present)")


def dailydialog() -> None:
    # DailyDialog's original host (yanran.li) is unreliable and the Hugging Face
    # copies are now gated (require `huggingface-cli login`). We ship a small
    # format sample so the pipeline has data; see README for the full download.
    print("C. DailyDialog — multi-turn dialogue (gated upstream; shipping a sample)")
    sample = (
        "Say , Jim , how about going for a few beers after dinner ? __eou__ "
        "You know that is tempting but is really not good for our fitness . __eou__ "
        "What do you mean ? It will help us to relax . __eou__ "
        "Do you really think so ? I don't . It will just make us fat and act silly . __eou__\n"
        "Can you do push-ups ? __eou__ Of course I can . It's a piece of cake ! "
        "Believe it or not , I can do 30 push-ups a minute . __eou__ "
        "Really ? I think that's impossible ! __eou__ You mean 30 push-ups ? __eou__\n"
        "Hello , this is Mary . Can I speak to John ? __eou__ "
        "Speaking . What can I do for you , Mary ? __eou__ "
        "I was wondering if you could help me move this weekend . __eou__ "
        "Sure , I'd be happy to . What time ? __eou__\n"
    )
    _write(ROOT / "dailydialog" / "dialogues_sample.txt", sample.encode())
    print("   -> 3 sample dialogues ( __eou__ = end-of-utterance ). Full set: see README.")


if __name__ == "__main__":
    print("Downloading public datasets into", ROOT, "\n")
    banking77()
    squad()
    ms_marco()
    cfpb()
    dailydialog()
    print("\nDone. See datasets/README.md for what each set is and how it's used.")
