"""A corpus that refreshes, and tells you what moved.

The naive version of this fetches once and treats the result as permanent. That
is how a kit ends up confidently quoting last year's filing fee: nothing in the
system is capable of noticing.

So the unit of change here is the chunk, not the page. Pages change constantly
for reasons nobody cares about -- a rotated banner, a new footer link. What
matters is whether the specific line a kit rests on still says what it said.

The trick is giving a chunk an identity that survives its own edit. A chunk's
*key* is derived from the opening of its text, which is the stable part:

    "Certificate of formation for a Texas entity ... (Forms 201, 203, 205, 206) $300"
     └──────────────── key: this survives ────────────────┘   └── hash: this moves ──┘

When the fee changes from $300 to $325, the key holds and the hash moves, and
refresh reports CHANGED against that exact line rather than "the page is
different somehow".

    python3 -m groundwork.corpus refresh            # only what is past its TTL
    python3 -m groundwork.corpus refresh --force    # everything
    python3 -m groundwork.corpus search "<query>"   # what retrieval sees
    python3 -m groundwork.corpus impact <plan.json> # which citations lost their support
"""

from __future__ import annotations

import hashlib
import html
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
import time
from datetime import date, datetime, timedelta

from .audit import Run
from .errors import ToolError, classify

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
RAW = CORPUS / "raw"
MANIFEST = CORPUS / "manifest.json"
CHUNKS = CORPUS / "chunks.jsonl"
LOCK = CORPUS / "corpus.lock.json"
WATCH = CORPUS / "watch.json"

UA = "Groundwork/0.1 (+https://github.com/Lily-Feng/Enterprise-Data-AI-Architecture-Atlas)"
TIMEOUT = 25
MIN_CHUNK = 40
MAX_CHUNK = 1200
KEY_PREFIX = 60

BLOCK_END = re.compile(
    rb"</(?:p|div|li|tr|h[1-6]|section|article|dd|dt|blockquote)\s*>", re.I
)
DROP = (
    re.compile(rb"<script\b[^>]*>.*?</script>", re.S | re.I),
    re.compile(rb"<style\b[^>]*>.*?</style>", re.S | re.I),
    re.compile(rb"<!--.*?-->", re.S),
    re.compile(rb"<nav\b[^>]*>.*?</nav>", re.S | re.I),
    re.compile(rb"<header\b[^>]*>.*?</header>", re.S | re.I),
    re.compile(rb"<footer\b[^>]*>.*?</footer>", re.S | re.I),
)

# Chunks that are about the website rather than its subject.
BOILERPLATE = re.compile(
    r"skip to main content|visit votetexas|cookies? (policy|settings)|"
    r"official website of the united states government|"
    r"^(home|menu|search|share|print|breadcrumb)\b", re.I
)
TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def normalize(text: str) -> str:
    return WS.sub(" ", html.unescape(TAG.sub(" ", text))).strip()


def digest(text: str, n: int = 12) -> str:
    return hashlib.sha1(text.lower().encode("utf-8")).hexdigest()[:n]


def chunk_key(url: str, text: str, occurrence: int = 0) -> str:
    """Identity that survives the chunk's own edit.

    Anchored on the opening of the text, which for a fee schedule or a form
    listing is the label rather than the value.

    Distinct rows can share an opening -- two Texas amendment fees differ only
    after sixty characters -- so the occurrence index disambiguates them. Both
    are kept. Dropping one made a real fee unretrievable and did it silently.
    """
    base = digest(url + "|" + text[:KEY_PREFIX].lower(), 12)
    return base if occurrence == 0 else f"{base}#{occurrence}"


def to_chunks(body: bytes, source: dict) -> list[dict]:
    """Split on block boundaries rather than a fixed window.

    Government pages are mostly tables and lists, where one row is one fact. A
    sliding window would cut "(Forms 201, 203, 205, 206)" away from "$300" and
    make the most important line in the corpus unretrievable.
    """
    for pattern in DROP:
        body = pattern.sub(b" ", body)
    blocks = BLOCK_END.split(body)
    out: list[dict] = []
    prefix_seen: dict[str, int] = {}
    for raw_block in blocks:
        text = normalize(raw_block.decode("utf-8", "replace"))
        if len(text) < MIN_CHUNK:
            continue
        for piece in ([text] if len(text) <= MAX_CHUNK else
                      [text[i:i + MAX_CHUNK] for i in range(0, len(text), MAX_CHUNK)]):
            piece = piece.strip()
            if len(piece) < MIN_CHUNK:
                continue
            if BOILERPLATE.search(piece):
                continue
            stem = digest(source["url"] + "|" + piece[:KEY_PREFIX].lower(), 12)
            occurrence = prefix_seen.get(stem, 0)
            prefix_seen[stem] = occurrence + 1
            out.append({
                "key": chunk_key(source["url"], piece, occurrence),
                "hash": digest(piece),
                "effective_date": source.get("effective_date"),
                "text": piece,
                "source_id": source["id"],
                "url": source["url"],
                "title": source["title"],
                "tier": source["tier"],
                "jurisdiction": source["jurisdiction"],
            })
    # An identical line repeated verbatim (nav plus body) is still noise, but
    # two different lines are not: dedupe on the full text, never on the key.
    seen: set[str] = set()
    return [c for c in out if not (c["hash"] in seen or seen.add(c["hash"]))]


def fetch(url: str, attempts: int = 3) -> tuple[bytes | None, ToolError | None]:
    """Fetch a page, retrying only the failures where retrying can help.

    A 403 from a host that refuses automated access is not a transient
    condition, and hammering it is both rude and useless. A 503 is.
    """
    last: ToolError | None = None
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read(), None
        except Exception as e:  # noqa: BLE001 - classify() sorts these out
            last = classify(e)
            if not last.retryable or attempt == attempts:
                return None, last
            time.sleep(min((last.retry_after_ms or 1000) / 1000, 5) * attempt)
    return None, last


def load_manifest() -> tuple[dict, list[dict]]:
    data = json.loads(MANIFEST.read_text())
    defaults = data.get("defaults", {})
    sources = []
    for s in data["sources"]:
        sources.append({**defaults, **s})
    return defaults, sources


def load_lock() -> dict:
    return json.loads(LOCK.read_text()) if LOCK.exists() else {"sources": {}, "chunks": {}}


def is_due(source: dict, lock: dict, force: bool) -> bool:
    if force:
        return True
    entry = lock["sources"].get(source["id"])
    if not entry or not entry.get("fetched"):
        return True
    age = date.today() - date.fromisoformat(entry["fetched"])
    return age >= timedelta(days=int(source.get("refresh_days", 30)))


def refresh(force: bool = False, only: str | None = None) -> int:
    with Run("refresh", force=force, only=only) as run:
        return _refresh(run, force, only)


def _refresh(run: Run, force: bool, only: str | None) -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    _, sources = load_manifest()
    lock = load_lock()
    previous_chunks: dict[str, dict] = lock.get("chunks", {})

    if only:
        sources = [s for s in sources if s["id"] == only]
        if not sources:
            print(f"no source with id {only!r}")
            return 2

    all_chunks: list[dict] = []
    refreshed_ids = {s["id"] for s in sources}
    # Carry forward anything this run is not touching.
    carried = [c for c in (load_chunks_quiet()) if c["source_id"] not in refreshed_ids]
    added: list[dict] = []
    changed: list[tuple[dict, str]] = []
    skipped = failed = 0

    print(f"refresh: {len(sources)} source(s) in manifest\n")
    for s in sources:
        if s.get("kind") != "html":
            print(f"  skip     {s['id']}  (kind={s.get('kind')} not yet supported)")
            skipped += 1
            continue
        if not is_due(s, lock, force):
            cached = RAW / f"{s['id']}.html"
            if cached.exists():
                all_chunks.extend(to_chunks(cached.read_bytes(), s))
                print(f"  fresh    {s['id']}  (within {s.get('refresh_days', 30)}d TTL)")
                skipped += 1
                continue

        body, err = fetch(s["url"])
        if body is None:
            failed += 1
            run.event("source_failed", source_id=s["id"], url=s["url"],
                      category=err.category if err else None,
                      retryable=err.retryable if err else None, detail=str(err))
            print(f"  FAILED   {s['id']}  ({err})")
            if note := s.get("note"):
                print(f"           note: {note}")
            cached = RAW / f"{s['id']}.html"
            if cached.exists():
                fallback = to_chunks(cached.read_bytes(), s)
                for ch in fallback:
                    ch["stale"] = True
                    ch["stale_reason"] = f"served from cache after {err}"
                all_chunks.extend(fallback)
                run.event("served_stale", source_id=s["id"], reason=str(err),
                          chunks=len(fallback))
                print(f"           serving {len(fallback)} STALE chunk(s) from cache")
            continue

        (RAW / f"{s['id']}.html").write_bytes(body)
        chunks = to_chunks(body, s)
        all_chunks.extend(chunks)
        lock["sources"][s["id"]] = {"fetched": date.today().isoformat(), "url": s["url"],
                                    "chunks": len(chunks)}

        for c in chunks:
            old = previous_chunks.get(c["key"])
            if old is None:
                added.append(c)
            elif old["hash"] != c["hash"]:
                changed.append((c, old["text"]))
        run.event("source_fetched", source_id=s["id"], url=s["url"], chunks=len(chunks))
        print(f"  ok       {s['id']}  ({len(chunks)} chunks)")

    current_keys = {c["key"] for c in all_chunks}
    # Only a source this run actually fetched can have lost a chunk.
    removed = [v for k, v in previous_chunks.items()
               if k not in current_keys and v.get("source_id") in refreshed_ids]

    merged = [*carried, *all_chunks]
    CHUNKS.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in merged) + "\n")
    lock["chunks"] = {c["key"]: {"hash": c["hash"], "text": c["text"][:240],
                                 "source_id": c["source_id"]} for c in merged}
    lock["refreshed_at"] = datetime.now().isoformat(timespec="seconds")
    LOCK.write_text(json.dumps(lock, indent=2, sort_keys=True))

    run.event("corpus_written", chunks=len(merged), added=len(added),
              changed=len(changed), removed=len(removed), failed=failed)
    scope = f" ({len(all_chunks)} from {len(refreshed_ids)} refreshed)" if carried else ""
    print(f"\n  {len(merged)} chunks{scope} | {len(added)} added, {len(changed)} changed, "
          f"{len(removed)} removed | {skipped} skipped, {failed} failed")

    if changed:
        print("\n  CHANGED - anything resting on these needs re-reading:\n")
        for c, before in changed:
            run.event("source_changed", source_id=c["source_id"], url=c["url"],
                      chunk=c["key"], now=c["text"][:300], was=before[:300])
            print(f"    [{c['source_id']}] {c['text'][:150]}")
            print(f"      was: {before[:150]}\n")
    if removed and previous_chunks:
        print(f"  REMOVED - {len(removed)} chunk(s) no longer on their page:\n")
        for r in removed[:10]:
            print(f"    [{r['source_id']}] {r['text'][:150]}")

    # A watched phrase that vanishes is the loudest possible signal: the exact
    # line a kit was built on is gone.
    missing_watch = []
    watched = json.loads(WATCH.read_text()) if WATCH.exists() else {}
    for s in sources:
        for phrase in s.get("watch", []):
            hits = [c["text"] for c in all_chunks
                    if c["source_id"] == s["id"] and phrase.lower() in c["text"].lower()]
            if hits:
                watched[f"{s['id']}::{phrase}"] = {
                    "url": s["url"],
                    "seen": sorted(hits, key=len)[0][:400],
                    "as_of": date.today().isoformat(),
                }
            else:
                missing_watch.append((s["id"], phrase))
    if watched:
        WATCH.write_text(json.dumps(watched, indent=2, sort_keys=True) + "\n")
    if missing_watch:
        print("\n  WATCH LOST:")
        for sid, phrase in missing_watch:
            run.event("watch_lost", source_id=sid, phrase=phrase)
            print(f"    [{sid}] {phrase!r} no longer appears on the page")
        return 1

    return 1 if failed and not all_chunks else 0


def load_chunks_quiet() -> list[dict]:
    """Chunks on disk, or nothing. Used by refresh, which may be building them."""
    if not CHUNKS.exists():
        return []
    return [json.loads(line) for line in CHUNKS.read_text().splitlines() if line.strip()]


def load_chunks() -> list[dict]:
    if not CHUNKS.exists():
        print("no corpus yet. run: python3 -m groundwork.corpus refresh", file=sys.stderr)
        raise SystemExit(2)
    return [json.loads(line) for line in CHUNKS.read_text().splitlines() if line.strip()]


def search(query: str, jurisdiction: str | None = None, limit: int = 5,
           as_of: str | None = None, allow_stale: bool = True) -> list[dict]:
    """Keyword scoring over the live corpus.

    Deliberately BM25-shaped rather than semantic: the highest-value queries in
    this domain are exact strings -- "Form 2553", "Forms 201, 203, 205, 206".
    Dense retrieval arrives alongside this, not instead of it.

    The jurisdiction filter runs *before* scoring. A California rule answering a
    Texas question is this domain's permission leak.
    """
    chunks = load_chunks()
    if jurisdiction:
        allowed = {"US", jurisdiction}
        chunks = [c for c in chunks if c["jurisdiction"] in allowed]
    if as_of:
        # Guidance that takes effect after the date being asked about must not
        # answer a question about that date.
        chunks = [c for c in chunks
                  if not c.get("effective_date") or c["effective_date"] <= as_of]
    if not allow_stale:
        chunks = [c for c in chunks if not c.get("stale")]
    terms = [t for t in re.findall(r"[a-z0-9§$.,-]+", query.lower()) if len(t) > 1]
    scored = []
    for c in chunks:
        low = c["text"].lower()
        score = sum(low.count(t) * (3 if len(t) > 4 else 1) for t in terms)
        if query.lower() in low:
            score += 25
        if score:
            weight = {1: 1.6, 2: 1.0, 3: 0.7}.get(c["tier"], 1.0)
            scored.append((score * weight / (1 + len(c["text"]) / 800), c))
    scored.sort(key=lambda x: -x[0])
    return [{**c, "score": round(s, 2)} for s, c in scored[:limit]]


def impact(plan_path: str) -> int:
    """Which of a kit's citations no longer have text behind them.

    This is the join between a refreshed corpus and an already-generated kit.
    Every `quote` in a plan claims a page says something; after a refresh, that
    claim is either still true or it is not.
    """
    plan = json.loads(pathlib.Path(plan_path).read_text())
    chunks = load_chunks()
    by_url: dict[str, list[dict]] = {}
    for c in chunks:
        by_url.setdefault(c["url"], []).append(c)

    quoted: list[tuple[str, str]] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("quote") and node.get("url"):
                quoted.append((node["url"], node["quote"]))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(plan)

    if not quoted:
        print("  no quoted citations in this plan; nothing to check against the corpus")
        return 0

    broken = 0
    print(f"  checking {len(quoted)} quoted citation(s) against the live corpus\n")
    for url, quote in quoted:
        pool = by_url.get(url, [])
        needle = WS.sub(" ", quote).strip().lower()
        if not pool:
            print(f"  NO CORPUS  {url}\n             add it to corpus/manifest.json")
            broken += 1
        elif any(needle in WS.sub(" ", c["text"]).lower() for c in pool):
            print(f"  ok         {quote[:90]}")
        else:
            print(f"  BROKEN     {quote[:90]}")
            print(f"             no longer appears at {url}")
            broken += 1
    print(f"\n  {len(quoted) - broken}/{len(quoted)} citations still supported")
    return 1 if broken else 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "refresh":
        only = None
        if "--only" in argv:
            only = argv[argv.index("--only") + 1]
        return refresh(force="--force" in argv, only=only)
    if cmd == "search":
        if len(argv) < 3:
            print("usage: search <query> [--jurisdiction TX]")
            return 2
        j = argv[argv.index("--jurisdiction") + 1] if "--jurisdiction" in argv else None
        as_of = argv[argv.index("--as-of") + 1] if "--as-of" in argv else None
        hits = search(argv[2], j, as_of=as_of, allow_stale="--no-stale" not in argv)
        if not hits:
            print("  no matches")
        for h in hits:
            mark = " STALE" if h.get("stale") else ""
            print(f"\n  [{h['score']}] {h['source_id']} (tier {h['tier']}, "
                  f"{h['jurisdiction']}){mark}")
            print(f"  {h['text'][:300]}")
        return 0
    if cmd == "impact":
        if len(argv) < 3:
            print("usage: impact <plan.json>")
            return 2
        return impact(argv[2])
    print(f"unknown command {cmd!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
