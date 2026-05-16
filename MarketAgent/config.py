import json
import os
from pathlib import Path
from typing import Optional

CONFIG_FILE = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "website": "",
    "autonomy_level": 1,
    "anthropic_api_key": "",
    "analytics": {
        "google_analytics": {"enabled": False, "property_id": "", "credentials_file": ""},
        "search_console": {"enabled": False, "site_url": "", "credentials_file": ""},
    },
    "ads": {
        "google_ads": {"enabled": False, "customer_id": "", "developer_token": "", "credentials_file": ""},
        "meta": {"enabled": False, "access_token": "", "ad_account_id": ""},
        "twitter": {"enabled": False, "api_key": "", "api_secret": "", "access_token": "", "access_secret": ""},
        "tiktok": {"enabled": False, "access_token": "", "advertiser_id": ""},
        "linkedin": {"enabled": False, "access_token": "", "account_id": ""},
    },
    "social": {
        "twitter": {"enabled": False, "api_key": "", "api_secret": "", "access_token": "", "access_secret": ""},
        "instagram": {"enabled": False, "access_token": "", "account_id": ""},
        "linkedin": {"enabled": False, "access_token": "", "person_id": ""},
        "facebook": {"enabled": False, "access_token": "", "page_id": ""},
    },
    "scan_interval_hours": 24,
    "ui": "cli",
}

AUTONOMY_LABELS = {
    0: "Manual — recommendations only, nothing executed",
    1: "Semi-auto — proposes actions, waits for your approval",
    2: "Auto — executes low-risk actions automatically, prompts for high-risk",
    3: "Full auto — runs everything without prompting",
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            stored = json.load(f)
        # Merge with defaults so new keys are always present
        merged = _deep_merge(DEFAULT_CONFIG, stored)
        return merged
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_enabled_platforms(config: dict, category: str) -> list[str]:
    return [name for name, cfg in config.get(category, {}).items() if cfg.get("enabled")]


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
