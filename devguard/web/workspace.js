const $ = (s) => document.querySelector(s);
const esc = (v) =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const paths = {
  shield: "M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6Z M8 12l3 3 5-6",
  grid: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  clipboard:
    "M9 4H6a2 2 0 0 0-2 2v14h16V6a2 2 0 0 0-2-2h-3 M9 2h6v5H9z M8 12h8 M8 16h5",
  code: "m8 6-6 6 6 6 M16 6l6 6-6 6 M14 3l-4 18",
  folder: "M3 7V4h7l3 3h8v14H3Z",
  activity: "M2 12h5l3-8 4 16 3-8h5",
  settings:
    "M12 3v3 M12 18v3 M3 12h3 M18 12h3 M6 6l2 2 M16 16l2 2 M6 18l2-2 M16 8l2-2 M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0",
  arrow: "M5 12h14 M13 6l6 6-6 6",
  refresh:
    "M20 7v5h-5 M4 17v-5h5 M6 7a7 7 0 0 1 12-2l2 2 M18 17a7 7 0 0 1-12 2l-2-2",
  sun: "M12 2v2 M12 20v2 M2 12h2 M20 12h2 M5 5l2 2 M17 17l2 2 M5 19l2-2 M17 7l2-2 M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0",
  lock: "M5 10h14v11H5z M8 10V7a4 4 0 0 1 8 0v3",
  check: "m5 12 4 4L19 6",
  menu: "M4 6h16 M4 12h16 M4 18h16",
  file: "M5 3h9l5 5v13H5Z M14 3v6h5 M9 13h6 M9 17h5",
  download: "M12 3v12 m-5-5 5 5 5-5 M4 16v5h16v-5",
  pause: "M8 5v14 M16 5v14",
  play: "m7 4 14 8-14 8Z",
  x: "m6 6 12 12 M18 6 6 18",
};
const icon = (n) =>
  `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[n] || paths.shield}"/></svg>`;
const nav = [
  ["overview", "grid", "Overview"],
  ["privacy", "shield", "Context gate"],
  ["clipboard", "clipboard", "Text clipboard"],
  ["repairs", "code", "Backend repairs"],
  ["projects", "folder", "Projects"],
  ["activity", "activity", "Activity"],
  ["evidence", "check", "Verification"],
  ["system", "settings", "System & coverage"],
];
const publicDemo = document.body.dataset.publicDemo === "1";
const state = {
  connected: publicDemo,
  status: null,
  projects: [],
  incidents: [],
  events: [],
  cursor: "0",
  coverage: [],
  selected: null,
  run: null,
  patch: null,
  result: null,
  source: false,
  composer: null,
  busy: false,
  privacyMode: "prompt",
  privacyDraft: {},
  filter: "",
  keys: {},
  authFailure: false,
};
let view = location.hash.slice(1) || "overview";
if (!nav.some((n) => n[0] === view)) view = "overview";
try {
  document.documentElement.dataset.theme =
    localStorage.getItem("devguard-theme") || "dark";
} catch {}
class ApiError extends Error {
  constructor(code, status) {
    super(code);
    this.code = code;
    this.status = status;
  }
}
function publicRead(path) {
  const repair = {
    configured: false,
    available: false,
    state: "UNAVAILABLE",
    reason_code: "LOCAL_RUNTIME_REQUIRED",
  };
  const clipboard = {
    supported: false,
    enabled: false,
    state: "OFF",
    capture_host_id: "Local Mac required",
    content_version: 0,
    safe_preview: null,
    can_copy_cleaned: false,
  };
  if (path === "/status")
    return {
      phase: "PUBLIC_READ_ONLY_TOUR",
      runtime: {
        model: "gemma4:e4b-it-q4_K_M",
        model_ready: false,
        reason_code: "LOCAL_RUNTIME_REQUIRED",
      },
      clipboard,
      repair,
      credential_scanner_available: false,
      audit: { durable: false },
      monitoring: { automatic: false, watched_projects: 0 },
    };
  if (path === "/projects")
    return {
      projects: [
        {
          project_id: "demo-cart-example",
          source_files: ["cart.py", "main.py"],
          writable_files: ["cart.py"],
          checks: ["cart"],
          watch: { enabled: false },
        },
      ],
    };
  if (path === "/incidents") return { incidents: [], repair };
  if (path === "/coverage")
    return {
      capabilities: [
        {
          capability: "public_feature_tour",
          status: "PARTIAL",
          limitations:
            "Read-only presentation. No model inference, native capture or repair execution is hosted here.",
        },
        {
          capability: "recorded_local_trials",
          status: "PARTIAL",
          limitations:
            "Real single-laptop Gemma, Docker, native text and delivery measurements are on the Verification page. Their scope and mismatches are preserved.",
        },
        {
          capability: "recorded_native_cli_boundaries",
          status: "PARTIAL",
          limitations:
            "Recorded CLI hook/MCP trials used real Gemma and a synthetic local coding-provider receiver. This tour does not install hooks or prove cloud/desktop coverage.",
        },
      ],
    };
  if (path.startsWith("/events")) return { events: [], next_cursor: "0" };
  if (path === "/composer") return { text: null, expires_in_seconds: 0 };
  if (path === "/scheduler/status")
    return { automatic: false, quiet_seconds: 60, watched_projects: 0 };
  throw new ApiError("LOCAL_RUNTIME_REQUIRED", 403);
}

async function api(path, { method = "GET", body, timeout = 25000 } = {}) {
  if (publicDemo) {
    if (method !== "GET") throw new ApiError("PUBLIC_TOUR_READ_ONLY", 403);
    return publicRead(path);
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch("/api/v1" + path, {
      method,
      credentials: "same-origin",
      headers: {
        "X-DevGuard-Workspace": "1",
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
    const data = await response.json();
    if (!response.ok)
      throw new ApiError(data.error?.code || "REQUEST_HELD", response.status);
    return data;
  } catch (e) {
    if (e.name === "AbortError") throw new ApiError("REQUEST_TIMED_OUT", 0);
    throw e;
  } finally {
    clearTimeout(timer);
  }
}
function toast(message, error = false) {
  const box = document.createElement("div");
  box.className = "toast" + (error ? " error" : "");
  box.textContent = message;
  $("#notifications").append(box);
  setTimeout(() => box.remove(), 6000);
}
function problem(e) {
  if (e.status === 401) {
    state.connected = false;
    state.result = null;
    state.privacyDraft = {};
    state.composer = null;
    render();
  }
  toast(
    (e.code || "CONNECTION_UNAVAILABLE").replaceAll("_", " ") +
      ". The action has not been confirmed.",
    true,
  );
}
function badge(text, tone) {
  const good = [
    "ALLOW",
    "SANITIZE",
    "READY",
    "PASS",
    "READY_FOR_REVIEW",
    "APPLIED",
    "VERIFIED",
    "MODEL_READY",
  ];
  const bad = ["BLOCKED", "BLOCK", "FAILED", "ERROR", "FAIL", "OBSOLETE"];
  return `<span class="badge ${tone || (good.includes(text) ? "good" : bad.includes(text) ? "bad" : "warn")}">${esc(text || "UNAVAILABLE").replaceAll("_", " ")}</span>`;
}
function button(label, action, cls = "", disabled = false) {
  return `<button type="button" class="btn ${cls}" data-action="${action}" ${disabled ? "disabled" : ""}>${label}</button>`;
}
const empty = (title, body, glyph = "shield") =>
  `<div class="empty">${icon(glyph)}<h3>${esc(title)}</h3>${esc(body)}</div>`;
const heading = (tag, title, sub, actions = "") =>
  `<div class="page-head"><div><div class="eyebrow">${tag}</div><h1>${title}</h1><p class="subtitle">${sub}</p></div><div class="actions">${actions}</div></div>`;
const stamp = (t) =>
  t
    ? new Date(t).toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "—";
const field = (label, name, value = "", placeholder = "", type = "text") =>
  `<label class="field"><span>${label}</span><input name="${name}" type="${type}" value="${esc(value)}" placeholder="${esc(placeholder)}" maxlength="512"></label>`;
const select = (label, name, options, value) =>
  `<label class="field"><span>${label}</span><select name="${name}">${options.map(([v, t]) => `<option value="${esc(v)}" ${v === value ? "selected" : ""}>${esc(t)}</option>`).join("")}</select></label>`;
const projectOptions = () =>
  state.projects.map((p) => [p.project_id, p.project_id]);
function eventTable(events) {
  if (!events.length)
    return empty(
      "A clean start",
      "Redacted events appear here after an inspection or repair.",
      "activity",
    );
  return `<div class="table-wrap"><table><thead><tr><th>EVENT</th><th>STATE</th><th>DETAIL</th><th>TIME</th></tr></thead><tbody>${events.map((e) => `<tr><td>${esc(e.kind)}</td><td>${badge(e.state)}</td><td>${esc(e.redacted_summary)}</td><td class="muted">${esc(stamp(e.timestamp))}</td></tr>`).join("")}</tbody></table></div>`;
}
function render() {
  if (!state.connected) {
    $("#app").innerHTML =
      `<section class="connect-card"><span class="brand-mark">d.</span><div class="eyebrow">YOUR LAPTOP. YOUR CONTROL.</div><h1>A quieter way<br>to build with AI.</h1><p>Guard the context you share. Investigate backend bugs. Review verified changes before they reach your code.</p><div class="notice">This is the real local workspace. Connecting authorizes this browser to use the local operator controls for eight hours. Clipboard capture and file watching stay off until you enable them.</div>${button(icon("lock") + " Connect this browser", "connect", "primary", state.busy)}<p class="caption">127.0.0.1 · No cloud model · No screen recording</p></section>`;
    return;
  }
  const s = state.status,
    r = s?.runtime,
    ready = r?.model_ready;
  $("#app").innerHTML =
    `<div class="shell"><aside class="sidebar"><a class="brand" href="#overview"><span class="brand-mark">d.</span><span>devguard<small>LOCAL AGENT WORKSPACE</small></span></a><div class="nav-label">WORKSPACE</div><nav aria-label="Workspace">${nav
      .slice(0, 5)
      .map(
        ([id, i, label]) =>
          `<a class="nav-item ${view === id ? "active" : ""}" href="#${id}" ${view === id ? 'aria-current="page"' : ""}>${icon(i)}${label}${id === "repairs" ? `<em>${state.incidents.length || "—"}</em>` : ""}</a>`,
      )
      .join(
        "",
      )}</nav><div class="nav-label">OBSERVABILITY</div><nav aria-label="Observability">${nav
      .slice(5)
      .map(
        ([id, i, label]) =>
          `<a class="nav-item ${view === id ? "active" : ""}" href="#${id}">${icon(i)}${label}</a>`,
      )
      .join(
        "",
      )}</nav><div class="side-bottom"><div class="engine-mini"><small>INFERENCE ENGINE</small><b><span class="dot ${ready ? "" : "off"}"></span>Gemma 4 E4B</b><p>${ready ? "Pinned & available locally" : "Unavailable · requests held"}</p></div><div class="side-foot"><span>ONE MACHINE / LOCAL</span><button class="icon-btn" data-action="theme" aria-label="Toggle color theme">${icon("sun")}</button></div></div></aside><div class="content"><header class="topbar"><div class="crumb"><button class="icon-btn menu-toggle" data-action="menu" aria-label="Toggle navigation">${icon("menu")}</button><span>Workspace</span><span>/</span><b>${nav.find((n) => n[0] === view)?.[2] || "Overview"}</b></div><div class="top-right"><span class="host-tag">${publicDemo ? "READ-ONLY TOUR" : "127.0.0.1 : " + esc(location.port)}</span><span class="connection"><span class="dot"></span>${publicDemo ? "Public demo" : "Local connection"}</span><button class="icon-btn" data-action="refresh" aria-label="Refresh workspace">${icon("refresh")}</button><div class="avatar" title="Local operator">YOU</div></div></header><main id="main">${{ overview, privacy, clipboard, repairs, projects, activity, system, evidence }[view]()}<footer class="footer"><span>DEVGUARD / Guarded context. Verified changes.</span><span>Local Gemma · No screenshot dependency · <a href="https://github.com/Abhijan-Patra/DevGuard" target="_blank" rel="noreferrer">Source ↗</a></span></footer></main></div></div>`;
  if (publicDemo) {
    document
      .querySelector("main")
      .insertAdjacentHTML(
        "afterbegin",
        '<div class="notice warn public-banner"><b>PUBLIC READ-ONLY FEATURE TOUR</b><br>No live inference or device access is hosted here. Controls are disabled; example project metadata is illustrative. Real Gemma, clipboard and Docker workflows run on the local Mac. Open Verification for recorded experiments and limitations. <a href="https://github.com/Abhijan-Patra/DevGuard/blob/main/docs/INSTALL.md" target="_blank" rel="noreferrer">Install DevGuard ↗</a></div>',
      );
    document
      .querySelectorAll("button,input,select,textarea")
      .forEach((element) => {
        if (
          !["theme", "menu", "export-evidence"].includes(
            element.dataset.action,
          ) &&
          !element.dataset.mode
        )
          element.disabled = true;
      });
  }
  if (state.busy) {
    document
      .querySelectorAll(
        "#inspect-form input, #inspect-form select, #inspect-form textarea, #inspect-form button, [data-mode]",
      )
      .forEach((element) => (element.disabled = true));
  }
}
function overview() {
  const s = state.status || {},
    rt = s.runtime || {},
    c = s.clipboard || {},
    r = s.repair || {};
  const open = state.incidents.filter(
    (i) => i.status === "READY_FOR_REVIEW",
  ).length;
  return `${heading("CONTROL PLANE / OVERVIEW", "Build freely. Share deliberately.", "Your private development workspace, with the checks and evidence in view.")}<div class="grid hero-grid"><section class="panel hero"><span class="tag good">${icon("lock")} PRIVATE BY DESIGN</span><h1>Less exposure.<br><span>More control.</span></h1><p>Keep useful debugging context. Leave sensitive details behind. Let your local agent investigate while you stay in charge.</p><div class="actions"><a class="btn primary" href="#privacy">Inspect context ${icon("arrow")}</a><a class="btn" href="#repairs">Review repairs</a></div><div class="orbit"></div></section><section class="panel hero-status"><div class="panel-head"><h2>Local control plane</h2><span class="caption">${publicDemo ? "LOCAL RUNTIME REQUIRED" : "LIVE"}</span></div><div class="status-row"><span class="muted">Gemma 4 E4B</span>${badge(rt.model_ready ? "MODEL_READY" : rt.reason_code)}</div><div class="status-row"><span class="muted">Credential scanner</span>${badge(s.credential_scanner_available ? "READY" : "UNAVAILABLE")}</div><div class="status-row"><span class="muted">Docker repair</span>${badge(r.available ? "READY" : r.reason_code)}</div><div class="status-row"><span class="muted">Audit storage</span><b>${s.audit?.durable ? "Persistent · redacted" : "Session only"}</b></div></section></div><div class="grid g4"><div class="panel stat"><small>Guarded inspections</small><strong>${state.events.filter((e) => e.kind === "guard.decision").length}</strong><p>In loaded audit records</p></div><div class="panel stat"><small>Text clipboard</small><strong>${c.enabled ? "Watching" : "Off"}</strong><p>${c.enabled ? esc(c.state) : "Only starts with your consent"}</p></div><div class="panel stat"><small>Review queue</small><strong>${open.toString().padStart(2, "0")}</strong><p>Verified candidates awaiting review</p></div><div class="panel stat"><small>Registered projects</small><strong>${state.projects.length.toString().padStart(2, "0")}</strong><p>${s.monitoring?.watched_projects || 0} watched · ${esc(r.state || "unavailable").toLowerCase()} worker</p></div></div><div class="section-row"><h2>Your next move</h2><span class="caption">EXPLICIT ACTIONS / REAL EVIDENCE</span></div><div class="grid g3">${[
    [
      "shield",
      "privacy",
      "Inspect before sharing",
      "Prompts and approved source go through rules, local Gemma and a final scan.",
    ],
    [
      "clipboard",
      "clipboard",
      "Keep copies intentional",
      "Opt in to future text copies. Review and copy a version-bound cleaned result.",
    ],
    [
      "code",
      "repairs",
      "Fix with evidence",
      "Reproduce a failure, investigate in a snapshot and review independently tested changes.",
    ],
  ]
    .map(
      ([i, v, t, d]) =>
        `<a class="panel workflow" href="#${v}"><span class="glyph">${icon(i)}</span><span class="arrow">${icon("arrow")}</span><h3>${t}</h3><p>${d}</p></a>`,
    )
    .join(
      "",
    )}</div><div class="section-row"><h2>Recent activity</h2><a class="btn text" href="#activity">View audit ${icon("arrow")}</a></div><section class="panel">${eventTable(state.events.slice(-5).reverse())}</section>`;
}
function privacy() {
  const result = state.result,
    d = state.privacyDraft || {},
    p = state.projects.find(
      (x) => x.project_id === (d.project_id || state.projects[0]?.project_id),
    );
  const input =
    state.privacyMode === "prompt"
      ? `${field("Active task", "task", d.task || "", "What are you debugging?")}<label class="field"><span>Context to inspect</span><textarea name="text" maxlength="32768" placeholder="Paste a prompt, a short error report or a source excerpt. Nothing is sent to an external assistant.">${esc(d.text || "")}</textarea><small>2 KiB contextual analysis budget. Larger inputs are held, never silently truncated.</small></label><div class="form-row">${select(
          "Text surface",
          "surface",
          [
            ["explicit_prompt", "Prompt"],
            ["tool_result", "Tool result"],
            ["file_read", "Source excerpt"],
          ],
          d.surface || "explicit_prompt",
        )}${select(
          "Destination",
          "destination",
          [
            ["local-composer", "Local context composer"],
            ["local-preview", "Preview only"],
          ],
          d.destination || "local-composer",
        )}</div>`
      : `${select("Registered project", "project_id", projectOptions(), p?.project_id)}${select(
          "Approved source file",
          "path",
          (p?.source_files || []).map((x) => [x, x]),
          d.path,
        )}${field("Active task (optional)", "task", d.task || "", "Leave empty for sensitivity-only inspection")}<div class="notice">A managed read uses the reviewed project manifest. Protected files, unregistered paths and symlinks are refused. Changed source invalidates delivery.</div>`;
  return `${heading("SHADOWLEAK / CONTEXT GATE", "The right context. Nothing extra.", "Rules protect credentials. Gemma checks meaning and relevance. You decide when approved text moves.")}<div class="grid split"><section class="panel"><div class="panel-head"><h2>Inspect context</h2><span class="tag">LOCAL INFERENCE</span></div><div class="tabs"><button data-mode="prompt" class="${state.privacyMode === "prompt" ? "active" : ""}">Prompt / text</button><button data-mode="source" class="${state.privacyMode === "source" ? "active" : ""}">Managed source read</button></div><form id="inspect-form">${input}<div class="actions"><button class="btn primary" type="submit" ${state.busy ? "disabled" : ""}>${state.busy ? '<span class="spinner"></span> Inspecting with Gemma' : icon("shield") + " Inspect context"}</button>${button("Try a synthetic example", "example", "text")}</div></form><div class="notice">Previewing is not delivery. Only approved, unexpired bytes can be released to the configured local composer. This does not intercept other applications.</div></section><section class="panel" id="inspection-panel"><div class="panel-head"><h2>Inspection result</h2><span class="caption">${result ? "VERSION " + esc(result.content_version) : "AWAITING INPUT"}</span></div>${result ? `<div class="result-title">${badge(result.decision)}<span class="caption">${esc(result.status)}</span></div><div class="receipts">${result.reason_codes.map((r) => `<span class="tag">${esc(r)}</span>`).join("") || '<span class="tag good">NO REDACTIONS PROPOSED</span>'}</div><span class="label">Approved preview</span>${result.safe_preview !== null ? `<pre>${esc(result.safe_preview)}</pre>` : empty("Request held", "No approved text is available. Revise the input or resolve the reported dependency.")}<p class="caption">Expires ${esc(stamp(result.expires_at))} · ${esc(result.destination_id)}</p><div class="actions">${button(icon("arrow") + " Release to composer", "deliver", "primary", !["ALLOW", "SANITIZE"].includes(result.decision) || result.status !== "READY" || result.destination_id !== "local-composer" || state.busy || result.delivered || Date.now() >= Date.parse(result.expires_at))}${button("Clear result", "clear-result", "text")}</div>${result.delivered ? '<div class="notice">Delivery confirmed. The inspected bytes are now in the local composer.</div>' : ""}` : empty("A decision you can inspect", "Your cleaned preview, reason codes and release controls appear here. No invented confidence scores.")}</section></div><section class="panel" ><div class="panel-head"><h2>Local context composer</h2><span class="tag">MEMORY ONLY · 10 MIN TTL</span></div>${state.composer?.text != null ? `<pre>${esc(state.composer.text)}</pre><div class="actions">${button(icon("clipboard") + " Copy approved text", "copy-composer")}${button("Clear composer", "clear-composer", "text")}</div><p class="caption">Actually received through the gate. Copying is explicit; no external assistant has received it.</p>` : empty("Ready for approved context", "Released text appears here. It is held in memory for ten minutes and is never written to the audit log.", "file")}</section>`;
}
function clipboard() {
  const c = state.status?.clipboard || {};
  const preview = c.display_preview ?? c.safe_preview;
  const held = c.preview_kind === "WITHHELD";
  const label = held ? "Content hidden · inspection held" : c.preview_kind === "SANITIZED" || c.state === "SENSITIVE" ? "Sanitized preview" : "Inspected text";
  return `${heading("SHADOWLEAK / NATIVE TEXT", "A little more care, every copy.", "Observe future text copies on this computer, with explicit consent. No images, key monitoring or clipboard history.")}<div class="grid split"><section class="panel"><div class="panel-head"><h2>Capture controls</h2>${badge(c.state || "OFF")}</div><div class="status-row"><span class="muted">Native adapter</span><b>${c.supported ? "Local OS text clipboard" : "Check runtime support"}</b></div><div class="status-row"><span class="muted">Capture host</span><span class="mono">${esc(c.capture_host_id)}</span></div><div class="status-row"><span class="muted">Content version</span><b>v${c.content_version || 0}</b></div><div class="divider"></div><form id="clipboard-form">${field("Task context (optional)", "task", "", "For example: diagnose an HTTP 503")}<label class="check"><input type="checkbox" name="consent" required ${c.enabled ? "disabled" : ""}><span>I am on this computer and consent to inspect future text copies. Existing clipboard contents are skipped when capture starts.</span></label><div class="actions"><button class="btn primary" ${c.enabled ? "disabled" : ""}>${icon("play")} Enable text capture</button>${button(icon("pause") + " Disable capture", "disable-capture", "", !c.enabled)}</div></form><div class="notice">Capture starts off. Turning it off cancels pending work and clears transient originals. Observation is advisory; it cannot prevent every paste.</div></section><section class="panel"><div class="panel-head"><h2>Current inspected copy</h2><span class="caption">VERSION BOUND</span></div>${preview != null ? `<span class="label">${esc(label)}</span><pre>${esc(preview)}</pre>${held ? '<div class="notice warn">The entire copy is hidden. This marker is not an approved cleaned copy. Copy new text to inspect again.</div>' : c.state === "SENSITIVE" ? '<p class="caption">Sensitive values have been replaced with placeholders.</p>' : ""}<div class="actions">${button(icon("clipboard") + " Copy cleaned text", "copy-cleaned", "primary", held || c.safe_preview == null || !c.can_copy_cleaned)}</div>` : empty(c.enabled ? "Waiting for an approved preview" : "Your clipboard stays yours", c.enabled ? "Copy new text after enabling capture. Pending, skipped or held checks are never labelled safe." : "Enable capture only when you want future copies inspected.")}<div class="divider"></div><p class="subtitle">${esc(c.redacted_summary || "No original text or raw history is exposed here.")}</p>${c.enabled ? '<p class="caption">Status updates every five seconds while this view is open.</p>' : ""}</section></div>`;
}
function repairs() {
  const r = state.status?.repair || {},
    run = state.run,
    patch = state.patch;
  return `${heading("SHIPFIX / BACKEND REPAIRS", "A patch backed by evidence.", "Named tests, approved source and isolated Docker checks. Your original files change only after explicit review.", button(icon("pause") + " Pause worker", "pause", "", !r.available) + button(icon("play") + " Resume worker", "idle", "primary", !r.available))}${!r.available ? `<div class="notice warn">Repair is unavailable: ${esc(r.reason_code)}. Start Docker, verify the pinned image and retry initialization. ${button("Retry initialization", "initialize")}</div>` : ""}<div class="grid repair-layout"><aside class="panel"><div class="panel-head"><h2>Investigations</h2>${badge(r.state || "UNAVAILABLE")}</div><form id="repair-form">${select("Project", "project_id", projectOptions())}${select(
    "Named check",
    "signal",
    (state.projects[0]?.checks || []).map((x) => [x, x]),
  )}<button class="btn primary" ${!r.available || state.busy ? "disabled" : ""}>${icon("code")} Queue investigation</button></form><div class="divider"></div>${
    state.incidents.length
      ? state.incidents
          .slice()
          .reverse()
          .map(
            (i) =>
              `<button class="incident ${state.selected === i.incident_id ? "selected" : ""}" data-incident="${esc(i.incident_id)}"><b>${esc(i.project_id)} / ${esc(i.signal)}</b><small>${esc((i.active_run_id || i.incident_id).slice(0, 18))}…</small><div class="receipts">${badge(i.status || "OPEN")}</div></button>`,
          )
          .join("")
      : empty(
          "No investigations yet",
          "Choose a registered project and named check to create a run.",
          "code",
        )
  }</aside><section class="panel"><div class="panel-head"><h2>${run ? "Investigation details" : "Your review workspace"}</h2>${run ? badge(run.state) : '<span class="caption">HUMAN IN CONTROL</span>'}</div>${
    run
      ? `<div class="grid g2"><div class="panel stat"><small>Baseline check</small><strong>${esc(run.baseline || "Pending")}</strong><p>Protected independent test</p></div><div class="panel stat"><small>Candidate verification</small><strong>${esc(run.verification || "Pending")}</strong><p>Same verifier, unchanged expectations</p></div></div><p class="caption">${esc(run.run_id)}${run.reason_code ? " · " + esc(run.reason_code) : ""}</p>${run.model?.digest ? `<p class="caption">MODEL ${esc(run.model.name)}<br><span class="mono">${esc(run.model.digest)}</span></p>` : ""}<ul class="timeline">${(run.completed_tools || []).map((t) => `<li><b>${esc(t.replaceAll("_", " "))}</b>Completed permitted tool</li>`).join("")}</ul>${run.reason_code ? `<div class="notice warn">${esc(run.reason_code)}. The reported state is authoritative; no successful patch is fabricated.</div>` : ""}${
          patch
            ? `<div class="section-row"><h2>Candidate diff</h2>${badge(patch.verification)}</div><pre class="diff">${patch.diff
                .split("\n")
                .map(
                  (line) =>
                    `<span class="diff-line ${line.startsWith("+") ? "add" : line.startsWith("-") ? "remove" : line.startsWith("@@") ? "chunk" : ""}">${esc(line) || " "}</span>`,
                )
                .join(
                  "",
                )}</pre><details><summary class="caption">Source and candidate hashes</summary><pre>${esc(JSON.stringify({ base_revision: patch.base_revision, candidate_hash: patch.candidate_hash, files: patch.base_hashes }, null, 2))}</pre></details><div class="actions">${button(icon("check") + " Review & apply", "review-apply", "primary", patch.state !== "READY_FOR_REVIEW")}${button("Reject candidate", "reject", "danger", patch.state !== "READY_FOR_REVIEW")}${button(icon("download") + " Export diff", "export-diff")}${patch.state === "APPLIED" ? button("Review rollback", "review-rollback", "danger") : ""}</div>`
            : ""
        }<div class="divider"></div><div class="actions">${button("Refresh investigation", "refresh-run")}${button("Cancel investigation", "cancel", "danger", ["APPLIED", "REJECTED", "CANCELED", "BLOCKED", "UNRESOLVED", "OBSOLETE", "ROLLED_BACK"].includes(run.state))}</div>`
      : empty(
          "Start with a reproducible failure",
          "The agent reads only approved source, proposes a snapshot patch and verifies it independently. Review the real tools and diff here.",
          "code",
        )
  }</section></div>`;
}
function projects() {
  return `${heading("SCOPE / PROJECTS", "Good agents have boundaries.", "Every source file, writable path and named check is explicitly enrolled at trusted startup.")}<div class="notice">Add a project with a reviewed local JSON manifest and <code>--projects-config</code>. The browser and model cannot enrol arbitrary roots, change trusted tests or select Docker images. <a href="#system">See setup instructions →</a></div><div class="grid g2">${state.projects.map((p) => `<section class="panel project-card"><div class="project-head"><span class="project-icon">${icon("folder")}</span><div><h2>${esc(p.project_id)}</h2><span class="caption">${p.source_files.length} SOURCE FILES · ${p.checks.length} NAMED CHECKS</span></div></div>${p.source_files.map((f) => `<div class="file-row"><span>${esc(f)}</span><span class="tag ${p.writable_files.includes(f) ? "good" : ""}">${p.writable_files.includes(f) ? "SANDBOX WRITE" : "READ ONLY"}</span></div>`).join("")}<div class="divider"></div><div class="status-row"><span class="muted">Saved-file watcher</span>${badge(p.watch?.enabled ? "WATCHING" : p.watch?.reason_code || "OFF")}</div><p class="caption">Only saved changes in this manifest are watched. Changes debounce into deduplicated incidents; worker permission is separate.</p><div class="actions"><button class="btn" data-watch="${esc(p.project_id)}" data-enabled="${!p.watch?.enabled}">${icon(p.watch?.enabled ? "pause" : "play")} ${p.watch?.enabled ? "Stop watching" : "Watch saved changes"}</button><a class="btn text" href="#repairs">Investigate ${icon("arrow")}</a></div></section>`).join("") || `<section class="panel">${empty("No enrolled projects", "Restart with an inspected demo image or a reviewed projects manifest.", "folder")}</section>`}</div><section class="panel"><div class="panel-head"><h2>Quiet-time scheduling</h2>${badge(state.status?.monitoring?.automatic ? "AUTOMATIC" : "MANUAL")}</div><p class="subtitle">Optionally admit queued work after 60 seconds without foreground model requests. This uses queue timestamps, not keyboard monitoring or OS idle detection. Foreground requests retain priority; an active inference is not preempted.</p><div class="actions">${button("Enable quiet-time mode", "auto-on", "", !!state.status?.monitoring?.automatic)}${button("Use manual scheduling", "auto-off", "text", !state.status?.monitoring?.automatic)}</div></section>`;
}
function activity() {
  const filtered = state.events.filter((e) =>
    `${e.kind} ${e.state} ${e.redacted_summary}`
      .toLowerCase()
      .includes(state.filter.toLowerCase()),
  );
  return `${heading("OBSERVABILITY / AUDIT", "The record. Without the raw data.", "Bounded, redacted metadata survives restart. Clipboard originals, prompts and model prose do not.", button(icon("download") + " Export loaded metadata", "export-audit"))}<section class="panel"><div class="panel-head"><h2>Audit timeline</h2><span class="caption">${state.events.length} LOADED / 5,000 EVENT RETENTION</span></div><label class="field"><span>Filter events</span><input id="event-filter" value="${esc(state.filter)}" placeholder="Decision, run state, event type…"></label><div id="event-table">${eventTable(filtered.slice().reverse())}</div><div class="divider"></div>${button("Load next page", "load-events", "", state.events.length >= 1000)}<p class="caption">Newest within the loaded records; use pagination to reach later pages. Maximum 1,000 records in this browser view.</p></section>`;
}
function system() {
  const s = state.status || {},
    r = s.runtime || {},
    repair = s.repair || {};
  const launcher = s.host_platform === "win32"
    ? ".\\.venv\\Scripts\\python.exe -m devguard"
    : "./scripts/devguard-local";
  const manifest = s.host_platform === "win32" ? "C:/Projects/projects.json" : "/absolute/path/projects.json";
  return `${heading("SYSTEM / COVERAGE", "Know what is actually running.", "Runtime readiness, trusted boundaries and explicit integration limits.")}<div class="grid system-grid"><section class="panel"><div class="panel-head"><h2>Runtime health</h2><span class="tag">THIS LAPTOP</span></div>${[
    ["shield", "Local model", r.model, r.model_ready ? "READY" : r.reason_code],
    [
      "code",
      "Docker verification",
      "Pinned image · no network · unprivileged",
      repair.available ? "READY" : repair.reason_code,
    ],
    [
      "lock",
      "Credential scanner",
      "Deterministic scan before and after Gemma",
      s.credential_scanner_available ? "READY" : "UNAVAILABLE",
    ],
    [
      "activity",
      "Audit store",
      "Metadata only · bounded SQLite",
      s.audit?.durable ? "READY" : "SESSION_ONLY",
    ],
    [
      "clipboard",
      "Native clipboard",
      "Off until explicit consent",
      s.clipboard?.state || "OFF",
    ],
  ]
    .map(
      ([i, t, d, status]) =>
        `<div class="health-check"><span class="health-icon">${icon(i)}</span><div>${esc(t)}<small>${esc(d)}</small></div>${badge(status)}</div>`,
    )
    .join(
      "",
    )}<div class="divider"></div><span class="label">Pinned model digest</span><pre>${esc(r.model_digest || "Not available")}</pre><span class="label">Inference queue</span><pre>${esc(JSON.stringify(s.inference_queue || {}, null, 2))}</pre></section><section class="panel"><div class="panel-head"><h2>Single-laptop setup</h2></div><p class="subtitle">Run from the repository root. The launcher checks Docker and the exact Gemma package, inspects the verifier image and starts this local workspace.</p><pre>${esc(launcher)} start
${esc(launcher)} status
${esc(launcher)} stop</pre><p class="subtitle">Enrol your own Python backend with independent pytest checks and a prepared image:</p><pre>${esc(launcher)} start --projects-config "${esc(manifest)}"</pre><div class="notice">The model can propose edits to one approved source file per candidate. It cannot change your policy, trusted tests or original files. Rollback requires explicit review and unchanged applied source.</div>${button("Disconnect this browser", "disconnect", "danger")}</section></div><div class="section-row"><h2>Integration boundaries</h2><span class="caption">IMPLEMENTATION ≠ UNIVERSAL COVERAGE</span></div><div class="grid g2">${state.coverage.map((c) => `<section class="panel"><div class="panel-head"><h2>${esc(c.capability.replaceAll("_", " "))}</h2>${badge(c.status)}</div><p class="subtitle">${esc(c.limitations)}</p></section>`).join("")}</div><div class="notice warn">Recorded Codex and Claude CLI hook/MCP boundaries passed with real Gemma and a local synthetic provider. Isolated profiles require explicit setup and native hook trust; they are not active in every application. The managed server source-read path enforces its own output gate. Arbitrary app pastes, automatic context ingestion and attachments remain outside its boundary. Native text capture requires a supported macOS or Windows desktop session. Windows signed-in coding-client trials remain unverified.</div>`;
}

function evidence() {
  const e = measuredEvidence;
  if (!e)
    return heading(
      "VERIFICATION / RECORDED TRIALS",
      "Evidence unavailable.",
      "Use the repository evidence files; no results are fabricated.",
    );
  const rows = e.privacy.results;
  const calibrated = [...(e.privacy_calibrated?.results || []), ...(e.privacy_variants?.results || [])];
  const native = e.native_clients?.results || [];
  const calibrationTable = (items) => `<div class="table-wrap"><table><thead><tr><th>CASE</th><th>EXPECTED</th><th>OBSERVED</th><th>REQUIRED REASONS</th></tr></thead><tbody>${items.map((r) => `<tr><td>${esc(r.case_id)}</td><td>${badge(r.expected_decision)}</td><td>${badge(r.actual_decision)}</td><td>${r.expected_reasons_present ? "Present" : "Missing"}</td></tr>`).join("")}</tbody></table></div>`;
  return `${heading("VERIFICATION / RECORDED TRIALS", "Measured. Not assumed.", "Recorded single-laptop trials from 21 October. These are individual experiments, not continuous monitoring or an unseen accuracy benchmark.", button(icon("download") + " Export redacted evidence", "export-evidence"))}
  <div class="grid g3"><div class="panel stat"><small>Real Gemma + Docker repair</small><strong>${esc(e.repair.elapsed_seconds)} s</strong><p>Failing baseline → verified patch → disposable apply</p></div><div class="panel stat"><small>Native text lifecycle</small><strong>${esc(e.clipboard.checks_passed)} / ${esc(e.clipboard.checks_total)}</strong><p>Private named pasteboard; general clipboard untouched</p></div><div class="panel stat"><small>Actual cleaned-text delivery</small><strong>${esc(e.delivery.elapsed_seconds)} s</strong><p>Receiver bytes matched; synthetic secret absent; replay held</p></div></div>
  ${calibrated.length ? `<div class="section-row"><h2>Privacy after calibration</h2><span class="caption">${calibrated.filter((r) => r.decision_matches_expectation && r.expected_reasons_present).length} / ${calibrated.length} SMALL REGRESSION CASES</span></div><section class="panel">${calibrationTable(calibrated)}<div class="notice">Real pinned Gemma and Gitleaks; original P01–P05 expectations unchanged, plus eight synthetic variants. A sentence-final email miss found during the variant run was fixed and retested. These are calibration cases, not an independent accuracy estimate. The earlier baseline with three mismatches is preserved below.</div></section>` : ""}
  ${native.length ? `<div class="section-row"><h2>Native coding-client boundaries</h2><span class="caption">${native.filter((r) => r.passed).length} / ${native.length} RECORDED CHECKS</span></div><section class="panel"><p class="subtitle">Actual installed Codex CLI 0.163.0-alpha.10.2 and Claude Code 2.1.119. The privacy guard uses real Gemma. The coding-provider transport is a local synthetic fixture; cloud-model delivery was not tested.</p><div class="table-wrap"><table><thead><tr><th>CLIENT</th><th>PATH</th><th>RESULT</th><th>RECEIVER CALLS</th><th>SENSITIVE MARKER</th></tr></thead><tbody>${native.map((r) => `<tr><td>${esc(r.client)}</td><td>${esc(({blocked:"Sensitive prompt held",text:"Benign prompt passed",managed:"Approved source read",sensitive:"Source credential removed",traversal:"Traversal held",shell:"Native shell denied",guard_unavailable:"Unavailable guard held"})[r.case] || r.case)}</td><td>${badge(r.passed ? "PASS" : "FAILED")}</td><td>${esc(r.provider_requests)}</td><td>${r.sensitive_marker_received ? "Received" : "Absent"}</td></tr>`).join("")}</tbody></table></div><div class="notice">Prompt holds, benign positive controls, managed clean reads, source redaction, traversal holds, native Codex shell denial and unavailable-guard holds were measured. This does not cover every app, attachment, automatic context source or transcript.</div></section>` : ""}
  <details class="panel"><summary>Earlier baseline: three mismatches preserved</summary>  <div class="section-row"><h2>Earlier privacy baseline</h2><span class="caption">HISTORICAL RESULTS / PRESERVED</span></div>
  <section class="panel"><div class="table-wrap"><table><thead><tr><th>CASE</th><th>EXPECTED</th><th>OBSERVED</th><th>REQUIRED REASONS PRESENT</th></tr></thead><tbody>${rows.map((r) => `<tr><td>${esc(r.case_id)}</td><td>${badge(r.expected_decision)}</td><td>${badge(r.actual_decision)}</td><td>${r.expected_reasons_present ? "Yes" : "No"}</td></tr>`).join("")}</tbody></table></div><div class="notice warn">This earlier baseline contains the P02 false positive, P03 decision mismatch and P05 missing injection reason. The corrected rerun is shown below; the earlier failures remain visible.</div></section>
</details>
  <div class="section-row"><h2>Checks beyond a green test</h2><span class="caption">REAL API + DOCKER</span></div><section class="panel">${[
    ["Original source unchanged", e.repair.original_source_unchanged],
    ["Protected tests unchanged", e.repair.trusted_tests_unchanged],
    ["Post-apply Docker check passed", e.rollback.post_apply_docker === "PASS"],
    [
      "Concurrent edit preserved on rollback",
      e.rollback.concurrent_edit_preserved,
    ],
    ["Exact original restored", e.rollback.exact_original_restored],
    ["Rollback repeat idempotent", e.rollback.rollback_repeat_idempotent],
  ]
    .map(
      ([label, passed]) =>
        `<div class="status-row"><span>${label}</span>${badge(passed ? "PASS" : "NOT VERIFIED")}</div>`,
    )
    .join(
      "",
    )}</section><div class="notice">Recorded native CLI boundaries are scoped to the tested versions and isolated configurations. Signed-in cloud delivery, desktop variants and broad unseen accuracy remain unverified. The model cannot edit policy, trusted tests or its own verification results. Evidence never substitutes for current runtime readiness.</div>`;
}

async function refresh({ draw = true } = {}) {
  try {
    const [status, projects, incidents, coverage] = await Promise.all([
      api("/status"),
      api("/projects"),
      api("/incidents"),
      api("/coverage"),
    ]);
    state.status = status;
    state.projects = projects.projects;
    state.incidents = incidents.incidents;
    state.coverage = coverage.capabilities;
    state.connected = true;
    if (draw) render();
  } catch (e) {
    problem(e);
  }
}
async function loadEvents() {
  const page = await api("/events?after=" + encodeURIComponent(state.cursor));
  const known = new Set(state.events.map((e) => e.event_id));
  state.events.push(...page.events.filter((e) => !known.has(e.event_id)));
  state.events = state.events.slice(-1000);
  state.cursor = page.next_cursor;
}
async function loadComposer() {
  const result = await api("/composer");
  state.composer = result;
  state.composerExpiry = Date.now() + (result.expires_in_seconds ?? 600) * 1000;
  return result;
}
async function refreshRun(force = false) {
  const incident = state.incidents.find(
    (i) => i.incident_id === state.selected,
  );
  if (!incident?.active_run_id) {
    state.run = null;
    state.patch = null;
    return;
  }
  state.run = await api("/runs/" + encodeURIComponent(incident.active_run_id));
  if (!state.run.candidate_id) {
    state.patch = null;
  } else if (force || state.patch?.candidate_id !== state.run.candidate_id || state.patchRunState !== state.run.state) {
    // Keep the approved display while unchanged. Apply still revalidates on
    // the server; ordinary polling must not repeatedly invoke Gemma on a diff.
    state.patch = await api('/patches/' + encodeURIComponent(state.run.candidate_id));
    state.patchRunState = state.run.state;
  }
}
async function navigate(target = null) {
  view =
    typeof target === "string" ? target : location.hash.slice(1) || "overview";
  if (!nav.some((n) => n[0] === view)) view = "overview";
  if (view !== "privacy") {
    state.result = null;
    state.privacyDraft = {};
  }
  render();
  if (state.connected)
    try {
      if (view === "activity" || view === "overview") await loadEvents();
      if (view === "privacy") await loadComposer();
      if (view === "repairs") await refreshRun();
      render();
    } catch (e) {
      problem(e);
    }
}
function download(name, text, type = "text/plain") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function review(kind) {
  if (!state.patch) return;
  const rollback = kind === "rollback";
  const dialog = $("#review-dialog");
  dialog.innerHTML = `<h2 id="dialog-title">${rollback ? "Roll back applied changes?" : "Apply this verified patch?"}</h2><p>${rollback ? "Restore the original source retained in this session. The backend refuses if the applied source or any tracked file has changed." : "This changes the enrolled original source file. The backend rechecks the candidate and all original source hashes, then performs one atomic file replacement."}</p><pre>${esc(state.patch.diff)}</pre><p class="caption">${esc(state.patch.candidate_id)}</p><label class="check"><input id="approve-change" type="checkbox"><span>I reviewed the diff and authorize ${rollback ? "restoring the original source" : "applying this change to the enrolled project"}.</span></label><div class="actions">${button(rollback ? "Restore original source" : "Apply to original source", rollback ? "rollback" : "apply", "primary", true)}${button("Keep reviewing", "close-dialog")}</div>`;
  dialog.showModal();
}
async function action(name, element) {
  switch (name) {
    case "connect":
      state.busy = true;
      render();
      try {
        await api("/session/connect", { method: "POST", body: {} });
        await refresh();
        await loadEvents();
        render();
        toast("Connected locally. Capture and monitoring remain opt-in.");
      } finally {
        state.busy = false;
        render();
      }
      break;
    case "disconnect":
      await api("/session/disconnect", { method: "POST", body: {} });
      Object.assign(state, {
        connected: false,
        result: null,
        composer: null,
        privacyDraft: {},
        events: [],
      });
      render();
      break;
    case "theme":
      document.documentElement.dataset.theme =
        document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      try {
        localStorage.setItem(
          "devguard-theme",
          document.documentElement.dataset.theme,
        );
      } catch {}
      break;
    case "menu":
      $(".sidebar").classList.toggle("open");
      break;
    case "refresh":
      await refresh();
      break;
    case "example":
      state.privacyMode = "prompt";
      state.privacyDraft = {
        task: "Debug the webhook HTTP 403",
        text: "api_key=synthetic-demo-credential-734875933; webhook returned HTTP 403.",
      };
      state.result = null;
      render();
      break;
    case "clear-result":
      state.result = null;
      state.privacyDraft = {};
      render();
      break;
    case "deliver": {
      const r = state.result;
      if (!r) return;
      const path = state.source ? "/context/requests/" : "/guard/requests/";
      const receipt = await api(
        path + encodeURIComponent(r.request_id) + "/deliver",
        {
          method: "POST",
          body: {
            content_version: r.content_version,
            destination_id: r.destination_id,
          },
        },
      );
      if (receipt.delivered !== true)
        throw new ApiError("DELIVERY_NOT_CONFIRMED");
      r.delivered = true;
      await loadComposer();
      render();
      toast("Actual delivery confirmed to the local composer.");
      break;
    }
    case "copy-composer":
      await loadComposer();
      if (state.composer?.text != null) {
        await navigator.clipboard.writeText(state.composer.text);
        toast("Approved text copied by your explicit action.");
      }
      break;
    case "clear-composer":
      await api("/composer", { method: "DELETE" });
      state.composer = null;
      render();
      break;
    case "disable-capture": {
      const result = await api("/clipboard/disable", {
        method: "POST",
        body: {},
      });
      if (result.enabled !== false)
        throw new ApiError("CAPTURE_DISABLE_UNCONFIRMED");
      await refresh();
      toast("Capture disabled. Transient originals cleared.");
      break;
    }
    case "copy-cleaned": {
      const version = state.status.clipboard.content_version;
      const r = await api("/clipboard/copy-cleaned", {
        method: "POST",
        body: { content_version: version },
      });
      if (!r.copied) throw new ApiError("COPY_NOT_CONFIRMED");
      await refresh();
      toast("The inspected version was copied.");
      break;
    }
    case "initialize":
      await api("/repair/initialize", { method: "POST", body: {} });
      await refresh();
      break;
    case "pause":
      await api("/scheduler/pause", { method: "POST", body: {} });
      await refresh();
      toast("Worker paused. Active work receives cancellation.");
      break;
    case "idle":
      await api("/scheduler/enter-idle", { method: "POST", body: {} });
      await refresh();
      toast("Queued work may now execute.");
      break;
    case "auto-on":
    case "auto-off":
      await api("/scheduler/automatic", {
        method: "POST",
        body: { enabled: name === "auto-on", quiet_seconds: 60 },
      });
      await refresh();
      break;
    case "cancel":
      await api("/runs/" + state.run.run_id + "/cancel", {
        method: "POST",
        body: {},
      });
      await refreshRun();
      render();
      toast("Cancellation requested. Inspect the state for acknowledgement.");
      break;
    case "refresh-run":
      await refresh({ draw: false });
      await refreshRun(true);
      render();
      break;
    case "review-apply":
      review("apply");
      break;
    case "review-rollback":
      review("rollback");
      break;
    case "close-dialog":
      $("#review-dialog").close();
      break;
    case "apply":
    case "rollback": {
      if (!$("#approve-change")?.checked) return;
      const p = state.patch;
      const key = p.candidate_id + ":" + name;
      state.keys[key] ??= crypto.randomUUID();
      element.disabled = true;
      try {
        await api("/patches/" + p.candidate_id + "/" + name, {
          method: "POST",
          body: {
            approved: true,
            expected_candidate_hash: p.candidate_hash,
            expected_base_revision: p.base_revision,
            idempotency_key: state.keys[key],
          },
        });
      } finally {
        element.disabled = !document.querySelector("#approve-change")?.checked;
      }
      $("#review-dialog").close();
      await refresh({ draw: false });
      await refreshRun();
      render();
      toast(
        name === "apply"
          ? "Patch application confirmed."
          : "Original source restored.",
      );
      break;
    }
    case "reject":
      await api("/patches/" + state.patch.candidate_id + "/reject", {
        method: "POST",
        body: {},
      });
      await refresh({ draw: false });
      await refreshRun();
      render();
      toast("Candidate rejected.");
      break;
    case "export-evidence":
      download(
        "devguard-measured-evidence.json",
        JSON.stringify(measuredEvidence, null, 2),
        "application/json",
      );
      break;
    case "export-diff":
      download("devguard-candidate.diff", state.patch.diff);
      break;
    case "export-audit":
      download(
        "devguard-redacted-audit.json",
        JSON.stringify(
          { scope: "Loaded redacted metadata only", events: state.events },
          null,
          2,
        ),
        "application/json",
      );
      break;
    case "load-events":
      await loadEvents();
      render();
      break;
  }
}
document.addEventListener("click", async (event) => {
  const localLink = event.target.closest('a[href^="#"]');
  if (publicDemo && localLink) {
    event.preventDefault();
    await navigate(localLink.getAttribute("href").slice(1));
    return;
  }
  const target = event.target.closest(
    "[data-action],[data-mode],[data-incident],[data-watch]",
  );
  if (!target) return;
  try {
    if (target.dataset.mode) {
      state.privacyMode = target.dataset.mode;
      state.result = null;
      render();
      return;
    }
    if (target.dataset.incident) {
      state.selected = target.dataset.incident;
      await refreshRun();
      render();
      return;
    }
    if (target.dataset.watch) {
      const enabled = target.dataset.enabled === "true";
      await api(
        "/projects/" + encodeURIComponent(target.dataset.watch) + "/watch",
        { method: "POST", body: { enabled } },
      );
      await refresh();
      toast(
        enabled
          ? "Saved-file monitoring enabled for this manifest."
          : "Saved-file monitoring disabled.",
      );
      return;
    }
    await action(target.dataset.action, target);
  } catch (e) {
    problem(e);
  }
});
function draftChanged(event) {
  if (!event.target.closest("#inspect-form")) return;
  state.privacyDraft = Object.fromEntries(
    new FormData(event.target.closest("form")),
  );
  if (state.result) {
    state.result = null;
    const panel = document.querySelector("#inspection-panel");
    if (panel)
      panel.innerHTML = empty(
        "Draft changed",
        "Inspect the updated context before release.",
      );
  }
}
document.addEventListener("change", (event) => {
  draftChanged(event);
  if (event.target.id === "approve-change") {
    const b = $(
      '#review-dialog [data-action="apply"],#review-dialog [data-action="rollback"]',
    );
    if (b) b.disabled = !event.target.checked;
  }
  if (event.target.name === "project_id") {
    const p = state.projects.find((x) => x.project_id === event.target.value);
    const form = event.target.closest("form");
    const dependent = form?.querySelector(
      'select[name="path"],select[name="signal"]',
    );
    if (dependent && p) {
      const values = dependent.name === "path" ? p.source_files : p.checks;
      dependent.innerHTML = values
        .map((v) => `<option>${esc(v)}</option>`)
        .join("");
    }
  }
});
document.addEventListener("input", (event) => {
  draftChanged(event);
  if (event.target.id === "event-filter") {
    state.filter = event.target.value;
    $("#event-table").innerHTML = eventTable(
      state.events
        .filter((e) =>
          `${e.kind} ${e.state} ${e.redacted_summary}`
            .toLowerCase()
            .includes(state.filter.toLowerCase()),
        )
        .reverse(),
    );
  }
});
document.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const data = Object.fromEntries(new FormData(form));
  try {
    if (form.id === "inspect-form") {
      if (state.busy) return;
      state.busy = true;
      state.result = null;
      state.privacyDraft = { ...data };
      render();
      try {
        const version = Date.now();
        if (state.privacyMode === "source") {
          state.source = true;
          state.result = await api("/context/read", {
            method: "POST",
            body: {
              project_id: data.project_id,
              path: data.path,
              task: data.task || null,
              content_version: version,
            },
          });
        } else {
          state.source = false;
          state.result = await api("/guard/evaluate", {
            method: "POST",
            body: {
              project_id: null,
              task: data.task || null,
              surface: data.surface,
              destination_id: data.destination,
              content_version: version,
              text: data.text,
            },
          });
        }
        await loadEvents();
      } finally {
        state.busy = false;
        if (view !== "privacy") {
          state.result = null;
          state.privacyDraft = {};
        }
        render();
      }
    } else if (form.id === "clipboard-form") {
      if (!data.consent) return;
      const r = await api("/clipboard/enable", {
        method: "POST",
        body: { consent: true, task: data.task || null },
      });
      if (r.enabled !== true) throw new ApiError("CAPTURE_ENABLE_UNCONFIRMED");
      await refresh();
      toast("Future text copies are now inspected on this computer.");
    } else if (form.id === "repair-form") {
      const incident = await api("/incidents", {
        method: "POST",
        body: { project_id: data.project_id, signal: data.signal },
      });
      await api("/incidents/" + incident.incident_id + "/investigate", {
        method: "POST",
        body: {},
      });
      state.selected = incident.incident_id;
      await refresh({ draw: false });
      await refreshRun();
      render();
      toast("Investigation queued. Resume the worker when ready.");
    }
  } catch (e) {
    problem(e);
  }
});
window.addEventListener("hashchange", navigate);
let polling = false;
setInterval(async () => {
  if (
    !state.connected ||
    document.hidden ||
    state.busy ||
    polling ||
    $("#review-dialog").open
  )
    return;
  if (
    state.result &&
    state.result.status !== "EXPIRED" &&
    Date.now() >= Date.parse(state.result.expires_at)
  ) {
    state.result.safe_preview = null;
    state.result.status = "EXPIRED";
    state.privacyDraft = {};
    render();
  }
  if (
    state.composer &&
    state.composerExpiry &&
    Date.now() >= state.composerExpiry
  ) {
    state.composer = null;
    if (view === "privacy") render();
  }
  polling = true;
  try {
    await refresh({ draw: false });
    if (view === "repairs" && state.selected) await refreshRun();
    if (["overview", "activity"].includes(view)) await loadEvents();
    if (
      ["overview", "repairs", "activity", "system", "clipboard"].includes(
        view,
      ) &&
      !document.activeElement?.matches("input,textarea,select")
    )
      render();
  } catch (e) {
    problem(e);
  } finally {
    polling = false;
  }
}, 5000);
const measuredEvidence =
  window.DEVGUARD_RECORDED_EVIDENCE ??
  (await fetch("/assets/evidence.json", { cache: "no-store" })
    .then((r) => (r.ok ? r.json() : null))
    .catch(() => null));
render();
try {
  await api("/status");
  await refresh();
  await navigate();
} catch {}
