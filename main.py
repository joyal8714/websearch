from fastapi import FastAPI, Request, Response
import requests as http_requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from tavily_service import search_tavily
from serpapi_service import search_serpapi
from custome_engine import search_google_pse
from serperdev import search_serper

from exa_search import search_exa          # ← add this

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(name="index.html", request=request)

@app.get("/search/tavily")
def tavily_search(query: str):
    results = search_tavily(query)
    return {"source": "tavily", "results": results}

@app.get("/search/serpapi")
def serpapi_search(query: str):
    results = search_serpapi(query)
    return {"source": "serpapi", "results": results}

@app.get("/search/google_pse")
def google_pse_search(query: str):
    results = search_google_pse(query)
    return {"source": "google_pse", "results": results}

@app.get("/search/serper")
def serper_search(query: str):
    results = search_serper(query)
    return {"source": "serper", "results": results}


@app.get("/search/exa")
def exa_search_endpoint(query: str):
    results = search_exa(query)
    return {"source": "exa", "results": results}


@app.get("/proxy-image")
def proxy_image(url: str):
    """Proxy image requests to bypass CDN hotlink protection on luxury sites."""
    try:
        # Extract origin for Referer header (e.g. https://media.tiffany.com -> https://www.tiffany.com)
        from urllib.parse import urlparse
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"

        resp = http_requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": origin,
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            },
            timeout=10,
            stream=True,
            verify=False,  # bypass SSL cert issues with luxury CDNs
        )
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        return Response(content=resp.content, media_type=content_type)
    except Exception as e:
        print(f"Proxy image error for {url}: {e}")
        return Response(status_code=404)