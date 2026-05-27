# Approach Document — SHL Assessment Recommender

## Problem decomposition

Build a stateless conversational agent that maps vague hiring intent to 1–10 grounded SHL Individual Test Solutions via clarify → recommend → refine/compare → end, with hard catalog validation on every URL.

## Catalog

Source: official `shl_product_catalog.json`. Embedded newlines in JSON strings are sanitized before parse. Pre-packaged Job Solutions filtered by name (`* Solution`, `* Short Form`, `*Job Focused Assessment*`) → 370 items. `test_type` derived deterministically from `keys` (Development & 360 → `D`; else comma-joined A/B/C/D/E/K/P/S).

## Retrieval

Hybrid: MiniLM embeddings + FAISS `IndexFlatIP` + keyword overlap boost + query expansion for domain terms (sales, leadership, Java, etc.). Top 25 candidates passed to the LLM.

## Agent (Claude Sonnet)

**Model:** `claude-sonnet-4-20250514` via Anthropic API — strong multi-turn instruction following for clarification, refusal, comparison, and refinement.

**Per turn:** rule-based guards (legal refuse, vague-first-turn clarify) → retrieve → Claude selects URLs from candidates → whitelist validator caps at 10.

No retrieval-only fallback in production; all recommendation turns use the LLM.

## Evaluation

Gold URLs parsed from sample conversations C1–C10. Metrics: Recall@10 (URL match), schema compliance, behavior probes (no rec on vague turn 1, catalog-only URLs, legal refusal). `eval/replay.py` runs multi-turn replay against `/chat`.

## Trade-offs

- Bundled `data/catalog.json` for reliable deploy cold-start.
- Flash/smaller models risk missing nuanced behaviors; Sonnet chosen for eval quality within 30s when warm.
- Deterministic `test_type` avoids LLM format drift.

## AI tools

Cursor for implementation; Anthropic Claude for dialogue and shortlist selection; sample conversations as behavioral reference.
