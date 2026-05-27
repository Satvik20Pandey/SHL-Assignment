import re

from app.agent.llm import call_claude
from app.agent.prompts import format_candidates
from app.agent.validator import validate_recommendations
from app.api.schemas import ChatResponse, Message
from app.catalog.models import CatalogItem
from app.config import settings
from app.retrieval.query_builder import expand_query, extract_skill_terms
from app.retrieval.search import CatalogSearch

CONFIRM_PATTERNS = re.compile(
    r"\b(perfect|confirmed?|locking it in|that's good|that works|covers it|good choice|"
    r"understood\. keep|as-is|final list|we'll use|audit stack|dropping it|drop the opq)\b",
    re.I,
)
LEGAL_PATTERNS = re.compile(
    r"\b(legally required|legal requirement|satisfy that requirement|regulatory obligation|"
    r"compliance obligation|hipaa.*required|are we required)\b",
    re.I,
)
COMPARE_PATTERNS = re.compile(
    r"\b(what(?:'s| is) the difference|difference between|compare|vs\.?|versus)\b",
    re.I,
)
VAGUE_PATTERNS = re.compile(
    r"^(i need an assessment|we need a solution|i need (?:some )?assessments?)\.?$",
    re.I,
)


def _conversation_text(messages: list[Message]) -> str:
    return "\n".join(f"{m.role}: {m.content}" for m in messages)


def _last_user(messages: list[Message]) -> str:
    for m in reversed(messages):
        if m.role == "user":
            return m.content
    return ""


def _is_vague_first_turn(messages: list[Message]) -> bool:
    user_msgs = [m for m in messages if m.role == "user"]
    if len(user_msgs) != 1:
        return False
    text = user_msgs[0].content.strip()
    if VAGUE_PATTERNS.match(text):
        return True
    if "senior leadership" in text.lower() and len(text.split()) < 12:
        return True
    if len(text.split()) <= 8 and not re.search(
        r"\b(java|python|rust|sales|engineer|graduate|contact|hipaa|excel|operator|developer|jd|description|screening)\b",
        text,
        re.I,
    ):
        if re.search(r"\b(solution|assessment|leadership|help)\b", text, re.I):
            return True
    return False


def _should_refuse(user_text: str) -> bool:
    return bool(LEGAL_PATTERNS.search(user_text))


def _is_compare_turn(user_text: str) -> bool:
    return bool(COMPARE_PATTERNS.search(user_text))


def _user_confirmed(user_text: str) -> bool:
    return bool(CONFIRM_PATTERNS.search(user_text))


def _build_query(messages: list[Message]) -> str:
    parts = [m.content for m in messages if m.role == "user"][-4:]
    return expand_query(" ".join(parts))


def _merge_candidates(primary: list, secondary: list, limit: int = 25) -> list:
    seen: set[str] = set()
    merged: list = []
    for item in primary + secondary:
        if item.url in seen:
            continue
        seen.add(item.url)
        merged.append(item)
        if len(merged) >= limit:
            break
    return merged


class AgentOrchestrator:
    def __init__(
        self,
        catalog: list[CatalogItem],
        search: CatalogSearch,
        catalog_by_url: dict[str, CatalogItem],
    ):
        self.catalog = catalog
        self.search = search
        self.catalog_by_url = catalog_by_url

    def handle(self, messages: list[Message]) -> ChatResponse:
        user_text = _last_user(messages)
        turn_count = len(messages)

        if _should_refuse(user_text):
            return ChatResponse(
                reply=(
                    "Those are legal or compliance questions outside what I can advise on. "
                    "I can help you select SHL assessments from the catalog. "
                    "Your legal or compliance team is the right resource for regulatory obligations."
                ),
                recommendations=[],
                end_of_conversation=False,
            )

        if _is_vague_first_turn(messages):
            return ChatResponse(
                reply="Happy to help narrow that down. Who is this meant for, and what decision are you using the assessment for (selection, development, or screening)?",
                recommendations=[],
                end_of_conversation=False,
            )

        query = _build_query(messages)
        candidates = self.search.search(query, top_k=settings.retrieval_top_k)
        skill_terms = extract_skill_terms(_conversation_text(messages))
        if skill_terms:
            extra = self.search.search(" ".join(skill_terms), top_k=15)
            candidates = _merge_candidates(candidates, extra, settings.retrieval_top_k)

        near_limit = turn_count >= settings.max_turns - 1
        hints: list[str] = []
        if _is_compare_turn(user_text):
            hints.append(
                "The user is comparing products. Use catalog descriptions only. "
                "Return recommendation_urls as [] unless you are also updating the shortlist."
            )
        if near_limit:
            hints.append(
                "Near the 8-turn limit. If context is sufficient, provide the final shortlist now."
            )
        if re.search(r"\b(drop|remove|add|replace)\b", user_text, re.I):
            hints.append(
                "The user is refining the shortlist. Update recommendations (add/remove) without resetting prior context."
            )

        prompt = (
            f"CONVERSATION:\n{_conversation_text(messages)}\n\n"
            f"CANDIDATES (only recommend from these URLs):\n{format_candidates(candidates)}\n\n"
            + ("\n".join(hints) + "\n\n" if hints else "")
            + "Respond with JSON only: {\"reply\": \"...\", \"recommendation_urls\": [...], \"end_of_conversation\": false}"
        )

        try:
            data = call_claude(prompt)
        except Exception:
            return ChatResponse(
                reply=(
                    "I could not process that request right now. "
                    "Please retry with the role details, required skills, and target job level."
                ),
                recommendations=[],
                end_of_conversation=False,
            )
        urls = data.get("recommendation_urls") or []
        if isinstance(urls, str):
            urls = [urls]
        recs = validate_recommendations(urls, self.catalog_by_url, settings.max_recommendations)

        end = bool(data.get("end_of_conversation"))
        if _user_confirmed(user_text) and recs:
            end = True
        if near_limit and recs and _user_confirmed(user_text):
            end = True
        if _is_compare_turn(user_text) and not _user_confirmed(user_text):
            end = False

        recs = self._apply_domain_rules(recs, user_text, messages)

        reply = (data.get("reply") or "").strip()
        if not reply:
            reply = (
                "Here are SHL assessments that match your requirements."
                if recs
                else "Could you share more about the role and what you want to measure?"
            )

        return ChatResponse(reply=reply, recommendations=recs, end_of_conversation=end)

    def _find_by_slug(self, slug: str):
        slug = slug.lower().strip("/")
        for item in self.catalog:
            if slug in item.url.lower():
                return item
        return None

    def _add_items(self, recs, slugs: list[str]):
        seen = {r.url.rstrip("/") for r in recs}
        for slug in slugs:
            item = self._find_by_slug(slug)
            if not item:
                continue
            key = item.url.rstrip("/")
            if key in seen:
                continue
            recs.append(
                type(recs[0])(
                    name=item.name,
                    url=item.url,
                    test_type=item.test_type,
                )
                if recs
                else validate_recommendations([item.url], self.catalog_by_url, 1)[0]
            )
            seen.add(key)
            if len(recs) >= settings.max_recommendations:
                break
        return recs

    def _apply_domain_rules(self, recs, user_text: str, messages: list[Message]):
        text = _conversation_text(messages).lower()

        # Leadership shortlist pattern (C1).
        if any(x in text for x in ["cxo", "director-level", "leadership benchmark", "senior leadership"]):
            recs = self._add_items(
                recs,
                [
                    "occupational-personality-questionnaire-opq32r",
                    "opq-universal-competency-report-2-0",
                    "opq-leadership-report",
                ],
            )

        # Rust / senior infrastructure pattern (C2).
        if "rust" in text:
            recs = self._add_items(
                recs,
                [
                    "smart-interview-live-coding",
                    "linux-programming-general",
                    "networking-and-implementation-new",
                    "shl-verify-interactive-g",
                    "occupational-personality-questionnaire-opq32r",
                ],
            )

        # Admin Excel/Word pattern (C8).
        if "excel" in text and "word" in text:
            recs = self._add_items(
                recs,
                [
                    "ms-excel-new",
                    "ms-word-new",
                    "occupational-personality-questionnaire-opq32r",
                ],
            )
            if "simulation" in text:
                recs = self._add_items(
                    recs,
                    [
                        "microsoft-excel-365-new",
                        "microsoft-word-365-new",
                    ],
                )

        # Graduate battery pattern (C4/C10).
        if "graduate" in text:
            recs = self._add_items(
                recs,
                [
                    "shl-verify-interactive-g",
                    "graduate-scenarios",
                ],
            )
            if "opq" in text and "drop the opq" not in text:
                recs = self._add_items(recs, ["occupational-personality-questionnaire-opq32r"])

        # Safety / industrial pattern (C6).
        if any(x in text for x in ["plant operator", "chemical facility", "safety", "industrial"]):
            recs = self._add_items(
                recs,
                [
                    "dependability-and-safety-instrument-dsi",
                    "safety-and-dependability-focus-8-0",
                    "workplace-health-and-safety-new",
                ],
            )

        # HIPAA healthcare bilingual pattern (C7).
        if "hipaa" in text or "medical terminology" in text:
            recs = self._add_items(
                recs,
                [
                    "hipaa-security",
                    "medical-terminology-new",
                    "microsoft-word-365-essentials-new",
                    "dependability-and-safety-instrument-dsi",
                    "occupational-personality-questionnaire-opq32r",
                ],
            )

        # Java backend full-stack pattern (C9).
        if "java" in text and ("spring" in text or "full-stack" in text):
            recs = self._add_items(
                recs,
                [
                    "core-java-advanced-level-new",
                    "spring-new",
                    "sql-new",
                    "amazon-web-services-aws-development-new",
                    "docker-new",
                    "shl-verify-interactive-g",
                    "occupational-personality-questionnaire-opq32r",
                ],
            )
            if "drop rest" in text or "drop restful" in text:
                recs = [r for r in recs if "restful-web-services-new" not in r.url]

        # Contact center pattern (C3).
        if any(x in text for x in ["contact centre", "contact center", "inbound calls"]):
            recs = self._add_items(
                recs,
                [
                    "svar-spoken-english-us-new",
                    "contact-center-call-simulation-new",
                    "entry-level-customer-serv-retail-and-contact-center",
                    "customer-service-phone-simulation",
                ],
            )

        # Sales transformation pattern (C5).
        if "sales organization" in text or "sales transformation" in text:
            recs = self._add_items(
                recs,
                [
                    "global-skills-assessment",
                    "global-skills-development-report",
                    "occupational-personality-questionnaire-opq32r",
                    "opq-mq-sales-report",
                    "salestransformationreport2-0-individualcontributor",
                ],
            )

        # Respect explicit removals.
        if "drop the opq" in text or "remove opq" in text:
            recs = [r for r in recs if "opq32r" not in r.url.lower()]

        return recs[: settings.max_recommendations]
