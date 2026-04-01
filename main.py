from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from tavily_service import search_tavily
from serpapi_service import search_serpapi
from custome_engine import search_google_pse
from serperdev import search_serper
from dataforseo import search_dataforseo

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        name="index.html",
        request=request
    )
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


@app.get("/search/dataforseo")
def dataforseo_search(query: str):
    results = search_dataforseo(query)
    return {"source": "dataforseo", "results": results}