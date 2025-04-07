from pydantic import BaseModel


class ArticleResponse(BaseModel):
    id: str
    title: str
    abstract: str | None
    summary: str | None