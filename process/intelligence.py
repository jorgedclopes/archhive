import json
import os
from openai import OpenAI

from dotenv import load_dotenv

from process.db import PGDB

load_dotenv()


class RateLimitError(ConnectionError):
    pass


db = PGDB()


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["API_KEY"],
)

post_abstract_instructions = """Explain this abstract to me at the language level of an high school graduate.
Do not insert the abstract into the response.
Make some easy to read paragraphs.
Do not make analogies If you find some term that could be considered lingo, explain it.
Do not repeat information or circle around what you are trying to say.
Do not hallucinate or make up words/information you do not know.
If you do not know what a work means, don't make it into an adjective.
If you have that information, explain how the result can help/be used.
Do not attempt to cite references."""


def generate_summary(abstract):
    content = abstract + post_abstract_instructions
    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "ArchHive",  # Optional. Site URL for rankings on openrouter.ai.
            "X-Title": "ArchHive",  # Optional. Site title for rankings on openrouter.ai.
        },
        model="microsoft/phi-3-medium-128k-instruct:free",
        messages=[{"role": "user", "content": content}],
    )
    if hasattr(completion, "error"):
        raise RateLimitError(completion.error["message"])
    return completion.choices[0].message.content


if __name__ == "__main__":
    for i, article in enumerate(db.get_articles_stream(limit=190)):
        print(f"Processing article {article['id']} - number {i+1} of the run")
        summary = generate_summary(article["abstract"])
        db.insert_summary(article["id"], summary)
