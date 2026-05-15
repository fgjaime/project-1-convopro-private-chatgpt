#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from pymongo import MongoClient

from config.settings import Settings


def check_env(settings: Settings) -> tuple[bool, str]:
    required = [
        ("MONGO_DB_URL", settings.MONGO_DB_URL),
        ("MONGO_DB_NAME", settings.MONGO_DB_NAME),
        ("OLLAMA_URL", settings.OLLAMA_URL),
        ("OLLAMA_MODELS", settings.OLLAMA_MODELS),
    ]
    missing = [name for name, value in required if not str(value).strip()]
    if missing:
        return False, f"missing values: {', '.join(missing)}"
    return True, "all required settings loaded"


def check_mongo(settings: Settings) -> tuple[bool, str]:
    client = MongoClient(settings.MONGO_DB_URL, tz_aware=True, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
        db = client[settings.MONGO_DB_NAME]
        _ = db.list_collection_names()
        return True, f"connected to db '{settings.MONGO_DB_NAME}'"
    except Exception as exc:
        return False, str(exc)
    finally:
        client.close()


def check_ollama(settings: Settings) -> tuple[bool, str]:
    tags_url = urljoin(settings.OLLAMA_URL.rstrip("/") + "/", "api/tags")
    req = Request(tags_url, method="GET")
    try:
        with urlopen(req, timeout=5) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
            model_count = len(data.get("models", [])) if isinstance(data, dict) else 0
            return True, f"reachable ({model_count} model(s) reported by /api/tags)"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    checks = []
    try:
        settings = Settings()
    except Exception as exc:
        print(f"[FAIL] settings: {exc}")
        return 1

    checks.append(("env", check_env(settings)))
    checks.append(("mongo", check_mongo(settings)))
    checks.append(("ollama", check_ollama(settings)))

    failed = False
    for name, (ok, msg) in checks:
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {name}: {msg}")
        if not ok:
            failed = True

    if failed:
        print("\nPreflight failed. Fix issues above before running Streamlit.")
        return 1

    print("\nPreflight passed. You can run: streamlit run main.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
