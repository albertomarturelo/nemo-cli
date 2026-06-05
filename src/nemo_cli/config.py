import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "https://portalclientes.vectorcapital.cl/api"


@dataclass(frozen=True)
class Credentials:
    user_name: str
    password: str


def load_credentials() -> Credentials:
    user_name = (os.environ.get("NEMO_USERNAME") or "").strip()
    password = os.environ.get("NEMO_PASSWORD") or ""
    if not user_name or not password:
        raise RuntimeError(
            "Missing credentials. Set NEMO_USERNAME and NEMO_PASSWORD (e.g. in .env)."
        )
    return Credentials(user_name=user_name, password=password)
