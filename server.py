from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files (CSS, JS, images, etc.)
if not os.path.exists("./static"):
    os.mkdir("./static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
if not os.path.exists("./templates"):
    os.mkdir("./templates")
templates = Jinja2Templates(directory="templates")


from fastapi import FastAPI
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Database connection
conn = psycopg2.connect(
    dbname="archhive", user="postgres", password="psp", host="192.168.1.59", port="5432"
)


@app.get("/articles")
def get_articles(date: str = Query(None, description="Date in YYYY-MM-DD format")):
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        logger.debug(f"{date=}")
        if date:
            cursor.execute(
                """
                SELECT r.id, r.title, r.abstract, COALESCE(s.summary, NULL) as summary
                FROM test.raw r
                LEFT JOIN test.llm_summary s ON r.id = s.id
                WHERE r.published = %s
                LIMIT 10
                """,
                (date,),
            )
        else:
            cursor.execute(
                """
                SELECT r.id, r.title, r.abstract, COALESCE(s.summary, NULL) as summary
                FROM test.raw r
                LEFT JOIN test.llm_summary s ON r.id = s.id
                LIMIT 10
                """
            )
        articles = cursor.fetchall()
    return articles


@app.get("/random_articles")
def get_random_articles(
    category: str = Query(..., description="Category name"), limit: int = 1
):
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        wildcard_category = f"%{category}%"
        cursor.execute(
            """
            SELECT r.id, r.title, r.abstract, s.summary
            FROM test.raw r
            LEFT JOIN test.llm_summary s ON r.id = s.id
            WHERE r.categories LIKE %s
            AND s.summary IS NOT NULL
            ORDER BY RANDOM()
            LIMIT %s
            """,
            (wildcard_category, limit),
        )
        articles = cursor.fetchall()
        logger.info(
            f"Random articles fetched: {[article['id'] for article in articles]}"
        )
    return articles


@app.get("/categories")
def get_categories():
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT name
            FROM test.category
            ORDER BY name;
            """
        )
        categories = [row["name"] for row in cursor.fetchall()]
    return categories


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
