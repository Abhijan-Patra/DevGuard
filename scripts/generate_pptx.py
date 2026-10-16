"""Generate a developer-crafted, authentic 10-slide presentation deck using python-pptx."""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path="DevGuard_Presentation.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Warm & sleek developer theme (Deep navy slate + vibrant electric blue/emerald)
    BG_COLOR = RGBColor(15, 23, 42)         # #0F172A
    CARD_BG = RGBColor(30, 41, 59)          # #1E293B
    CODE_BG = RGBColor(10, 15, 30)          # #0A0F1E
    BORDER_COLOR = RGBColor(51, 65, 85)     # #334155
    TEXT_MAIN = RGBColor(248, 250, 252)     # #F8FAFC
    TEXT_MUTED = RGBColor(148, 163, 184)    # #94A3B8
    TEXT_EMPHASIS = RGBColor(226, 232, 240) # #E2E8F0
    ACCENT_CYAN = RGBColor(56, 189, 248)    # #38BDF8
    ACCENT_GREEN = RGBColor(52, 211, 153)   # #34D399
    ACCENT_AMBER = RGBColor(251, 191, 36)   # #FBBF24
    ACCENT_ROSE = RGBColor(244, 63, 94)     # #F43F5E

    def set_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.color.rgb = BG_COLOR
        return bg

    def add_slide_header(slide, title, kicker=None):
        if kicker:
            k_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.35))
            tf_k = k_box.text_frame
            tf_k.word_wrap = True
            p_k = tf_k.paragraphs[0]
            p_k.text = kicker.upper()
            p_k.font.size = Pt(11)
            p_k.font.bold = True
            p_k.font.color.rgb = ACCENT_CYAN
            p_k.font.name = "Segoe UI"

        t_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7 if kicker else 0.5), Inches(11.5), Inches(0.8))
        tf = t_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(26)
        p.font.bold = True
        p.font.color.rgb = TEXT_MAIN
        p.font.name = "Segoe UI"

    def add_card(slide, left, top, width, height, title, body_bullets, accent=ACCENT_CYAN, subheader=None):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = BORDER_COLOR
        card.line.width = Pt(1.5)

        tx = slide.shapes.add_textbox(Inches(left + 0.3), Inches(top + 0.25), Inches(width - 0.6), Inches(height - 0.5))
        tf = tx.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(17)
        p_t.font.bold = True
        p_t.font.color.rgb = accent
        p_t.font.name = "Segoe UI"

        if subheader:
            p_sub = tf.add_paragraph()
            p_sub.text = subheader
            p_sub.font.size = Pt(11)
            p_sub.font.color.rgb = TEXT_MUTED
            p_sub.font.italic = True
            p_sub.space_after = Pt(8)
        else:
            p_t.space_after = Pt(8)

        for b in body_bullets:
            p = tf.add_paragraph()
            p.text = b
            p.font.size = Pt(13)
            p.font.color.rgb = TEXT_EMPHASIS
            p.font.name = "Segoe UI"
            p.space_after = Pt(8)

    def add_code_box(slide, left, top, width, height, code_text, label="CODE SNIPPET"):
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        box.fill.solid()
        box.fill.fore_color.rgb = CODE_BG
        box.line.color.rgb = BORDER_COLOR
        box.line.width = Pt(1)

        tx = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.15), Inches(width - 0.4), Inches(height - 0.3))
        tf = tx.text_frame
        tf.word_wrap = True

        p_lbl = tf.paragraphs[0]
        p_lbl.text = label
        p_lbl.font.size = Pt(9)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = ACCENT_CYAN
        p_lbl.font.name = "Segoe UI"
        p_lbl.space_after = Pt(6)

        for line in code_text.strip().split("\n"):
            p = tf.add_paragraph()
            p.text = line
            p.font.size = Pt(11)
            p.font.name = "Consolas"
            if line.startswith("-"):
                p.font.color.rgb = ACCENT_ROSE
            elif line.startswith("+"):
                p.font.color.rgb = ACCENT_GREEN
            elif "REDACTED" in line or "[" in line:
                p.font.color.rgb = ACCENT_AMBER
            else:
                p.font.color.rgb = TEXT_MUTED

    # -------------------------------------------------------------
    # SLIDE 1: Real Developer Title
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    set_bg(s1)

    t_box = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(3.5))
    tf1 = t_box.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "DevGuard"
    p0.font.size = Pt(60)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT_CYAN
    p0.font.name = "Segoe UI"
    p0.space_after = Pt(8)

    p1 = tf1.add_paragraph()
    p1.text = "Stop accidentally leaking private keys & customer data to AI tools."
    p1.font.size = Pt(22)
    p1.font.color.rgb = TEXT_MAIN
    p1.font.name = "Segoe UI"
    p1.space_after = Pt(14)

    p2 = tf1.add_paragraph()
    p2.text = "A local-first privacy guard & automated bug fixer powered by Gemma 4.\nNo invasive screen recorders. No cloud prompts. Zero fluff."
    p2.font.size = Pt(14)
    p2.font.color.rgb = TEXT_MUTED
    p2.font.name = "Segoe UI"

    foot = s1.shapes.add_textbox(Inches(1.0), Inches(5.8), Inches(11.3), Inches(0.8))
    p_foot = foot.text_frame.paragraphs[0]
    p_foot.text = "Team DevGuard | Hackathon 2026 | Powered by Gemma 4 E4B"
    p_foot.font.size = Pt(12)
    p_foot.font.color.rgb = ACCENT_GREEN
    p_foot.font.name = "Segoe UI"

    # -------------------------------------------------------------
    # SLIDE 2: Relatable Problem
    # -------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    set_bg(s2)
    add_slide_header(s2, "We've All Done This at 2 AM...", "The Problem")

    add_card(s2, 0.8, 1.8, 3.7, 4.8, "The 'Copy-Paste' Mistake", [
        "You get a nasty crash in auth.py.",
        "You copy the entire traceback into ChatGPT or Cursor.",
        "Oops: You just sent a live customer email and AWS token straight to an external cloud server.",
        "Now that secret sits in external model logs."
    ], ACCENT_ROSE, "Accidental credential leakage")

    add_card(s2, 4.8, 1.8, 3.7, 4.8, "The 'Corporate Spyware' Fix", [
        "Company IT panics and installs 'monitoring agents'.",
        "They record your screen, log every keystroke, and kill your laptop battery.",
        "Engineers hate it, feel watched, and it doesn't even understand code context.",
        "There has to be a smarter, non-creepy way."
    ], ACCENT_AMBER, "Overly invasive enterprise tooling")

    add_card(s2, 8.8, 1.8, 3.7, 4.8, "The Risky AI Patches", [
        "You ask AI to fix a failing test.",
        "While it generates code, you edit a nearby function.",
        "You apply the AI suggestion — and it silently overwrites your fresh work.",
        "Plus, you still had to test it by hand."
    ], ACCENT_CYAN, "Concurrency & unverified code")

    # -------------------------------------------------------------
    # SLIDE 3: The Solution
    # -------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    set_bg(s3)
    add_slide_header(s3, "How DevGuard Works: Two Local Agents, Zero Spying", "Our Solution")

    add_card(s3, 0.8, 1.8, 5.6, 4.8, "Agent 1: The Fast Privacy Gate", [
        "Sits right between your editor and the network.",
        "Runs synchronously in milliseconds using local Gemma 4.",
        "Catches API keys, emails, and internal URLs before they leave your laptop.",
        "Replaces ONLY sensitive bytes with typed placeholders.",
        "Keeps the full stack trace intact so AI can still debug it.",
        "Fail-Closed: If offline, it holds the request. Never leaks by default."
    ], ACCENT_CYAN, "Protects you before prompt sends")

    add_card(s3, 6.8, 1.8, 5.6, 4.8, "Agent 2: The Sandbox Fixer", [
        "Runs quietly in the background when tests fail.",
        "Spins up an isolated Docker container with your repo.",
        "Gemma 4 examines pytest traces & writes a minimal fix.",
        "Runs independent tests to prove the fix actually works.",
        "Base-Hash Check: Rejects the patch if you edited code in the meantime (no lost work!).",
        "Human must click 'Apply' — no auto-overwriting."
    ], ACCENT_GREEN, "Heals bugs without manual copy-paste")

    # -------------------------------------------------------------
    # SLIDE 4: Feature 1 - Privacy Gate in Action
    # -------------------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    set_bg(s4)
    add_slide_header(s4, "Privacy Gate: Clean Secrets, Keep Debug Context", "Feature 1")

    add_card(s4, 0.8, 1.8, 5.6, 4.8, "Why Simple Regex Fails", [
        "Regex is great for AWS keys (AKIA...), but terrible at confidential sentences.",
        "What about: 'Use db password SuperSecretPass2026!'?",
        "Or customer PII buried inside JSON response dumps?",
        "Gemma 4 understands semantics: It spots private context that regex misses.",
        "Result: Type-safe replacements ([CUSTOMER_EMAIL_1], [REDACTED_PASSWORD_01])."
    ], ACCENT_CYAN, "Combining Gitleaks + Gemma 4 reasoning")

    add_code_box(s4, 6.8, 1.8, 5.6, 4.8,
"""// BEFORE: Raw error with live secret
ValueError: Auth failed for contact@enterprise.com
Token: ghp_synthetic_pat_1234567890abcdef
File: auth.py:54 in verify_session()

// AFTER: DevGuard Gate output
ValueError: Auth failed for [CUSTOMER_EMAIL_1]
Token: [REDACTED_SECRET_TOKEN_1]
File: auth.py:54 in verify_session()

// DECISION: SANITIZE (Sent safely to assistant!)""",
    "LIVE EXAMPLE: EXACT-SPAN REDACTION")

    # -------------------------------------------------------------
    # SLIDE 5: Feature 2 - Clipboard
    # -------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    set_bg(s5)
    add_slide_header(s5, "Clipboard Watcher: One Click to 'Copy Cleaned'", "Feature 2")

    add_card(s5, 0.8, 1.8, 5.6, 4.8, "The Everyday Clipboard Trap", [
        "You copy a Postgres connection string from your .env file.",
        "You want to ask AI: 'Why does this query hang?'",
        "Your clipboard currently has the live database password in plaintext.",
        "DevGuard's macOS text watcher flags it immediately: State: SENSITIVE.",
        "Strictly Opt-In: Starts OFF. Only watches text when you turn it on."
    ], ACCENT_AMBER, "Opt-in text pasteboard watcher")

    add_card(s5, 6.8, 1.8, 5.6, 4.8, "One Click: 'Copy Cleaned Text'", [
        "Dashboard shows a sanitized preview right away.",
        "Click one button: 'Copy Cleaned Text'.",
        "Your clipboard is replaced with the safe version:",
        "postgres://admin:REDACTED_PASS@db.internal:5432/app",
        "Anti-Scan Loop: We hash the cleaned text so the watcher doesn't re-trigger itself.",
        "Zero raw clipboard history is ever saved to disk."
    ], ACCENT_GREEN, "Safe paste into Cursor / Slack / AI")

    # -------------------------------------------------------------
    # SLIDE 6: Feature 3 - Repair Agent
    # -------------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    set_bg(s6)
    add_slide_header(s6, "Autonomous Repair: Real Docker Tests, No Hallucinations", "Feature 3")

    add_card(s6, 0.8, 1.8, 5.6, 4.8, "How It Actually Diagnoses", [
        "1. Pytest fails in your demo cart service.",
        "2. DevGuard spins up a disposable Docker container.",
        "3. Baseline check: Confirms the test genuinely fails.",
        "4. Gemma 4 reads the code and error output using scoped tools.",
        "5. Gemma writes a candidate patch.",
        "6. Re-runs the test suite in isolation. If it doesn't pass 100%, patch is thrown out!"
    ], ACCENT_CYAN, "Deterministic test-driven loop")

    add_code_box(s6, 6.8, 1.8, 5.6, 4.8,
"""// Incident: inc-cart-01 (Cart quantity regression)
// Baseline test: FAIL (3 * $125 returned $125)

--- a/demo/backend/cart.py
+++ b/demo/backend/cart.py
@@ -6,3 +6,3 @@
-    total += item['price']
+    total += item['quantity'] * item['price']

// Sandbox Test Verification:
// pytest trusted_tests/test_cart.py
// 3 passed in 0.14s (READY_FOR_REVIEW)""",
    "VERIFIED CANDIDATE DIFF")

    # -------------------------------------------------------------
    # SLIDE 7: Feature 4 - Base Hash Protection
    # -------------------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    set_bg(s7)
    add_slide_header(s7, "Concurrency Protection: 'Don't Overwrite My Code!'", "Feature 4")

    add_card(s7, 0.8, 1.8, 5.6, 4.8, "The Problem With Auto-Apply", [
        "Imagine an AI agent quietly modifying your files while you're typing.",
        "It's a recipe for merge conflicts and lost code.",
        "DevGuard uses cryptographic base-hashes (SHA-256):",
        "When an incident starts, we record the hash of cart.py.",
        "Before applying any patch, we check if the file changed on disk."
    ], ACCENT_AMBER, "Preventing silent code loss")

    add_card(s7, 6.8, 1.8, 5.6, 4.8, "HTTP 409 Conflict: Safe by Default", [
        "If you edited cart.py while Gemma was thinking:",
        "DevGuard immediately blocks the apply with HTTP 409 STALE_CONTENT.",
        "Your code is completely protected.",
        "You get to decide: discard your edits or generate a fresh patch.",
        "Human is always in control."
    ], ACCENT_GREEN, "Human operator has final authority")

    # -------------------------------------------------------------
    # SLIDE 8: Dashboard
    # -------------------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    set_bg(s8)
    add_slide_header(s8, "The Operator Dashboard: Clean & Honest", "The Experience")

    add_card(s8, 0.8, 1.8, 3.7, 4.8, "5 Simple Views", [
        "🛡️ Privacy Gate: Test prompts with real or scenario inputs.",
        "📋 Clipboard: Status, preview, and 'Copy Cleaned'.",
        "🔍 Coverage Matrix: What's verified vs unverified.",
        "🔧 Patch Review: Side-by-side diffs & test proof.",
        "📜 Audit Stream: Filtered log of past actions."
    ], ACCENT_CYAN, "Streamlit-powered interface")

    add_card(s8, 4.8, 1.8, 3.7, 4.8, "Honest Fixture Mode", [
        "Big disclaimer banner when running offline.",
        "Synthetic demo data never pretends to be real model output.",
        "Judges can see exactly what is running live vs simulated.",
        "No fake 99% accuracy progress bars."
    ], ACCENT_AMBER, "Radical transparency")

    add_card(s8, 8.8, 1.8, 3.7, 4.8, "Security Invariants", [
        "Tokens stay server-side, never exposed in browser HTML.",
        "Cross-platform: Windows dashboard acts as a viewer for macOS capture hosts.",
        "Audit DB is private SQLite capped at 5,000 events."
    ], ACCENT_GREEN, "Zero secret leakage in UI")

    # -------------------------------------------------------------
    # SLIDE 9: Real-World Uses
    # -------------------------------------------------------------
    s9 = prs.slides.add_slide(blank_layout)
    set_bg(s9)
    add_slide_header(s9, "Who Needs DevGuard Today?", "Real-World Impact")

    add_card(s9, 0.8, 1.8, 3.7, 4.8, "Dev Teams Using AI", [
        "Every engineer using Cursor, Copilot, or Claude Code.",
        "Management wants to say 'yes' to AI productivity, but security says 'no' due to secret leaks.",
        "DevGuard is the bridge: Devs keep their AI tools, security sleeps soundly at night."
    ], ACCENT_CYAN, "Enterprise compliance")

    add_card(s9, 4.8, 1.8, 3.7, 4.8, "FinTech & Healthcare", [
        "Teams handling HIPAA health data or credit card numbers.",
        "When an API crashes, stack traces often contain real customer data.",
        "DevGuard sanitizes patient/account IDs automatically so devs can debug legally."
    ], ACCENT_GREEN, "Regulated environments")

    add_card(s9, 8.8, 1.8, 3.7, 4.8, "On-Call Bug Triage", [
        "When tests break in staging or CI, engineers waste hours digging through logs.",
        "Repair agent runs in the background, identifies the bug, and prepares a verified PR.",
        "Turns a 2-hour debugging session into a 2-minute review."
    ], ACCENT_AMBER, "CI/CD acceleration")

    # -------------------------------------------------------------
    # SLIDE 10: Tech Stack & Why Gemma 4
    # -------------------------------------------------------------
    s10 = prs.slides.add_slide(blank_layout)
    set_bg(s10)
    add_slide_header(s10, "Under the Hood & Why Gemma 4", "Summary")

    add_card(s10, 0.8, 1.8, 5.6, 4.8, "Our Stack", [
        "Model: Gemma 4 E4B (q4_K_M) via Ollama (100% on-device inference).",
        "Backend: FastAPI + Pydantic v2 (async, strictly typed).",
        "Scanner: Gitleaks pattern detector + Gemma semantic classifier.",
        "Sandboxing: Scoped Docker runner with immutable test mounts.",
        "UI: Streamlit dashboard with real-time API client.",
        "Tested: Over 130 unit, integration, and UI tests passing."
    ], ACCENT_CYAN, "Fast, lightweight & self-hosted")

    add_card(s10, 6.8, 1.8, 5.6, 4.8, "Why DevGuard Wins", [
        "1. Real Gemma 4 Power: Small 4B footprint fits on laptops, fast enough for real-time prompts.",
        "2. Zero Surveillance: We respect developers. No screen recording, no keylogging.",
        "3. Fail-Closed: Privacy isn't an afterthought. If offline, data is held.",
        "4. Built for Engineers: Clean diffs, concurrency safety, and transparent logs.",
        "Try it out today: github.com/Abhijan-Patra/DevGuard"
    ], ACCENT_GREEN, "Honest open-source AI engineering")

    prs.save(output_path)
    print(f"Developer presentation saved to {output_path}")

if __name__ == "__main__":
    create_deck()
