# Public dashboard

The Render service uses `DEVGUARD_PUBLIC_DEMO=1`. It exposes synthetic fixture workflows only and disables live connections and operator enrolment. It does not expose the Mac API, tokens, clipboard, model or Docker. Each visitor has separate Streamlit session state. Do not submit private input.

Real local Gemma and Docker measurements are linked from the page. Public presentation data is not evidence of live inference.

Build: `pip install '.[ui]'`

Start: `streamlit run devguard/ui/app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true --browser.gatherUsageStats false`

Use Python 3.11+. Native clipboard capture remains available in the unchanged local deployment when the public-demo environment flag is absent.
