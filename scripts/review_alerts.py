"""
review_alerts.py
────────────────
Sends CCTV alert images (where alert_type is null / blank / "None") to Gemini
and classifies each into one of four store-operations categories.

Result written back to MongoDB `alerts` collection:
  alert_type  →  "Overcrowding alert"    | crowded / congested area
                 "Cleanliness alert"     | bags / litter on the floor
                 "Empty shelf alert"     | shelves appear empty or bare
                 "Billing counter alert" | customers at counter, no staff visible
                 "None"                  | none of the above detected
  gemini_note →  raw Gemini keyword (for audit / debugging)

Usage
-----
  python3 scripts/review_alerts.py                  # process all unclassified
  python3 scripts/review_alerts.py --limit 20       # first 20 only (test)
  python3 scripts/review_alerts.py --dry-run        # no DB writes
  python3 scripts/review_alerts.py --reprocess      # re-examine already
                                                     # classified store alerts too
"""

import os, sys, time, argparse, requests
from pymongo import MongoClient
from google import genai
from google.genai import types

# ── Config ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = "AIzaSyCfL06rKavVSMjKZ4iCD3-SQpH0BfrYDWE"
GEMINI_MODEL   = "gemini-2.0-flash"          # fast + vision-capable

MONGO_URI = (
    "mongodb://tarsyer_admin:MdbTarsyerAdmin%232025%21Prod%247"
    "@database.tarsyer.com:27018/adaniServer?authSource=admin"
)

# Seconds to wait between API calls (free tier = 15 req/min → 4 s gap)
REQUEST_DELAY = 4.0

# ── Store-alert types produced by this script ─────────────────────────────────
STORE_ALERT_TYPES = [
    "Overcrowding alert",
    "Cleanliness alert",
    "Empty shelf alert",
    "Billing counter alert",
    "Processed",
]

# ── Prompt ────────────────────────────────────────────────────────────────────
PROMPT = """
You are a security and compliance analyst reviewing CCTV footage from an
airport duty-free retail store.

Examine this image carefully and classify it into EXACTLY ONE of the following
five categories:

  OVERCROWDING      – Too many people are visible; the area looks congested or
                      crowded beyond normal shopping capacity.

  CLEANLINESS       – Bags, litter, packaging, or other debris is clearly
                      visible lying on the floor or ground.

  EMPTY_SHELF       – Display shelves, racks, or product stands appear notably
                      empty or very poorly stocked.

  BILLING_COUNTER   – One or more customers are visibly standing or waiting at
                      a billing / checkout counter, but NO staff member wearing
                      a black uniform is present or visible to serve them.

  NONE              – None of the above issues are clearly present in this
                      frame.

Rules:
- Reply with EXACTLY one of the five keywords above and nothing else.
- If you are uncertain, choose NONE.
- If multiple issues are visible, choose the single most prominent one.
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def download_image(url: str, timeout: int = 20) -> tuple[bytes, str]:
    """Return (image_bytes, mime_type)."""
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    ct = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
    if ct not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        ct = "image/jpeg"
    return resp.content, ct


def ask_gemini(client: genai.Client, image_bytes: bytes, mime_type: str) -> str:
    """Call Gemini and return the raw text response (stripped)."""
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            PROMPT,
        ],
    )
    return response.text.strip()


def classify(gemini_answer: str) -> str:
    """Map Gemini keyword to alert_type value stored in MongoDB."""
    # Take first word only, normalise to uppercase
    token = gemini_answer.strip().upper().split()[0] if gemini_answer.strip() else ""
    mapping = {
        "OVERCROWDING":    "Overcrowding alert",
        "CLEANLINESS":     "Cleanliness alert",
        "EMPTY_SHELF":     "Empty shelf alert",
        "BILLING_COUNTER": "Billing counter alert",
    }
    # "Processed" marks reviewed images where Gemini found no actionable issue
    return mapping.get(token, "Processed")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Classify unreviewed store alerts with Gemini vision"
    )
    parser.add_argument("--limit",     type=int, default=0,
                        help="Max documents to process (0 = all)")
    parser.add_argument("--dry-run",   action="store_true",
                        help="Run Gemini but do NOT write to MongoDB")
    parser.add_argument("--reprocess", action="store_true",
                        help="Re-examine docs already classified with store "
                             "alert types (not just unclassified ones)")
    args = parser.parse_args()

    # ── MongoDB ──
    print("Connecting to MongoDB …")
    mongo = MongoClient(MONGO_URI)
    col   = mongo["adaniServer"]["alerts"]

    if args.reprocess:
        # Re-examine everything that isn't a bag alert
        query = {"alert_type": {"$nin": ["duty_free_bag", "bag_detected"]}}
    else:
        # Default: only documents whose alert_type is null, missing, or "None"/"" (unclassified)
        query = {"alert_type": {"$in": [None, "None", ""]}}

    total = col.count_documents(query)
    print(f"Documents to process: {total}"
          f"{' (dry-run – no writes)' if args.dry_run else ''}")

    if total == 0:
        print("Nothing to do. Use --reprocess to re-examine already-classified docs.")
        return

    cursor = col.find(query, {"_id": 1, "image_url": 1, "alert_type": 1})
    if args.limit:
        cursor = cursor.limit(args.limit)
        print(f"(Limited to first {args.limit} documents)")

    # ── Gemini client ──
    gemini = genai.Client(api_key=GEMINI_API_KEY)

    # ── Process ──
    ok = err = skipped = 0
    docs = list(cursor)

    # Tally by result type for summary
    tally = {t: 0 for t in STORE_ALERT_TYPES}

    for i, doc in enumerate(docs, 1):
        doc_id    = doc["_id"]
        image_url = (doc.get("image_url") or "").strip()
        prefix    = f"[{i:>5}/{len(docs)}]"

        if not image_url:
            print(f"{prefix} SKIP  — no image_url  (_id={doc_id})")
            skipped += 1
            continue

        try:
            # 1. Download image
            image_bytes, mime_type = download_image(image_url)

            # 2. Ask Gemini
            answer     = ask_gemini(gemini, image_bytes, mime_type)
            alert_type = classify(answer)
            tally[alert_type] = tally.get(alert_type, 0) + 1

            # 3. Write to DB
            if not args.dry_run:
                col.update_one(
                    {"_id": doc_id},
                    {"$set": {
                        "alert_type":  alert_type,
                        "gemini_note": answer,
                    }}
                )

            tag = "DRY" if args.dry_run else "OK "
            print(f"{prefix} {tag}  {alert_type:<26} │ gemini='{answer[:40]}'")
            ok += 1

        except requests.exceptions.HTTPError as e:
            print(f"{prefix} ERR  HTTP {e.response.status_code} — {image_url[:80]}")
            err += 1
        except Exception as e:
            print(f"{prefix} ERR  {type(e).__name__}: {e}")
            err += 1

        # Rate-limit between calls
        if i < len(docs):
            time.sleep(REQUEST_DELAY)

    # ── Summary ──
    print("\n─────────────────────────────────────────────────────")
    print(f"Done.  ok={ok}  errors={err}  skipped={skipped}")
    print(f"Total processed: {ok + err + skipped} / {len(docs)}")
    if ok:
        print("\nBreakdown of classifications:")
        for t, count in tally.items():
            if count:
                print(f"  {t:<28} {count:>5}")


if __name__ == "__main__":
    main()
