import os
from typing import Optional, List, Annotated
from fastapi import FastAPI, Request, Query, HTTPException,Form,File,UploadFile
from fastapi.responses import HTMLResponse , FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from file_storage import upload_file
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings
from db import get_db_session
from models import JobBoard,JobPost
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field,field_validator



engine = create_engine(str(settings.DATABASE_URL))
with sessionmaker(bind=engine)() as session:
    session.execute(text("SELECT 1"))
    print("All good!")




BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 1. Mount the static directory at /static
static_dir = os.path.join(BASE_DIR, "static")
#app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


if not settings.PRODUCTION:
    app.mount("/uploads", StaticFiles(directory="uploads"))



# # 2. Setup Jinja2 templates directory
# templates_dir = os.path.join(BASE_DIR, "templates")
# templates = Jinja2Templates(directory=templates_dir)

@app.get("/api/health")
async def health():
    try:
        with get_db_session as s9ession:
            session.execute(text("SELECT 1"))
            print("All good!")
            return {"DB_STATUS":"OK"}
    
    except:
        return {"DB_STATUS":"NOT_OKAY"}



'''app.get("/api/job-boards/{job_board_id}/posts")
async def api_job_boards (job_board_id: int):
    with get_db_session() as session:
       jobBoards = session.query(JobBoard).all()
       posts = session.query(JobPost).filter(JobPost.job_board_id == job_board_id).all()
       #posts = session.query(JobPost).all()
       return posts

@app.get("/api/job-boards/{job_board_id}/posts")
async def api_company_job_board(job_board_id):
  with get_db_session() as session:
     Posts = session.query(JobPost).filter(JobPost.job_board_id.__eq__(job_board_id)).all()
     return Posts

@app.get("/api/job-boards/{slug}")
async def api_company_job_board(slug):
  with get_db_session() as session:
     Posts = session.query(JobPost).join(JobPost.job_board).filter(JobBoard.slug.__eq__(slug)).all()
     return  Posts'''
    


# 🔹 List all job boards (React will call this)
@app.get("/api/job-boards")
async def list_job_boards():
    with get_db_session() as session:
        boards = session.query(JobBoard).all()
        return boards


# 🔹 Get posts by job_board_id (used by /job-boards/:jobBoardId/job-posts)
@app.get("/api/job-boards/{job_board_id}/posts")
async def get_job_posts_by_board_id(job_board_id: int):
    with get_db_session() as session:
        posts = (
            session.query(JobPost)
            .filter(JobPost.job_board_id == job_board_id)
            .all()
        )
        return posts


# (Optional) 🔹 Get posts by slug – if later you want slug URLs
@app.get("/api/job-boards/{slug}")
async def get_job_posts_by_slug(slug: str):
    with get_db_session() as session:
        posts = (
            session.query(JobPost)
            .join(JobPost.job_board)
            .filter(JobBoard.slug == slug)
            .all()
        )
        return posts

    
 
    
'''@app.get("/health")
async def health():
  with sessionmaker(bind=engine)() as session:
    if session.execute(text("SELECT 1")):
        print("All good!")
        return {"DB_status": "ok"}
    else:
        return {"DB_status":"not ok"}'''

@app.get("/api/acme")
async def home():
    return FileResponse("static/acme.html")

'''@app.get("/acme")
async def home():
    return "<h2>hello<h2>"
'''

@app.get("/api/acc")
async def home():
    return HTMLResponse(content ="<h2>hello<h2>")


@app.get("/api/index")
async def home():
    index_path = os.path.join(BASE_DIR, "static", "index.html")
    return FileResponse(index_path)




'''@app.post("api/job-boards")
async def api_create_new_job_board(request: Request):
    body=await request.body()
    raw_text = body.decode()
    print(request.headers.get('content-type'))
    print(raw_text)
    return {}


@app.post("/api/job-boards")
async def api_create_new_job_board(slug: Annotated[str,Form()]):
    return {"slug":slug}

class JobBoardNumbersInput(BaseModel):
    slug: str
    numbers: list[int]

@app.post("/api/job-boards")
async def create_job_board_and_calc(data: JobBoardNumbersInput):
    total = sum(data.numbers)
    product = 1
    for n in data.numbers:
        product *= n

    return {
        "slug": data.slug,
        "numbers": data.numbers,
        "sum": total,
        "product": product
    }'''

class JobBoardForm(BaseModel):
    slug: str = Field(..., min_length=3, max_length=20)

    @field_validator("slug")
    @classmethod
    def to_lowercase(cls, v):
        return v.lower()


@app.post("/api/job-boards")
async def api_create_new_job_board(
    slug: Annotated[str, Form(...)],
    logo: UploadFile = File(...)
):
    # 1) Validate/normalize slug via Pydantic
    job_board_form = JobBoardForm(slug=slug)

    # 2) Read uploaded file contents
    logo_contents = await logo.read()

    # 3) Store file and get URL
    file_url = upload_file(
        "company_logo",     # bucket/folder name
        logo.filename,       # filename
        logo_contents,       # bytes
        logo.content_type,   # MIME type
    )

    # 4) Save new JobBoard in DB
    with get_db_session() as session:
        new_job_board = JobBoard(
            slug=job_board_form.slug,
            logo_url=file_url,
        )
        session.add(new_job_board)
        session.commit()
        session.refresh(new_job_board)

        # 5) Return the row
        return new_job_board


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

app.mount("/assets", StaticFiles(directory="frontend/build/client/assets"))

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
  indexFilePath = os.path.join("frontend", "build", "client", "index.html")
  return FileResponse(path=indexFilePath, media_type="text/html")

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
