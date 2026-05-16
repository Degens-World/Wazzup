"""
Ad platform connectors. Each platform returns a status dict and exposes
create_campaign / get_metrics / pause_campaign methods.
Add real API calls here when credentials are configured.
"""
from typing import Optional


class BasePlatform:
    name = "Base"

    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get("enabled", False)

    def status(self) -> dict:
        return {"platform": self.name, "enabled": self.enabled, "configured": self._is_configured()}

    def _is_configured(self) -> bool:
        raise NotImplementedError

    def get_metrics(self) -> dict:
        self._check()
        return self._get_metrics()

    def create_campaign(self, name: str, budget: float, target_url: str, keywords: list[str]) -> dict:
        self._check()
        return self._create_campaign(name, budget, target_url, keywords)

    def _check(self):
        if not self.enabled:
            raise RuntimeError(f"{self.name} is not enabled")
        if not self._is_configured():
            raise RuntimeError(f"{self.name} credentials not configured")

    def _get_metrics(self) -> dict:
        return {"note": f"{self.name} metrics not yet implemented — add API call here"}

    def _create_campaign(self, name, budget, target_url, keywords) -> dict:
        return {"note": f"{self.name} campaign creation not yet implemented — add API call here"}


class GoogleAds(BasePlatform):
    name = "Google Ads"

    def _is_configured(self) -> bool:
        return bool(self.config.get("customer_id") and self.config.get("developer_token"))


class MetaAds(BasePlatform):
    name = "Meta Ads"

    def _is_configured(self) -> bool:
        return bool(self.config.get("access_token") and self.config.get("ad_account_id"))


class TwitterAds(BasePlatform):
    name = "X / Twitter Ads"

    def _is_configured(self) -> bool:
        return bool(self.config.get("api_key") and self.config.get("access_token"))


class TikTokAds(BasePlatform):
    name = "TikTok Ads"

    def _is_configured(self) -> bool:
        return bool(self.config.get("access_token") and self.config.get("advertiser_id"))


class LinkedInAds(BasePlatform):
    name = "LinkedIn Ads"

    def _is_configured(self) -> bool:
        return bool(self.config.get("access_token") and self.config.get("account_id"))


PLATFORM_MAP = {
    "google_ads": GoogleAds,
    "meta": MetaAds,
    "twitter": TwitterAds,
    "tiktok": TikTokAds,
    "linkedin": LinkedInAds,
}


def get_platforms(ads_config: dict) -> dict[str, BasePlatform]:
    return {
        key: PLATFORM_MAP[key](cfg)
        for key, cfg in ads_config.items()
        if key in PLATFORM_MAP
    }
