"""Configuration management for the autonomous AI co-worker."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(override=True)

# Path configurations
PACKAGE_DIR = Path(__file__).resolve().parent
ROOT_DIR = PACKAGE_DIR.parent
SANDBOX_DIR = ROOT_DIR / "sandbox"

# Model configurations
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
MAX_EVALUATION_ATTEMPTS = int(os.getenv("MAX_EVALUATION_ATTEMPTS", "3"))
MODEL_RUN_LIMIT = int(os.getenv("MODEL_CALL_LIMIT", "30"))

# Service API keys
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER = os.getenv("PUSHOVER_USER")

# MCP Configurations
MCP_BROWSER_HEADED = os.getenv("MCP_BROWSER_HEADED", "true").lower() == "true"
MCP_BROWSER_ISOLATED = os.getenv("MCP_BROWSER_ISOLATED", "true").lower() == "true"
