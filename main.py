import os
from typing import Optional
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse , FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings
from db import get_db_session

engine = create_engine(str(settings.DATABASE_URL))
with sessionmaker(bind=engine)() as session:
    session.execute(text("SELECT 1"))
    print("All good!")




BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

# 1. Mount the static directory at /static
static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))



# # 2. Setup Jinja2 templates directory
# templates_dir = os.path.join(BASE_DIR, "templates")
# templates = Jinja2Templates(directory=templates_dir)

@app.get("/health")
async def health():
    try:
        with get_db_session as session:
            session.execute(text("SELECT 1"))
            print("All good!")
            return {"DB_STATUS":"OK"}
    
    except:
        return {"DB_STATUS":"NOT_OKAY"}




@app.get("/health")
async def health():
  with sessionmaker(bind=engine)() as session:
    if session.execute(text("SELECT 1")):
        print("All good!")
        return {"DB_status": "ok"}
    else:
        return {"DB_status":"not ok"}

@app.get("/api/acme")
async def home():
    return FileResponse("static/acme.html")

'''@app.get("/acme")
async def home():
    return "<h2>hello<h2>"
'''

@app.get("/acc")
async def home():
    return HTMLResponse(content ="<h2>hello<h2>")


@app.get("/index")
async def home():
    index_path = os.path.join(BASE_DIR, "static", "index.html")
    return FileResponse(index_path)


    # """
    # Render an HTML page that uses static CSS, JS, and an image.
    # """
    # return templates.TemplateResponse(
    #     "index.html",
    #     {
    #         "request": request,
    #         "title": "FastAPI Static Files Demo",
    #         "message": "Serving CSS, JS, and images from /static",
    #     },
    # )


'''@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # Your dynamic data here
    jobs = [
        {"title": "Software Engineer", "salary": "₹12,00,000"},
        {"title": "Data Analyst", "salary": "₹7,50,000"},
        {"title": "UI/UX Designer", "salary": "₹9,00,000"},
    ]

    return templates.TemplateResponse(
       request=request,name="job-board.html",context={"jobs":jobs}  

    )'''

COMPANIES = [
    {
        "name": "Google",
        "slug": "google",
        "logo": "google.png",
        "jobs": [
            {"title": "Software Engineer", "salary": "₹25,00,000 / year"},
            {"title": "Data Engineer", "salary": "₹22,00,000 / year"},
        ],
    },
    {
        "name": "Amazon",
        "slug": "amazon",
        "logo": "amazon.png",
        "jobs": [
            {"title": "Cloud Architect", "salary": "₹30,00,000 / year"},
            {"title": "DevOps Engineer", "salary": "₹20,00,000 / year"},
        ],
    },
    {
        "name": "StartUpX",
        "slug": "startupx",
        "logo": "startupx.png",
        "jobs": [
            {"title": "Full Stack Developer", "salary": "₹15,00,000 / year"},
        ],
    },
]


@app.get("/api", response_class=HTMLResponse)
async def home(request: Request, q: Optional[str] = Query(default=None), slug: Optional[str] = Query(default=None),):
    
    """
    Home page:
    - if ?slug=... is passed -> show only that company
    - elif ?q=... is passed  -> filter by name
    - else                   -> show all
    """
    selected_slug = None

    if slug:
        selected_slug = slug.strip().lower()
        company = next((c for c in COMPANIES if c["slug"] == selected_slug), None)
        companies = [company] if company else []
    elif q:
        query = q.lower().strip()
        companies = [c for c in COMPANIES if query in c["name"].lower()]
    else:
        companies = COMPANIES


    return templates.TemplateResponse(
        "job-board.html",
        {
            "request": request,
            "companies": companies,
            "search_query": q or "",
            "all_companies": COMPANIES,
            "selected_slug": selected_slug or "",

        },
    )


@app.get("/api/{company_slug}", response_class=HTMLResponse)
async def company_page(request: Request, company_slug: str):
    """
    Pretty URLs:
    /google, /amazon, /startupx
    """
    slug = company_slug.lower().strip()

    company = next((c for c in COMPANIES if c["slug"] == slug), None)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Reuse same template, but with only this company
    return templates.TemplateResponse(
        "job-board.html",
        {
            "request": request,
            "companies": [company],
            "search_query": company["name"],
            "all_companies": COMPANIES,
            "selected_slug": company["slug"],

        },
    )
'''

@app.get("/api/{company_slug}")
async def company_jobs(company_slug: str):
    """
    JSON API:
    /api/google -> [ { "title": "...", "salary": "..." }, ... ]
    """
    slug = company_slug.lower().strip()

    company = next((c for c in COMPANIES if c["slug"] == slug), None)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Return only jobs as JSON
    return company["jobs"]
'''
''' Optional: avoid /favicon.ico being treated as a company slug
@app.get("/favicon.ico")
async def favicon():
    return HTMLResponse(status_code=204)'''
