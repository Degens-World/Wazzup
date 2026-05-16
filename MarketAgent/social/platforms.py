"""
Social media platform connectors.
Each platform exposes post / schedule / get_analytics methods.
Wire in real API SDKs (tweepy, facebook-sdk, etc.) when credentials are set.
"""
from datetime import datetime
from typing import Optional


class BaseSocial:
    name = "Base"

    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get("enabled", False)

    def status(self) -> dict:
        return {"platform": self.name, "enabled": self.enabled, "configured": self._is_configured()}

    def _is_configured(self) -> bool:
        raise NotImplementedError

    def post(self, content: str, image_path: Optional[str] = None) -> dict:
        self._check()
        return self._post(content, image_path)

    def schedule(self, content: str, publish_at: datetime, image_path: Optional[str] = None) -> dict:
        self._check()
        return self._schedule(content, publish_at, image_path)

    def get_analytics(self) -> dict:
        self._check()
        return self._get_analytics()

    def _check(self):
        if not self.enabled:
            raise RuntimeError(f"{self.name} is not enabled")
        if not self._is_configured():
            raise RuntimeError(f"{self.name} credentials not configured")

    def _post(self, content, image_path) -> dict:
        return {"note": f"{self.name} posting not yet implemented — add API call here"}

    def _schedule(self, content, publish_at, image_path) -> dict:
        return {"note": f"{self.name} scheduling not yet implemented — add API call here"}

    def _get_analytics(self) -> dict:
        return {"note": f"{self.name} analytics not yet implemented — add API call here"}


class TwitterSocial(BaseSocial):
    name = "Twitter / X"

    def _is_configured(self) -> bool:
        return bool(self.config.get("api_key") and self.config.get("access_token"))


class InstagramSocial(BaseSocial):
    name = "Instagram"

    def _is_configured(self) -> bool:
        return bool(self.config.get("access_token") and self.config.get("account_id"))


class LinkedInSocial(BaseSocial):
    name = "LinkedIn"

    def _is_configured(self) -> bool:
        return bool(self.config.get("access_token") and self.config.get("person_id"))


class FacebookSocial(BaseSocial):
    name = "Facebook"

    def _is_configured(self) -> bool:
        return bool(self.config.get("access_token") and self.config.get("page_id"))


PLATFORM_MAP = {
    "twitter": TwitterSocial,
    "instagram": InstagramSocial,
    "linkedin": LinkedInSocial,
    "facebook": FacebookSocial,
}


def get_platforms(social_config: dict) -> dict[str, BaseSocial]:
    return {
        key: PLATFORM_MAP[key](cfg)
        for key, cfg in social_config.items()
        if key in PLATFORM_MAP
    }
