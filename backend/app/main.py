"""FastAPI entry point for the SustainIQ backend.

Only a health check for now. The /analyse route, CORS and settings
are added in later steps, one feature at a time.
"""

from fastapi import FastAPI

# Title and version appear in the auto-generated docs at /docs.
app = FastAPI(title="SustainIQ API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the server is running.

    Hosting platforms like Render call a route like this to check
    that the app is alive, so it must stay fast and dependency-free.
    """
    return {"status": "ok"}
