import os
from dotenv import load_dotenv

# Load environment variables from a local .env file for development.
load_dotenv()


def require(name: str) -> str:
    # Helper to enforce required settings at startup.
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Error: Could not load environment vars {name}")
    else:
        return val


# Environment and server settings.
APP_ENV = os.environ.get("APP_ENV", "dev")
PORT = int(os.environ.get("PORT", "8000"))

# External service and database configuration.
OPENAI_API_KEY = require("OPENAI_API_KEY")
DATABASE_URL = require("DATABASE_URL")
