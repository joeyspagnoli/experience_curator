import os
from dotenv import load_dotenv

load_dotenv()


def require(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Error: Could not load environment vars {name}")
    else:
        return val


APP_ENV = os.environ.get("APP_ENV", "dev")
PORT = int(os.environ.get("PORT", "8000"))

OPENAI_API_KEY = require("OPENAI_API_KEY")
DATABASE_URL = require("DATABASE_URL")
