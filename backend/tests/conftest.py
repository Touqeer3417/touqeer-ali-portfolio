import os

# Keep imports deterministic in unit tests; no real service calls use these values.
os.environ.setdefault("OPENAI_API_KEY", "unit-test-openai-key")
os.environ.setdefault("QDRANT_URL", "https://localhost:6333")
os.environ.setdefault("QDRANT_API_KEY", "unit-test-qdrant-key")
os.environ.setdefault("SHARED_SECRET", "unit-test-shared-secret-at-least-24-chars")
