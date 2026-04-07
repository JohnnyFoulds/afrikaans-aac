"""
o3-feedback.py — Deep-thinking OpenAI o3 feedback on the research outline and outreach email.

Sends each document to o3 with a role-specific system prompt:
  1. research-outline-working.md  — reviewed as a UNISA doctoral committee member
  2. email-van-biljon.md          — reviewed as Prof van Biljon reading cold outreach

Writes results to:
  pipeline-outputs/o3-feedback-research-outline.md
  pipeline-outputs/o3-feedback-email-van-biljon.md
  pipeline-outputs/o3-feedback-summary.md   (combined summary)

Usage:
    conda run -n claude-llm python scripts/o3-feedback.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------
env_path = Path(__file__).parent.parent / ".env"
env = {}
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()

api_key = env.get("OPENAI_API_KEY")
if not api_key:
    sys.exit("ERROR: OPENAI_API_KEY not found in .env")

try:
    import openai
except ImportError:
    sys.exit("ERROR: openai package not installed. Run: pip install openai")

client = openai.OpenAI(api_key=api_key)
MODEL = "o3"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO = Path(__file__).parent.parent
OUTLINE = REPO / "admin/research-outline/research-outline-working.md"
EMAIL   = REPO / "admin/outreach/email-van-biljon.md"
OUT_DIR = REPO / "pipeline-outputs"
OUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

OUTLINE_SYSTEM = """You are a member of a UNISA doctoral admissions and examination committee for the College of Science, Engineering and Technology (CSET). You are also an expert in Design Science Research methodology, information retrieval, and NLP applications in education.

You are reading a PhD research outline submitted by a doctoral applicant. Your job is to give the applicant the most honest, detailed, and useful feedback possible — the kind that will either get the proposal approved or identify exactly what must be fixed before it can be.

Your review must cover:

1. **Novelty and contribution** — Is the contribution claim convincing? Is the three-gap framing (corpus type, deployment context, evaluation standard) defensible? What will examiners push back on hardest?

2. **Methodological rigour** — Is the DSR framing appropriate? Is the generalisation strategy credible for a single-case study? Are the evaluation protocols (50-query set, RAGAS, inter-annotator agreement) sufficient for a PhD?

3. **Literature coverage** — Are there obvious gaps in the literature review? Are the theoretical lenses (CLT, SDL, transactional distance) well integrated or decorative?

4. **Scope and feasibility** — Is the scope appropriate for a 3-year PhD? What risks are underestimated?

5. **Writing and structure** — Is the document well-structured for a doctoral committee? Is anything unclear or poorly positioned?

6. **Overall recommendation** — Would you accept this outline as submitted, request minor revisions, or request major revisions? Be specific about what would need to change.

Be rigorous. Do not soften criticism. This applicant needs to know exactly where the weak points are."""


EMAIL_SYSTEM = """You are Prof Judy van Biljon — NRF C1-rated researcher at UNISA's School of Computing, with an h-index of 19, specialising in HCI4D (Human-Computer Interaction for Development), ML4D (Machine Learning for Development), and ODeL technology adoption. You have published on LMS usability in ODeL environments and on applying NLP techniques to research landscape analysis.

You have just received a cold PhD supervision enquiry email from a prospective doctoral student. Read it as you actually would — as a senior researcher with limited time, a full supervision load, and a good nose for whether an applicant has done their homework.

Your feedback must cover:

1. **First impression** — Does the email demonstrate genuine engagement with your work, or does it feel generic? Would it catch your attention in a crowded inbox?

2. **Accuracy of paper references** — The applicant references your 2022 paper with Lehong and Sanders, and your 2021 and 2023 NLP papers. Are the characterisations of those papers accurate and appropriate?

3. **Research alignment** — Does the proposed research genuinely align with your supervision programme? What would make it a stronger fit — or a weaker one?

4. **Applicant credibility** — Does the background paragraph (MSc DSAI with Distinction, production AI systems) present a credible doctoral candidate?

5. **Red flags** — Is there anything in the email that would make you hesitant to respond positively? Anything that seems presumptuous, inaccurate, or poorly judged?

6. **Co-supervision suggestion** — The applicant names Prof van der Poel as a potential co-supervisor. How does this land?

7. **Overall response** — Would you respond positively, request more information, or decline? What would you want to see in a follow-up?

Be honest. You receive many enquiries. What would actually make you say yes?"""

# ---------------------------------------------------------------------------
# Call o3
# ---------------------------------------------------------------------------

def call_o3(system_prompt: str, document: str, label: str) -> str:
    print(f"[o3] Sending {label} to o3 (reasoning_effort=high)...", flush=True)
    response = client.chat.completions.create(
        model=MODEL,
        reasoning_effort="high",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": document},
        ],
    )
    text = response.choices[0].message.content
    tokens = response.usage
    print(f"[o3] {label}: {tokens.prompt_tokens} prompt + {tokens.completion_tokens} completion tokens", flush=True)
    return text

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    outline_text = OUTLINE.read_text(encoding="utf-8")
    email_text   = EMAIL.read_text(encoding="utf-8")

    # --- Research outline feedback ---
    print("\n=== RESEARCH OUTLINE ===")
    outline_feedback = call_o3(OUTLINE_SYSTEM, outline_text, "research-outline")

    outline_out = OUT_DIR / "o3-feedback-research-outline.md"
    outline_out.write_text(
        f"# o3 Feedback — Research Outline\n\n"
        f"**Model:** {MODEL} (reasoning_effort=high)  \n"
        f"**Document:** admin/research-outline/research-outline-working.md  \n"
        f"**Generated:** {timestamp}\n\n"
        f"---\n\n"
        + outline_feedback,
        encoding="utf-8"
    )
    print(f"[o3] Written: {outline_out}")

    # --- Email feedback ---
    print("\n=== OUTREACH EMAIL ===")
    email_feedback = call_o3(EMAIL_SYSTEM, email_text, "email-van-biljon")

    email_out = OUT_DIR / "o3-feedback-email-van-biljon.md"
    email_out.write_text(
        f"# o3 Feedback — Van Biljon Outreach Email\n\n"
        f"**Model:** {MODEL} (reasoning_effort=high)  \n"
        f"**Document:** admin/outreach/email-van-biljon.md  \n"
        f"**Generated:** {timestamp}\n\n"
        f"---\n\n"
        + email_feedback,
        encoding="utf-8"
    )
    print(f"[o3] Written: {email_out}")

    # --- Summary ---
    summary_out = OUT_DIR / "o3-feedback-summary.md"
    summary_out.write_text(
        f"# o3 Feedback Summary\n\n"
        f"**Model:** {MODEL} (reasoning_effort=high)  \n"
        f"**Generated:** {timestamp}\n\n"
        f"---\n\n"
        f"## Research Outline — Key Points\n\n"
        f"Full report: `pipeline-outputs/o3-feedback-research-outline.md`\n\n"
        + _extract_key_points(outline_feedback, "outline") +
        f"\n\n---\n\n"
        f"## Outreach Email — Key Points\n\n"
        f"Full report: `pipeline-outputs/o3-feedback-email-van-biljon.md`\n\n"
        + _extract_key_points(email_feedback, "email"),
        encoding="utf-8"
    )
    print(f"[o3] Written: {summary_out}")
    print("\nDone.")


def _extract_key_points(text: str, doc_type: str) -> str:
    """Pull out the recommendation / overall response section if present."""
    lines = text.splitlines()
    # Look for the overall recommendation / response section
    capture = False
    captured = []
    for line in lines:
        lower = line.lower()
        if any(kw in lower for kw in ["overall recommendation", "overall response", "red flag", "would you respond"]):
            capture = True
        if capture:
            captured.append(line)
        if capture and len(captured) > 30:
            break
    if captured:
        return "\n".join(captured[:30])
    # Fallback: last 20 lines
    return "\n".join(lines[-20:])


if __name__ == "__main__":
    main()
