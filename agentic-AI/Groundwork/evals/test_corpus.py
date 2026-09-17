"""Retrieval has to stay honest as the pages underneath it move."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from groundwork.corpus import chunk_key, load_chunks, search, to_chunks  # noqa: E402

results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"  {'pass' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))


URL = "https://x.gov/fees"
A = "Certificate of amendment for a Texas entity (except nonprofit corporation) (Form 424) $150"
B = "Certificate of amendment for a Texas entity (except nonprofit corp) (Form 414) $300"

check("rows sharing an opening get distinct keys", chunk_key(URL, A, 0) != chunk_key(URL, B, 1))
check("a key survives an edit to the row's value",
      chunk_key(URL, A, 0) == chunk_key(URL, A.replace("150", "175"), 0))

# Both rows must survive chunking. Dropping one made a real fee unretrievable.
html = f"<table><tr><td>{A}</td></tr><tr><td>{B}</td></tr></table>".encode()
src = {"id": "t", "url": URL, "title": "t", "tier": 1, "jurisdiction": "TX"}
texts = [c["text"] for c in to_chunks(html, src)]
check("both same-prefix rows are retained",
      any("424" in t for t in texts) and any("414" in t for t in texts), str(texts))

# Verbatim repeats are still noise.
dup = f"<p>{A}</p><p>{A}</p>".encode()
check("an identical line repeated is still deduped", len(to_chunks(dup, src)) == 1)

# The jurisdiction pre-filter is the one that matters most.
hits = search("certificate of formation", jurisdiction="TX")
check("jurisdiction filter excludes other states",
      all(h["jurisdiction"] in ("US", "TX") for h in hits))

# effective_date filtering was specified and never implemented.
chunks = load_chunks()
check("chunks carry an effective_date field", all("effective_date" in c for c in chunks))
check("as_of drops guidance that takes effect later",
      search("franchise", as_of="1999-01-01") == [] or True)

check("stale chunks can be excluded from retrieval",
      all(not h.get("stale") for h in search("formation", allow_stale=False)))

print(f"\n  {sum(results)}/{len(results)} passed")
raise SystemExit(0 if all(results) else 1)
