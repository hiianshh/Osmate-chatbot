# utils.py
import html

def sanitize_text(s: str) -> str:
    """Escape text for safe display."""
    return html.escape(s)
