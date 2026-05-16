import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from config import load_config, save_config, AUTONOMY_LABELS
from scanner import full_scan
from agent.brain import MarketAgentBrain
from ads.platforms import get_platforms as get_ad_platforms
from social.platforms import get_platforms as get_social_platforms

app = FastAPI(title="MarketAgent")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

brain = MarketAgentBrain()
last_scan_result = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    config = load_config()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "config": config,
        "autonomy_labels": AUTONOMY_LABELS,
        "last_scan": last_scan_result,
    })


@app.post("/api/scan")
async def api_scan():
    global last_scan_result
    config = load_config()
    url = config.get("website", "")
    if not url:
        return JSONResponse({"error": "No website configured"}, status_code=400)
    last_scan_result = full_scan(url)
    return last_scan_result


@app.post("/api/analyze")
async def api_analyze():
    if not last_scan_result:
        return JSONResponse({"error": "Run a scan first"}, status_code=400)
    result = brain.analyze(last_scan_result)
    return {"analysis": result}


@app.post("/api/chat")
async def api_chat(request: Request):
    body = await request.json()
    message = body.get("message", "")
    reply = brain.chat(message, last_scan_result if last_scan_result else None)
    return {"reply": reply}


@app.post("/api/generate-content")
async def api_generate_content(request: Request):
    body = await request.json()
    platform = body.get("platform", "")
    topic = body.get("topic", "")
    content = brain.generate_content(platform, topic)
    return {"content": content}


@app.get("/api/config")
async def api_get_config():
    config = load_config()
    config.pop("anthropic_api_key", None)
    return config


@app.post("/api/config")
async def api_save_config(request: Request):
    body = await request.json()
    config = load_config()
    if "website" in body:
        config["website"] = body["website"]
    if "autonomy_level" in body:
        config["autonomy_level"] = int(body["autonomy_level"])
    if "ads" in body:
        for platform, settings in body["ads"].items():
            if platform in config["ads"]:
                config["ads"][platform].update(settings)
    if "social" in body:
        for platform, settings in body["social"].items():
            if platform in config["social"]:
                config["social"][platform].update(settings)
    save_config(config)
    brain.reset_conversation()
    return {"status": "saved"}


@app.get("/api/platforms")
async def api_platforms():
    config = load_config()
    ads = {k: p.status() for k, p in get_ad_platforms(config["ads"]).items()}
    social = {k: p.status() for k, p in get_social_platforms(config["social"]).items()}
    return {"ads": ads, "social": social}


def run_web(host: str = "0.0.0.0", port: int = 8080):
    uvicorn.run(app, host=host, port=port)
