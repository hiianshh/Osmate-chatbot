# osmate_chat.py
import os
from typing import Optional

# Try to import the SDK. If your SDK name/version is different adjust accordingly.
try:
    from google import genai
except Exception as e:
    raise RuntimeError("Missing google-genai package. Run: pip install google-genai") from e

# Read API key from environment
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GENAI_API_KEY")

if not API_KEY:
    # Fail early with clear error (this will be raised if import happens before env is loaded)
    raise RuntimeError(
        "Missing Gemini API key. Add GEMINI_API_KEY to your .env or export it in the shell, "
        "or set GOOGLE_API_KEY/GENAI_API_KEY environment variable."
    )

# Try to configure the SDK explicitly (some versions provide configure())
try:
    genai.configure(api_key=API_KEY)
except Exception:
    # If configure doesn't exist, the Client() may pick up the environment variable.
    pass

# Create client
try:
    client = genai.Client()
except Exception as e:
    # Re-raise with clearer context
    raise RuntimeError("Failed to create genai.Client(). Check your google-genai package and API key.") from e


def generate_text(prompt: str, model: str = "gemini-2.5-flash", max_output_tokens: int = 512) -> str:
    """
    Send a prompt to Gemini and return the best text result.
    Keeps the wrapper defensive against SDK surface changes.
    """
    try:
        # Many quickstarts use client.models.generate_content(...)
        resp = client.models.generate_content(model=model, contents=prompt)
        # Common property for quickstart responses
        text = getattr(resp, "text", None)
        if text:
            return text

        # Fallback: dig into candidates structure used by some SDK versions
        try:
            return resp.candidates[0].content.parts[0].text
        except Exception:
            return str(resp)

    except Exception as e:
        # Return a readable error (so Streamlit shows it instead of crashing)
        return f"(Gemini call error) {e}"


if __name__ == "__main__":
    # Quick sanity check (only run when invoked directly)
    print(generate_text("Hello from OSMate — introduce yourself in one short sentence."))
