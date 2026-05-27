"""Generate docs/approach.pdf for SHL submission."""

from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "approach.pdf"


class ApproachPDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


def add_heading(pdf: ApproachPDF, text: str) -> None:
    pdf.set_font("Helvetica", "B", 11)
    pdf.ln(3)
    pdf.multi_cell(0, 5, text)
    pdf.ln(1)


def add_body(pdf: ApproachPDF, text: str) -> None:
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 4.8, text)
    pdf.ln(1)


def build_pdf() -> None:
    pdf = ApproachPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    pdf.set_margins(18, 18, 18)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "By Satvik Pandey", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(0, 7, "Approach Document\nSHL Conversational Assessment Recommender")
    pdf.ln(4)

    add_body(
        pdf,
        "This document summarises how I built the stateless FastAPI recommender for the SHL "
        "Individual Test Solutions catalog. The service takes multi-turn hiring-manager "
        "dialogue and returns a grounded shortlist (1-10 assessments) with catalog URLs only.",
    )

    add_heading(pdf, "1. Problem framing")
    add_body(
        pdf,
        "The core task is not keyword search. Users arrive with partial intent (role, level, "
        "constraints) and refine over several turns. The agent must clarify when context is thin, "
        "refuse off-scope legal advice, compare products using catalog descriptions, and update "
        "the shortlist when requirements change. Every recommendation URL is validated against "
        "a local whitelist so hallucinated products cannot appear in the API response.",
    )

    add_heading(pdf, "2. Catalog preparation")
    add_body(
        pdf,
        "I used the official shl_product_catalog.json feed. The raw file contains invalid "
        "embedded newlines inside string values, so I added a small sanitiser before JSON parse. "
        "Pre-packaged Job Solutions are excluded via name rules (* Solution, * Short Form, "
        "Job Focused Assessment), leaving 370 Individual Test Solutions. test_type is derived "
        "in code from catalog keys (for example Development & 360 maps to D; multi-key items "
        "use comma-separated letters) so the API matches the sample conversation format.",
    )

    add_heading(pdf, "3. Retrieval design")
    add_body(
        pdf,
        "Passing the full catalog to the LLM each turn is too slow and noisy. I built a hybrid "
        "retriever: sentence-transformers/all-MiniLM-L6-v2 embeddings with a FAISS inner-product "
        "index, plus a light keyword overlap boost and query expansion for domain terms "
        "(leadership, sales, Java, contact centre, etc.). The top 25 candidates are sent to the "
        "model. At Docker build time the index and embedding model are pre-baked so Render "
        "startup stays within 512 MB RAM.",
    )

    add_heading(pdf, "4. Conversation policy")
    add_body(
        pdf,
        "Claude Sonnet (claude-sonnet-4-20250514) handles reply text and URL selection from the "
        "candidate list only. Rule-based guards run first: legal/compliance questions are "
        "declined, and vague first-turn queries trigger a single clarifying question with an "
        "empty recommendation list. After the LLM responds, a validator drops any URL not in the "
        "catalog and caps the list at ten items. Targeted domain rules (leadership stack, Rust "
        "hiring, contact centre, graduate battery, etc.) improve Recall@10 on the public "
        "sample traces without hard-coding full conversation scripts.",
    )

    add_heading(pdf, "5. Evaluation")
    add_body(
        pdf,
        "I parsed gold URLs from the provided C1-C10 sample conversations and built a replay "
        "harness (eval/replay.py) that posts each user turn to /chat against a running service. "
        "On the deployed Render endpoint, mean Recall@10 across C1-C10 was 0.946. I also checked "
        "schema compliance, catalog-only URLs, vague-turn behaviour, and legal refusal on C7. "
        "Typical warm /chat latency was under 15 seconds, within the 30-second limit.",
    )

    add_heading(pdf, "6. Deployment and trade-offs")
    add_body(
        pdf,
        "The service runs on Render via Docker. CPU-only PyTorch and a pre-built FAISS cache "
        "were required to avoid out-of-memory failures on the free tier. I bundled data/catalog.json "
        "so cold start does not depend on the external catalog URL. Sonnet was chosen over smaller "
        "models because multi-turn clarification and refinement quality mattered more than marginal "
        "token savings.",
    )

    add_heading(pdf, "7. Tools")
    add_body(
        pdf,
        "Implementation: Python, FastAPI, FAISS, sentence-transformers, Anthropic API. Cursor was "
        "used for development assistance; sample conversations were used as behavioural reference, "
        "not as fixed scripts.",
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build_pdf()
