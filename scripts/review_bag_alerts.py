"""
review_bag_alerts.py
────────────────────
Sends every alert image to Gemini and asks whether anyone in the frame
is carrying a duty-free plastic bag.

Result written back to MongoDB `alerts` collection:
  alert_type  →  "duty_free_bag"  |  "None"
  gemini_note →  raw Gemini answer (for audit / debugging)

Usage
-----
  python3 scripts/review_bag_alerts.py            # process all alerts
  python3 scripts/review_bag_alerts.py --limit 20 # first 20 only (test)
  python3 scripts/review_bag_alerts.py --dry-run  # no DB writes
  python3 scripts/review_bag_alerts.py --reprocess # re-examine already
                                                    # classified docs too
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

# ── Prompt ────────────────────────────────────────────────────────────────────
PROMPT = """
You are a security analyst reviewing CCTV footage from an airport retail store.

Examine this image carefully and answer ONE question:

Is there any person in the image who is visibly holding or carrying a
duty-free shopping bag? Duty-free bags are typically:
- Plastic or paper bags with handles
- Branded with airport duty-free shop names (e.g. DFS, Dufry, Heinemann,
  IndiGo Duty Free, or similar)
- Or plain white/transparent plastic bags consistent with airport retail
- The bag should be clearly in someone's hand or arm, not just on a shelf

Reply with EXACTLY one of these two words and nothing else:
  YES   – at least one duty-free bag is clearly visible being carried
  NO    – no duty-free bags are visible being carried by any person
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
    """Map Gemini YES/NO to alert_type value."""
    upper = gemini_answer.upper()
    if upper.startswith("YES"):
        return "duty_free_bag"
    return "None"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Review bag alerts with Gemini")
    parser.add_argument("--limit",     type=int, default=0,
                        help="Max number of documents to process (0 = all)")
    parser.add_argument("--dry-run",   action="store_true",
                        help="Run Gemini but do NOT write to MongoDB")
    parser.add_argument("--reprocess", action="store_true",
                        help="Include docs already classified (not just 'bag_detected')")
    args = parser.parse_args()

    # ── MongoDB ──
    print("Connecting to MongoDB …")
    mongo = MongoClient(MONGO_URI)
    col   = mongo["adaniServer"]["alerts"]

    if args.reprocess:
        query = {}          # every document
    else:
        # Only touch documents that haven't been reviewed yet
        query = {"alert_type": {"$nin": ["duty_free_bag", "None"]}}

    total = col.count_documents(query)
    print(f"Documents to process: {total}"
          f"{' (dry-run – no writes)' if args.dry_run else ''}")

    if total == 0:
        print("Nothing to do. Use --reprocess to re-examine classified docs.")
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

    for i, doc in enumerate(docs, 1):
        doc_id    = doc["_id"]
        image_url = (doc.get("image_url") or "").strip()
        prefix    = f"[{i}/{len(docs)}]"

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

            # 3. Write to DB
            if not args.dry_run:
                update = {
                    "alert_type":  alert_type,
                    "gemini_note": answer,            # keep raw answer for audit
                }
                if alert_type == "None":
                    update["response"] = ""           # blank response when no bag found
                col.update_one({"_id": doc_id}, {"$set": update})

            tag = "DRY" if args.dry_run else "OK "
            print(f"{prefix} {tag}  {alert_type:<16} │ gemini='{answer[:60]}'")
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

    print("\n─────────────────────────────────────")
    print(f"Done.  ok={ok}  errors={err}  skipped={skipped}")
    print(f"Total processed: {ok + err + skipped} / {len(docs)}")


if __name__ == "__main__":
    main()
