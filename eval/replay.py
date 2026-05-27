"""Replay sample conversations against a running /chat endpoint."""

import argparse
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from eval.parse_samples import load_all_samples
from eval.recall import mean_recall_at_k, recall_at_k


def replay_conversation(client: httpx.Client, base_url: str, sample: dict) -> tuple[list[str], list[dict]]:
    messages: list[dict] = []
    trace: list[dict] = []
    final_recs: list[str] = []

    for turn in sample["turns"]:
        if not turn["user"]:
            continue
        messages.append({"role": "user", "content": turn["user"]})
        resp = client.post(f"{base_url}/chat", json={"messages": messages}, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        messages.append({"role": "assistant", "content": data["reply"]})
        rec_urls = [r["url"] for r in data.get("recommendations", [])]
        if rec_urls:
            final_recs = rec_urls
        trace.append(
            {
                "user": turn["user"][:80],
                "reply": data["reply"][:120],
                "rec_count": len(rec_urls),
                "end": data.get("end_of_conversation"),
            }
        )
        if data.get("end_of_conversation"):
            break

    return final_recs, trace


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--conv", default=None, help="e.g. C1")
    args = parser.parse_args()

    samples = load_all_samples()
    if args.conv:
        samples = [s for s in samples if s["id"] == args.conv]

    results = []
    with httpx.Client() as client:
        for sample in samples:
            recs, trace = replay_conversation(client, args.url, sample)
            score = recall_at_k(recs, sample["gold_urls"], 10)
            results.append((recs, sample["gold_urls"]))
            print(f"\n{sample['id']}: Recall@10 = {score:.2f}")
            print(f"  Gold ({len(sample['gold_urls'])}): {len(sample['gold_urls'])} items")
            print(f"  Got  ({len(recs)}): {len(recs)} items")
            for t in trace:
                print(f"    - user: {t['user']}... | recs: {t['rec_count']} | end: {t['end']}")

    mean = mean_recall_at_k(results, 10)
    print(f"\nMean Recall@10: {mean:.3f}")


if __name__ == "__main__":
    main()
