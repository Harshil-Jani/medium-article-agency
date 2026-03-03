import os
from dotenv import load_dotenv

load_dotenv()

# Model configuration
DEFAULT_MODEL = "claude-opus-4-6"
FAST_MODEL = "claude-haiku-4-5-20251001"
BALANCED_MODEL = "claude-sonnet-4-5-20250929"

# API configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Output configuration
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

# Agency configuration
AGENCY_NICHE = "Rust, Open Source, Systems Programming, Fintech, Developer Tooling"
CADENCE = "2 articles/week"
VOICE = "Harshil Jani — clear, opinionated, practical, rooted in real engineering experience"
