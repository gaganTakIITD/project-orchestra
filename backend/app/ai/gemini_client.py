"""Gemini client factory — credit-schema compliant.

Orchestra AI runs on **raystartup** via **Vertex AI** (first-party Gemini) and
Application Default Credentials (Cloud Run SA). This is covered by the GCP free
trial.

Forbidden for Orchestra:
- Gemini Developer API / AI Studio API keys (not trial-eligible on raystartup)
- Pointing SDK calls at gen-lang-client for the ₹95.7k credit (that credit is
  Agent Builder Search/Conversation only)

See docs/GCP_BILLING_SPLIT.md.
"""

from __future__ import annotations

from typing import Any

from app.config import settings

_NOT_CONFIGURED = (
    "Vertex Gemini is not configured. Set GEMINI_AUTH=vertex and "
    "VERTEX_PROJECT=raystartup (see docs/GCP_BILLING_SPLIT.md). "
    "Do not use GEMINI_API_KEY / Gemini Developer API (AI Studio)."
)


def make_gemini_client() -> Any:
    """Return a google-genai Client bound to Vertex on VERTEX_PROJECT."""
    auth = (settings.gemini_auth or "off").strip().lower()
    if auth != "vertex":
        raise RuntimeError(_NOT_CONFIGURED)
    if not (settings.vertex_project or "").strip():
        raise RuntimeError(_NOT_CONFIGURED)

    from google import genai
    from google.genai import types

    # Timeout in ms — confirm used to hang for minutes without this.
    timeout_ms = max(1_000, int(float(settings.gemini_timeout_seconds) * 1000))

    return genai.Client(
        vertexai=True,
        project=settings.vertex_project.strip(),
        location=(settings.vertex_location or "us-central1").strip(),
        http_options=types.HttpOptions(timeout=timeout_ms),
    )
