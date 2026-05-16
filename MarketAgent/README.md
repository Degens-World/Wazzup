# MarketAgent

Autonomous SEO & digital marketing agent powered by Claude AI.

## Features

- **Website Scanner** — detect hosting provider, audit SEO health, check for common issues
- **AI Analysis** — Claude-powered action plans based on real scan data
- **Ad Platform Integration** — Google Ads, Meta, X/Twitter, TikTok, LinkedIn
- **Social Media Management** — post and schedule content on Twitter/X, Instagram, LinkedIn, Facebook
- **Content Generator** — AI-written platform-optimized social posts
- **Two UIs** — Rich terminal dashboard or clean browser-based HTML dashboard

## Autonomy Levels

| Level | Behavior |
|---|---|
| 0 | Manual — shows recommendations only, executes nothing |
| 1 | Semi-auto — proposes actions and waits for approval |
| 2 | Auto — runs low-risk actions automatically, prompts for high-risk |
| 3 | Full auto — handles everything without prompting |

## Setup

```bash
cd MarketAgent
pip install -r requirements.txt
python main.py
```

On first run, the setup wizard collects:
- Your website URL
- Anthropic API key
- Autonomy level preference
- Which ad and social platforms to enable

## Running

```bash
# CLI mode
python main.py cli

# Web UI (opens at http://localhost:8080)
python main.py web
```

## Adding API Credentials

After initial setup, go to **Settings** (web UI) or run the setup wizard again (CLI) to add credentials for each platform you want to use.

Each platform module is in `ads/platforms.py` and `social/platforms.py` — drop in the real SDK calls once credentials are configured.

## Project Structure

```
MarketAgent/
├── main.py              # entry point
├── config.py            # config management
├── scanner.py           # hosting detection + SEO audit
├── agent/brain.py       # Claude AI orchestration
├── ads/platforms.py     # ad platform connectors
├── social/platforms.py  # social media connectors
├── ui/cli.py            # Rich terminal UI
└── ui/web/              # FastAPI + HTML web UI
```
