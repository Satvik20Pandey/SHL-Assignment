import re
from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parents[1].parent / "sample_conversations" / "GenAI_SampleConversations"
URL_RE = re.compile(r"<(https://www\.shl\.com/products/product-catalog/view/[^>]+)>")


def parse_conversation(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    turns: list[dict] = []
    user_msgs: list[str] = []
    blocks = re.split(r"### Turn \d+", text)
    for block in blocks[1:]:
        user_m = re.search(r"\*\*User\*\*\s*\n+>\s*(.+?)(?=\n\n\*\*Agent\*\*|\Z)", block, re.S)
        agent_block = re.search(r"\*\*Agent\*\*\s*\n+(.*?)(?=_No recommendations|_`end_of_conversation`|### Turn|\Z)", block, re.S)
        user_content = ""
        if user_m:
            user_content = re.sub(r"\n>\s*", "\n", user_m.group(1).strip())
            user_content = user_content.strip("> ").strip()
            user_msgs.append(user_content)
        urls = URL_RE.findall(block)
        end = "`end_of_conversation`: **true**" in block
        no_rec = "recommendations: null" in block or "_No recommendations" in block
        turns.append(
            {
                "user": user_content,
                "urls": urls,
                "end": end,
                "no_recommendations": no_rec,
            }
        )
    final_urls: list[str] = []
    for t in reversed(turns):
        if t["urls"]:
            final_urls = t["urls"]
            break
    return {
        "id": path.stem,
        "turns": turns,
        "user_messages": user_msgs,
        "gold_urls": [u.rstrip("/") for u in final_urls],
    }


def load_all_samples(samples_dir: Path | None = None) -> list[dict]:
    base = samples_dir or SAMPLES_DIR
    return [parse_conversation(p) for p in sorted(base.glob("C*.md"))]
