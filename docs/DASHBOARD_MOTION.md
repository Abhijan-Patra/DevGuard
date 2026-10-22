# Dashboard presentation and motion

23 October 2026. The FastAPI browser workspace and read-only public tour share
the same frontend assets. This update adds presentation features, without new
API routes, permissions, runtime dependencies or external image/font requests.

- A procedural particle shield appears on the connection screen, Overview and
  Context Gate. Pointer movement displaces the dots; clicking the illustration
  creates a ripple. This is explicitly labelled an interactive illustration,
  not an inspection, model-readiness or protection indicator.
- Context Gate shows input, local inspection and review stages. Only an actual
  pending request animates the inspection stage. Approved, held and expired
  results use the existing backend response; no percentages or success results
  are invented.
- Backend Repairs has an evidence strip displaying actual baseline, completed
  tools, verification and review state. Active highlighting uses actual run
  states, not timers.
- Page entry and result transitions play on navigation/new results, not on
  every five-second refresh. Particle canvases survive same-view redraws;
  leaving the view disconnects observers, listeners and animation frames.
- A session-only Pause motion control disables motion throughout the workspace.
  The operating system's reduced-motion preference takes priority. Particle
  frames settle when idle and stop when offscreen or the tab is hidden. The
  shield falls back to a static SVG if 2D canvas is unavailable.

The particle controller receives only decorative canvas geometry and pointer
coordinates inside that illustration. It has no API, clipboard, prompt or
source input. Capture/watchers remain opt-in and reviewed apply/rollback use
the existing authority checks.

The implementation is original plain JavaScript/CSS, inspired by the supplied
interactive-particle examples. It does not embed their React components,
external assets or WebGL engine. React, Tailwind and shadcn are not required.

## Validation

```sh
node --check devguard/web/workspace.js
node --check devguard/web/workspace-motion.js
node --test tests/ui/workspace-motion.test.cjs
python -m pytest -q
python -m pip check
```

The Node tests exercise canvas reuse, bounded geometry, settling, pointer
response, pause/reduced motion, visibility and observer/listener cleanup.
Python integration and public-tour tests verify the additional asset is served
and inlined before the workspace controller. The installed-wheel smoke also
requires the asset. Browser review should include both themes, live synthetic
inspection, all eight views and the public tour with device controls disabled.
