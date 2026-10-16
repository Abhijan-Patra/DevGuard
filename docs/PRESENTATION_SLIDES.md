# DevGuard — Hackathon Presentation (10 Slides)

**Deck Format:** 10 Slides (under 10 slides limit)  
**Tone:** Developer-to-developer, authentic, honest, zero marketing fluff  
**PowerPoint File:** [`DevGuard_Deck.pptx`](../DevGuard_Deck.pptx)  
**Interactive Web Slides:** [`docs/presentation.html`](presentation.html)  

---

## Slide 1: Title Slide

### DevGuard: Stop accidentally leaking private keys & customer data to AI tools.
- **Subtitle:** A local-first privacy guard & automated bug fixer powered by Gemma 4. No invasive screen recorders. No cloud prompts. Zero fluff.
- **Tags:** Local Gemma 4 E4B (Ollama) • Zero Screen Recording • Fail-Closed Privacy
- **Track:** Best Use of Gemma 4 | Open Source AI

> **Speaker Notes (0:00 - 0:30):**  
> *"Hey everyone! We're Team DevGuard. Like many of you, we use AI coding tools every single day—Copilot, Cursor, Claude Code. But there's a huge elephant in the room: every time you paste a stack trace or terminal output into an AI chat, you risk sending production database passwords, AWS tokens, or customer emails straight to third-party servers. Today, we're showing DevGuard: a fast, local-first privacy guard and background repair agent powered completely on-device by Gemma 4."*

---

## Slide 2: The Problem Every Dev Knows

### We've All Done This at 2 AM...
1. **The 'Copy-Paste' Mistake (Accidental Secret Leaks):**
   - You get a nasty crash in `auth.py`.
   - You copy the entire traceback into ChatGPT or Cursor.
   - Oops: You just sent a live customer email and AWS token straight to an external cloud server.
   - Now that secret sits in external training and audit logs.
2. **The 'Corporate Spyware' Fix (Overly Invasive Tooling):**
   - Company IT panics and installs 'monitoring agents'.
   - They record your screen, log every keystroke, and kill your laptop battery.
   - Engineers feel surveilled, and the tools don't even understand code context.
   - There has to be a smarter, non-creepy way.
3. **The Risky AI Patches (Concurrency & Broken Code):**
   - You ask an AI tool to fix a failing test.
   - While it generates code, you edit a nearby function.
   - You apply the AI suggestion — and it silently overwrites your fresh work!
   - Plus, nobody tested it in a clean sandbox.

> **Speaker Notes (0:30 - 1:00):**  
> *"Every developer knows the 2 AM feeling: an API is failing, you copy the full stack trace into an AI chat, and realize two seconds later that you just pasted a production database URL with the real password. Companies usually respond by installing creepy employee surveillance software that records your screen. We built DevGuard to protect developer privacy without spying on them."*

---

## Slide 3: Our Solution

### How DevGuard Works: Two Local Agents, Zero Spying
```
               ┌──────────────────────────────────────────────┐
               │         Developer Action / Code Event        │
               └──────────────────────┬───────────────────────┘
                                      │
                ┌─────────────────────┴─────────────────────┐
                ▼                                           ▼
  [ 🛡️ Agent 1: Fast Privacy Gate ]            [ 🔧 Agent 2: Sandbox Fixer ]
• Sits between editor & network             • Runs in background on test failures
• Millisecond synchronous Gemma 4 scan      • Isolated Docker container execution
• Exact-span type-safe redaction            • Proves fix with independent pytest
• Fail-closed (holds if offline)            • Base-hash check: rejects stale edits
```
- **Local Gemma 4 E4B (`gemma4:e4b-it-q4_K_M`):** A single 4B quantized model running locally via Ollama.
- **Fail-Closed Privacy:** If Ollama drops or times out, prompts are safely held (`REVIEW`). Never leaks by default.

> **Speaker Notes (1:00 - 1:30):**  
> *"DevGuard uses a dual-agent architecture powered by a single quantized Gemma 4 model running locally on your laptop. Agent 1 is a synchronous privacy gate: it cleans prompts and clipboard text before they ever leave your machine. Agent 2 is a background repair agent: when tests fail, it spins up an isolated Docker sandbox, diagnoses the bug, and verifies the fix."*

---

## Slide 4: Feature 1 — Precision Privacy Gate

### Clean Secrets, Keep Debug Context
- **Why Simple Regex Fails:**
  - Regex is great for standard AWS keys (`AKIA...`), but terrible at conversational sentences.
  - What about: *"Use db password SuperSecretPass2026!"*?
  - Or customer PII buried inside JSON response dumps?
  - Gemma 4 understands semantics: It spots private context that regex misses.
  - Result: Type-safe replacements (`[CUSTOMER_EMAIL_1]`, `[REDACTED_PASSWORD_01]`).
- **Live Example:**
  ```text
  // BEFORE: Raw error with live secret
  ValueError: Auth failed for contact@enterprise.com
  Token: ghp_synthetic_pat_1234567890abcdef
  File: auth.py:54 in verify_session()

  // AFTER: DevGuard Gate output
  ValueError: Auth failed for [CUSTOMER_EMAIL_1]
  Token: [REDACTED_SECRET_TOKEN_1]
  File: auth.py:54 in verify_session()

  // DECISION: SANITIZE (Sent safely to assistant!)
  ```

> **Speaker Notes (1:30 - 2:00):**  
> *"Notice the before and after on this slide. Most tools either do nothing or block the entire prompt. DevGuard redacts only the sensitive tokens—the customer email and GitHub token—while keeping the line numbers, exception class, and file paths 100% intact. The AI assistant has all the facts to fix the bug, but never sees private bytes."*

---

## Slide 5: Feature 2 — Smart Clipboard

### Clipboard Watcher: One Click to 'Copy Cleaned'
- **The Everyday Clipboard Trap:**
  - You copy a Postgres connection string from your `.env` file.
  - You want to ask AI: *"Why does this query hang?"*
  - Your clipboard currently has the live database password in plaintext.
  - DevGuard's macOS text watcher flags it immediately: **State: SENSITIVE**.
  - **Strictly Opt-In:** Starts OFF. Only watches text when you turn it on.
- **One Click: 'Copy Cleaned Text':**
  - Dashboard shows a sanitized preview right away.
  - Click one button: **'Copy Cleaned Text'**.
  - Your clipboard is replaced with the safe version: `postgres://admin:REDACTED_PASS@db.internal:5432/app`
  - **Anti-Scan Loop:** We hash the cleaned text so the watcher doesn't re-trigger itself.
  - Zero raw clipboard history is ever saved to disk.

> **Speaker Notes (2:00 - 2:30):**  
> *"We copy-paste database strings and API keys constantly. DevGuard includes an opt-in macOS text pasteboard watcher. When it detects a secret in your clipboard, it flags it as SENSITIVE in the dashboard and gives you a one-click 'Copy Cleaned Text' button. You click it, and your clipboard is instantly replaced with safe, sanitized text without infinite re-scan loops."*

---

## Slide 6: Feature 3 — Autonomous Sandbox Repair

### Autonomous Repair: Real Docker Tests, No Hallucinations
- **How It Actually Diagnoses:**
  1. Pytest fails in your demo cart service.
  2. DevGuard spins up a disposable Docker container.
  3. Baseline check: Confirms the test genuinely fails.
  4. Gemma 4 reads the code and error output using scoped tools.
  5. Gemma writes a candidate patch.
  6. Re-runs the test suite in isolation. If it doesn't pass 100%, patch is thrown out!
- **Verified Candidate Diff:**
  ```diff
  // Incident: inc-cart-01 (Cart quantity regression)
  // Baseline test: FAIL (3 * $125 returned $125)

  --- a/demo/backend/cart.py
  +++ b/demo/backend/cart.py
  @@ -6,3 +6,3 @@
  -    total += item['price']
  +    total += item['quantity'] * item['price']

  // Sandbox Test Verification:
  // pytest trusted_tests/test_cart.py
  // 3 passed in 0.14s (READY_FOR_REVIEW)
  ```

> **Speaker Notes (2:30 - 3:00):**  
> *"When a backend test fails, you don't have to copy-paste logs into an external AI. DevGuard spins up an isolated Docker container, runs a baseline test to confirm the bug, and lets Gemma 4 explore the code using restricted tools. Gemma proposes a fix, tests it against immutable test oracles, and presents a clean diff for you to review."*

---

## Slide 7: Feature 4 — Concurrency Guard

### Concurrency Protection: 'Don't Overwrite My Code!'
- **The Problem With Auto-Apply:**
  - Imagine an AI agent quietly modifying your files while you're typing.
  - It's a recipe for merge conflicts and lost code.
  - DevGuard uses cryptographic base-hashes (SHA-256):
  - When an incident starts, we record the hash of `cart.py`.
  - Before applying any patch, we check if the file changed on disk.
- **HTTP 409 Conflict: Safe by Default:**
  - If you edited `cart.py` while Gemma was thinking:
  - DevGuard immediately blocks the apply with **HTTP 409 STALE_CONTENT**.
  - Your code is completely protected.
  - You get to decide: discard your edits or generate a fresh patch.
  - **Human operator has final authority.**

> **Speaker Notes (3:00 - 3:30):**  
> *"Here is a classic problem with AI agents: race conditions. What if you edit a file while the AI is in the middle of preparing a patch? If it blindly applies, your work is erased. DevGuard cryptographically hashes files. If you touched the file, it rejects the patch with HTTP 409 Conflict. The human always holds final apply authority."*

---

## Slide 8: The Experience

### The Operator Dashboard: Clean & Honest
- **5 Focused Views:**
  1. 🛡️ **Privacy Gate:** Interactive prompt evaluator with scenario prefill selectors.
  2. 📋 **Text Clipboard:** Real-time capture status, safe previews & 'Copy Cleaned'.
  3. 🔍 **Coverage Matrix:** Honest capability boundaries (`VERIFIED`, `PARTIAL`, `UNSUPPORTED`).
  4. 🔧 **Patch Review:** Interactive side-by-side unified diffs & sandbox test proof.
  5. 📜 **Audit Stream:** Chronological event logs with zero raw secrets.
- **Honest Fixture Mode:**
  - Big disclaimer banner when running offline.
  - Synthetic demo data never pretends to be real model output.
  - Judges can see exactly what is running live vs simulated.
  - No fake 99% accuracy progress bars.

> **Speaker Notes (3:30 - 4:00):**  
> *"Our operator dashboard is built with Streamlit. It's clean, responsive, and radically honest. When running offline without a GPU, it shows an unmistakable Fixture Mode banner. We never pretend simulated mock data is real model output."*

---

## Slide 9: Real-World Impact

### Who Needs DevGuard Today?
1. **Dev Teams Using AI (Enterprise Compliance):**
   - Every engineer using Cursor, Copilot, or Claude Code.
   - Management wants to say 'yes' to AI productivity, but security says 'no' due to secret leaks.
   - DevGuard is the bridge: Devs keep their AI tools, security sleeps soundly at night.
2. **FinTech & Healthcare (Regulated Environments):**
   - Teams handling HIPAA health data or credit card numbers.
   - When an API crashes, stack traces often contain real customer data.
   - DevGuard sanitizes patient/account IDs automatically so devs can debug legally.
3. **On-Call Bug Triage (CI/CD Acceleration):**
   - When tests break in staging or CI, engineers waste hours digging through logs.
   - Repair agent runs in the background, identifies the bug, and prepares a verified PR.
   - Turns a 2-hour debugging session into a 2-minute review.

> **Speaker Notes (4:00 - 4:30):**  
> *"Who is this for? First: any engineering team adopting AI coding assistants where security teams are worried about data leaks. Second: FinTech and healthcare developers handling HIPAA or PCI data. And third: DevOps and on-call teams where background repair cuts test triage time from hours to minutes."*

---

## Slide 10: Summary

### Under the Hood & Why Gemma 4
- **Our Stack:**
  - **Model:** Gemma 4 E4B (`gemma4:e4b-it-q4_K_M`) via Ollama (100% on-device).
  - **Backend:** FastAPI + Pydantic v2 (async, strictly typed).
  - **Scanner:** Gitleaks pattern detector + Gemma semantic classifier.
  - **Sandboxing:** Scoped Docker runner with immutable test mounts.
  - **UI:** Streamlit dashboard with real-time API client.
  - **Tested:** Over 130 unit, integration, and UI tests passing.
- **Why DevGuard Wins:**
  1. **Real Gemma 4 Power:** Small 4B footprint fits on laptops, fast enough for real-time prompts.
  2. **Zero Surveillance:** We respect developers. No screen recording, no keylogging.
  3. **Fail-Closed:** Privacy isn't an afterthought. If offline, data is held.
  4. **Built for Engineers:** Clean diffs, concurrency safety, and transparent logs.
  - Open source on GitHub: `github.com/Abhijan-Patra/DevGuard`

> **Speaker Notes (4:30 - 5:00):**  
> *"To wrap up: DevGuard proves that you don't need cloud LLMs or intrusive screen monitors to protect developers. A fast, local 4B model like Gemma 4 can guard prompts and heal code right on your machine. Thank you so much, and we'd love to take your questions!"*
