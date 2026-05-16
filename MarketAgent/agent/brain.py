import anthropic
import json
from typing import Optional
from config import load_config, AUTONOMY_LABELS

SYSTEM_PROMPT = """You are MarketAgent, an autonomous SEO and digital marketing assistant.
You analyze websites, monitor performance, and take actions to improve search rankings,
drive traffic, and manage advertising campaigns.

You have access to:
- Website scanner (hosting detection, SEO audit)
- Google Analytics & Search Console data
- Ad platforms: Google Ads, Meta, X/Twitter, TikTok, LinkedIn
- Social media: Twitter/X, Instagram, LinkedIn, Facebook

When given scan results or user requests, you:
1. Identify the highest-impact issues and opportunities
2. Propose concrete, prioritized actions
3. Execute actions according to the user's autonomy level setting
4. Report results clearly

Always be specific — cite actual data, not vague suggestions.
Format your responses clearly with sections for: Issues Found, Recommended Actions, and Next Steps.
"""


class MarketAgentBrain:
    def __init__(self):
        self.config = load_config()
        self.client = anthropic.Anthropic(api_key=self.config["anthropic_api_key"])
        self.autonomy = self.config["autonomy_level"]
        self.conversation_history = []

    def _build_context(self, scan_result: Optional[dict] = None) -> str:
        ctx_parts = [
            f"Website: {self.config['website']}",
            f"Autonomy level: {self.autonomy} — {AUTONOMY_LABELS[self.autonomy]}",
        ]

        enabled_ads = [k for k, v in self.config["ads"].items() if v.get("enabled")]
        enabled_social = [k for k, v in self.config["social"].items() if v.get("enabled")]

        if enabled_ads:
            ctx_parts.append(f"Active ad platforms: {', '.join(enabled_ads)}")
        if enabled_social:
            ctx_parts.append(f"Active social platforms: {', '.join(enabled_social)}")

        if scan_result:
            ctx_parts.append(f"\nLatest scan results:\n{json.dumps(scan_result, indent=2)}")

        return "\n".join(ctx_parts)

    def analyze(self, scan_result: dict) -> str:
        context = self._build_context(scan_result)
        user_message = f"{context}\n\nAnalyze these scan results and provide your prioritized action plan."

        self.conversation_history.append({"role": "user", "content": user_message})

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=self.conversation_history,
        )

        reply = response.content[0].text
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

    def chat(self, user_input: str, scan_result: Optional[dict] = None) -> str:
        context = self._build_context(scan_result)
        message = f"{context}\n\nUser: {user_input}" if not self.conversation_history else user_input

        self.conversation_history.append({"role": "user", "content": message})

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=self.conversation_history,
        )

        reply = response.content[0].text
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

    def generate_content(self, platform: str, topic: str, website_context: str = "") -> str:
        prompt = f"""Generate {platform} content for the following:
Topic: {topic}
Website: {self.config['website']}
{f'Context: {website_context}' if website_context else ''}

Create platform-optimized content with appropriate length, tone, hashtags, and call-to-action.
"""
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def suggest_keywords(self, current_seo_data: dict) -> str:
        prompt = f"""Based on this SEO data for {self.config['website']}, suggest:
1. Primary keywords to target
2. Long-tail keyword opportunities
3. Keywords competitors are likely ranking for
4. Content gaps to fill

SEO Data: {json.dumps(current_seo_data, indent=2)}
"""
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def reset_conversation(self):
        self.conversation_history = []
        self.config = load_config()
        self.autonomy = self.config["autonomy_level"]
