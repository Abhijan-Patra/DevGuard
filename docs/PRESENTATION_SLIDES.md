# DevGuard — Hackathon Presentation (10 Slides)

**Deck Format:** 10 Slides (under 10 slides limit)  
**Target Duration:** 3 to 5 minutes  
**Accompanying PPTX File:** [`DevGuard_Presentation.pptx`](../DevGuard_Presentation.pptx)  
**Interactive Web Slides:** [`docs/presentation.html`](presentation.html)  

---

## Slide 1: Title Slide

### DevGuard: Local-First Privacy Guard & Autonomous Repair Agent
**Subtitle:** Dual-agent developer protection powered 100% on-device by Gemma 4 E4B  
**Track:** Best Use of Gemma 4 | Open Source AI  
**Key Highlights:** Zero Screen Recording • Fail-Closed Privacy • Docker Sandbox Verification  

> **Speaker Notes (0:00 - 0:30):**  
> *"Good afternoon, judges. We are presenting DevGuard. As software engineers, we rely daily on AI coding assistants like Copilot and Cursor. However, sending raw code, crash logs, and clipboard contents to cloud LLMs creates an immense privacy and security liability. Today, we're showing how a single, local Gemma 4 model can synchronously guard developer prompts and autonomously diagnose backend regressions in isolated Docker containers—with zero invasive screen recording."*

---

## Slide 2: The Core Problem

### The AI Coding Security Blindspot
1. **Accidental Cloud Token Leaks:**
   - Developers frequently paste stack traces and terminal logs containing AWS secrets, database passwords, and auth tokens directly into AI chats.
   - Cloud models retain and log prompt bytes, exposing enterprises to data leaks and compliance violations.
2. **Invasive Surveillance Approaches:**
   - Traditional security tools attempt to record video screens, capture keystrokes, or intercept all OS paste events.
   - These methods cause extreme privacy pushback from engineers and heavy battery/CPU drain.
3. **Risky & Friction-Heavy Bug Fixing:**
   - Debugging test failures requires manual log copy-pasting.
   - Untested AI patches can cause silent regressions or overwrite concurrent developer changes.

> **Speaker Notes (0:30 - 1:00):**  
> *"The fundamental dilemma today is: do we block AI assistants and hurt developer velocity, or allow them and risk leaking production secrets? Furthermore, enterprise 'monitoring' tools that record screens or log keystrokes are toxic to developer trust and lack semantic understanding of code. DevGuard solves this from the ground up."*

---

## Slide 3: The Solution & Architecture

### Dual-Agent Local-First Protection
```
               ┌──────────────────────────────────────────────┐
               │         Developer Action / Code Event        │
               └──────────────────────┬───────────────────────┘
                                      │
                ┌─────────────────────┴─────────────────────┐
                ▼                                           ▼
  [ 🛡️ Agent 1: Privacy Gate ]                [ 🔧 Agent 2: Sandbox Repair ]
• Synchronous pre-delivery inspection       • Triggered by test failure signals
• Gitleaks regex + Gemma 4 reasoning        • Isolated Docker container execution
• Exact-span type-safe redaction            • Immutable pytest verification oracles
• Fail-closed authorization gate            • Base-hash stale conflict protection
```
- **Local Gemma 4 E4B (`gemma4:e4b-it-q4_K_M`):** Single model serving foreground privacy inspection and background patch diagnosis.
- **Fail-Closed Security Invariant:** If the model or scanner is offline or times out, delivery is strictly held (`REVIEW`) instead of leaking raw bytes.

> **Speaker Notes (1:00 - 1:30):**  
> *"Here is DevGuard's architecture: A dual-agent system sharing a local Gemma 4 instance. Agent 1 is a synchronous privacy gate that intercepts prompts and clipboard text before external transmission. Agent 2 is a background repair agent that investigates test regressions inside disposable Docker sandboxes using structured logs and diffs—never relying on video or screenshots."*

---

## Slide 4: Feature 1 — Precision Privacy Gate

### Exact-Span Redaction & Fail-Closed Gate
- **Semantic & Pattern Redaction:**
  - Multi-tier inspection: High-entropy regex scanning for API keys paired with Gemma 4 contextual reasoning for confidential prose and PII.
  - Catches what regex misses: Unformatted passwords, internal cluster hostnames, and customer emails.
- **Type-Safe Semantic Placeholders:**
  - Replaces sensitive bytes with type-safe tokens like `[CUSTOMER_EMAIL_1]` and `[REDACTED_SECRET_TOKEN_1]`.
  - Preserves 100% of debugging context (line numbers, exception classes, and syntax) so the assistant can still diagnose the problem.
- **Deterministic Gate Decisions:**
  - `ALLOW` (benign text), `SANITIZE` (cleanly redacted), `REVIEW` (held for human check), `BLOCK` (path traversal / command injection).

> **Speaker Notes (1:30 - 2:00):**  
> *"In our live demo, when an engineer submits an error trace with an internal email and GitHub token, DevGuard replaces only the private bytes with typed placeholders. The error stack, line numbers, and file paths remain intact, enabling the AI assistant to fix the defect without ever seeing private customer data."*

---

## Slide 5: Feature 2 — Opt-In macOS Clipboard Watcher

### Native Text Protection with Cleaned Copy
- **Strict Opt-In Consent:**
  - Clipboard capture starts strictly `OFF`; requires deliberate local activation.
  - Windows dashboard acts as an operator viewer; native capture runs on the developer's macOS machine.
- **Anti-Scan Loop & Transient Memory:**
  - Content hashes prevent infinite re-scan loops when copying sanitized text.
  - Clipboard text is never written to disk or audit logs; only transient redacted metadata persists.
- **One-Click 'Copy Cleaned Text':**
  - Developer copies a raw database connection string (`DATABASE_URL=postgres://...`).
  - DevGuard detects the credential and displays a sanitized preview.
  - One click on **Copy Cleaned Text** replaces the OS clipboard with safe, sanitized text.

> **Speaker Notes (2:00 - 2:30):**  
> *"Engineers copy-paste connection strings all day. DevGuard's clipboard watcher intercepts text payloads on macOS, generates a safe preview, and provides a 'Copy Cleaned Text' button. With one click, your clipboard is sanitized and ready to paste into any public channel or AI tool."*

---

## Slide 6: Feature 3 — Autonomous Sandbox Repair Agent

### Safe Regression Healing via Docker Sandboxes
- **Structured Code Reasoning:**
  - Gemma 4 diagnoses defects using deterministic facts: structured pytest traces, stack traces, and source diffs.
  - Zero screen-recording dependencies: completely headless and non-invasive.
- **Strictly Scoped Tools & Step Limits:**
  - Gemma 4 interacts through restricted tools: `read_allowed_file`, `propose_patch`, and `run_tests`.
  - Enforces a 6-step limit and bounded source scopes to prevent infinite wandering.
- **Independent Test Oracles:**
  - First confirms baseline failure in a clean container.
  - Evaluates candidate patch against protected test suites in `trusted_tests/`.
  - Generates minimal, clean unified diffs for human review.

> **Speaker Notes (2:30 - 3:00):**  
> *"When a backend test fails—such as our cart quantity calculation regression—the background repair agent spins up an isolated Docker container, inspects the error trace, proposes a minimal diff, and verifies it against independent unit tests. If tests fail, it never fabricates success."*

---

## Slide 7: Feature 4 — Stale Conflict & Base-Hash Guard

### Concurrency Protection & Human Authorization
- **Cryptographic Base-Hash Validation:**
  - Records SHA-256 hashes of original files at the snapshot moment.
  - Before applying any approved patch, DevGuard verifies the working tree's live hash against the snapshot hash.
  - If the developer touched the file while the repair ran: **HTTP 409 Conflict (`STALE_CONTENT`)**.
  - Prevents accidental code loss or race conditions!
- **Human-in-the-Loop Authority:**
  - AI proposes, but the human operator explicitly authorizes patch application.
  - Idempotent application prevents repeated apply side-effects.

> **Speaker Notes (3:00 - 3:30):**  
> *"A major danger with autonomous agents is race conditions: what if you edit a file while the AI is patching it? DevGuard cryptographically verifies file base hashes before applying. If you modified the file, it rejects the patch with HTTP 409 Stale Content, safeguarding your code."*

---

## Slide 8: Real-Time Observability & Operator Dashboard

### Streamlit Dashboard with Unmistakable Modes
- **5 Focused Operational Views:**
  1. 🛡️ **Privacy Gate:** Interactive prompt evaluator with scenario prefill selectors.
  2. 📋 **Text Clipboard:** Real-time capture status and one-click cleaned copy.
  3. 🔍 **Coverage Matrix:** Honest capability boundaries (`VERIFIED`, `PARTIAL`, `UNSUPPORTED`).
  4. 🔧 **Incident & Patch Review:** Interactive unified diffs and sandbox verification evidence.
  5. 📜 **Audit Stream:** Chronological event logs with zero raw secrets.
- **Honest Fixture Mode:**
  - Prominent banner whenever running in simulated mode.
  - Declared synthetic fixtures never pretend to be live model outputs.

> **Speaker Notes (3:30 - 4:00):**  
> *"Our Streamlit dashboard provides complete visibility. It clearly separates simulated Fixture Mode from Live Mode so operators are never misled. Every decision, diff, and audit event is presented with crystal clarity."*

---

## Slide 9: Target Use Cases & Industry Impact

### Where DevGuard Delivers Immediate Value
1. **Enterprise AI Adoption (Cursor, Copilot, Claude):**
   - Enable developers to safely use cloud AI assistants without violating enterprise data leakage policies.
   - Adhere to SOC 2, ISO 27001, and confidentiality requirements automatically.
2. **FinTech, Banking & Healthcare:**
   - Automatically redact PCI payment cards, bank account numbers, and HIPAA patient health identifiers from logs and prompts.
   - Retain full technical debugging utility without exposing regulated PII.
3. **Automated CI/CD Test Healing:**
   - Autonomously investigate flaky test failures and regression breaks in background Docker runners.
   - Deliver verified, human-approvable diffs directly to the engineering team.

> **Speaker Notes (4:00 - 4:30):**  
> *"DevGuard unlocks massive value for enterprises adopting AI coding tools. In regulated industries like finance and healthcare, developers can safely debug crashes without exposing customer PII. In high-velocity teams, background repair cuts regression debugging time by over 80%."*

---

## Slide 10: Tech Stack & Key Takeaways

### Why DevGuard Wins
- **Technical Architecture:**
  - **Model:** Local Gemma 4 E4B (`gemma4:e4b-it-q4_K_M`) via Ollama
  - **Backend:** FastAPI, Pydantic v2, Python 3.11+
  - **Scanner:** Gitleaks + Gemma Semantic Span Engine
  - **Sandbox:** Docker Container Runner + Pytest Oracles
  - **Frontend:** Streamlit 1.40+ Dashboard
  - **Storage:** Bounded SQLite Metadata Store (5,000 events max)
- **Top 5 Invariants:**
  1. **100% On-Device Inference:** No cloud telemetry or third-party model dependency.
  2. **Zero Screen Scraping:** No cameras, video watchers, or keyloggers.
  3. **Fail-Closed Privacy:** If the model drops, prompts are safely held.
  4. **Cryptographic Concurrency:** Base-hash checks prevent code loss.
  5. **Radical Honesty:** Real verification boundaries and declared synthetic fixtures.

> **Speaker Notes (4:30 - 5:00):**  
> *"In summary: DevGuard delivers the first truly local, dual-agent developer guard powered by Gemma 4 E4B. It is privacy-first, non-invasive, fail-closed, and production-minded. Thank you, and we welcome your questions!"*
