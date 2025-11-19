cat > README.md <<'MD'
# OSMate — Operating System Chat

Streamlit app: OS tutor & safe shell assistant using Gemini.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.sample .env   # add GEMINI_API_KEY to .env (do NOT commit .env)
streamlit run osmate_app.py
