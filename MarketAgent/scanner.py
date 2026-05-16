import socket
import re
import httpx
import whois
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import Optional


HOSTING_SIGNATURES = {
    "Vercel": ["vercel.com", "vercel-dns.com", "cname.vercel-dns.com"],
    "Netlify": ["netlify.app", "netlify.com"],
    "GitHub Pages": ["github.io", "github.com"],
    "Cloudflare Pages": ["pages.dev", "cloudflare.com"],
    "AWS": ["amazonaws.com", "awsdns", "cloudfront.net"],
    "Google Cloud": ["googleusercontent.com", "googleapis.com", "google.com"],
    "Azure": ["azurewebsites.net", "azure.com", "trafficmanager.net"],
    "Heroku": ["heroku.com", "herokudns.com"],
    "DigitalOcean": ["digitalocean.com", "do.co"],
    "Squarespace": ["squarespace.com", "sqsp.net"],
    "Wix": ["wix.com", "wixdns.net"],
    "WordPress.com": ["wordpress.com", "wpengine.com"],
    "Shopify": ["shopify.com", "myshopify.com"],
    "Fastly": ["fastly.net"],
    "Akamai": ["akamai.net", "akamaiedge.net"],
}

HOSTING_HEADERS = {
    "Vercel": "x-vercel-id",
    "Netlify": "x-nf-request-id",
    "Cloudflare": "cf-ray",
    "AWS CloudFront": "x-amz-cf-id",
    "GitHub Pages": "x-github-request-id",
    "Fastly": "x-served-by",
}


def normalize_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def detect_hosting(url: str) -> dict:
    result = {"provider": "Unknown", "method": "", "nameservers": [], "ip": ""}
    parsed = urlparse(normalize_url(url))
    domain = parsed.netloc or parsed.path

    try:
        ip = socket.gethostbyname(domain)
        result["ip"] = ip
    except Exception:
        pass

    # Check response headers
    try:
        resp = httpx.get(normalize_url(url), follow_redirects=True, timeout=10)
        headers = {k.lower(): v for k, v in resp.headers.items()}
        for provider, header in HOSTING_HEADERS.items():
            if header in headers:
                result["provider"] = provider
                result["method"] = "response header"
                return result
        server = headers.get("server", "")
        if server:
            result["server_header"] = server
    except Exception:
        pass

    # Check WHOIS / nameservers
    try:
        w = whois.whois(domain)
        ns = w.name_servers or []
        if isinstance(ns, str):
            ns = [ns]
        ns = [n.lower() for n in ns]
        result["nameservers"] = ns
        for provider, signatures in HOSTING_SIGNATURES.items():
            for sig in signatures:
                if any(sig in n for n in ns):
                    result["provider"] = provider
                    result["method"] = "nameserver"
                    return result
    except Exception:
        pass

    return result


def audit_seo(url: str) -> dict:
    url = normalize_url(url)
    issues = []
    recommendations = []
    score = 100
    data = {}

    try:
        resp = httpx.get(url, follow_redirects=True, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; MarketAgent/1.0)"
        })
        soup = BeautifulSoup(resp.text, "html.parser")

        # Title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""
        data["title"] = title
        if not title:
            issues.append("Missing <title> tag")
            score -= 15
        elif len(title) < 30:
            recommendations.append(f"Title is short ({len(title)} chars) — aim for 50-60")
            score -= 5
        elif len(title) > 60:
            recommendations.append(f"Title is too long ({len(title)} chars) — keep under 60")
            score -= 5

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        desc = meta_desc["content"] if meta_desc and meta_desc.get("content") else ""
        data["meta_description"] = desc
        if not desc:
            issues.append("Missing meta description")
            score -= 10
        elif len(desc) < 120:
            recommendations.append(f"Meta description is short ({len(desc)} chars) — aim for 150-160")
            score -= 3
        elif len(desc) > 160:
            recommendations.append(f"Meta description too long ({len(desc)} chars) — keep under 160")
            score -= 3

        # H1
        h1_tags = soup.find_all("h1")
        data["h1_count"] = len(h1_tags)
        if len(h1_tags) == 0:
            issues.append("No H1 tag found")
            score -= 10
        elif len(h1_tags) > 1:
            recommendations.append(f"Multiple H1 tags ({len(h1_tags)}) — use only one per page")
            score -= 5

        # Canonical
        canonical = soup.find("link", attrs={"rel": "canonical"})
        data["canonical"] = canonical["href"] if canonical else None
        if not canonical:
            recommendations.append("No canonical tag — add one to prevent duplicate content issues")
            score -= 5

        # Open Graph
        og_title = soup.find("meta", attrs={"property": "og:title"})
        og_desc = soup.find("meta", attrs={"property": "og:description"})
        og_image = soup.find("meta", attrs={"property": "og:image"})
        data["og"] = {
            "title": og_title["content"] if og_title else None,
            "description": og_desc["content"] if og_desc else None,
            "image": og_image["content"] if og_image else None,
        }
        if not og_title or not og_image:
            recommendations.append("Incomplete Open Graph tags — affects social media sharing")
            score -= 5

        # Images without alt
        imgs = soup.find_all("img")
        imgs_no_alt = [img for img in imgs if not img.get("alt")]
        data["images_total"] = len(imgs)
        data["images_missing_alt"] = len(imgs_no_alt)
        if imgs_no_alt:
            issues.append(f"{len(imgs_no_alt)} image(s) missing alt text")
            score -= min(10, len(imgs_no_alt) * 2)

        # HTTPS
        data["https"] = resp.url.scheme == "https"
        if not data["https"]:
            issues.append("Site is not served over HTTPS")
            score -= 20

        # robots.txt
        robots_resp = httpx.get(f"{url}/robots.txt", timeout=5)
        data["has_robots_txt"] = robots_resp.status_code == 200
        if not data["has_robots_txt"]:
            recommendations.append("No robots.txt found")
            score -= 3

        # sitemap
        sitemap_resp = httpx.get(f"{url}/sitemap.xml", timeout=5)
        data["has_sitemap"] = sitemap_resp.status_code == 200
        if not data["has_sitemap"]:
            recommendations.append("No sitemap.xml found — submit one to Google Search Console")
            score -= 5

        # Page load size
        data["page_size_kb"] = round(len(resp.content) / 1024, 1)
        if data["page_size_kb"] > 500:
            recommendations.append(f"Page size is large ({data['page_size_kb']} KB) — consider optimizing assets")
            score -= 5

        data["status_code"] = resp.status_code
        data["final_url"] = str(resp.url)

    except httpx.RequestError as e:
        return {"error": f"Could not reach site: {e}", "score": 0, "issues": [], "recommendations": []}

    return {
        "score": max(0, score),
        "issues": issues,
        "recommendations": recommendations,
        "data": data,
    }


def full_scan(url: str) -> dict:
    url = normalize_url(url)
    hosting = detect_hosting(url)
    seo = audit_seo(url)
    return {"url": url, "hosting": hosting, "seo": seo}
