# Archhive

This project fetches and displays abstracts and AI-generated summaries of arXiv articles, either by date or by category, with an option to view a specific article by its ID. It consists of a **FastAPI backend** and a **HTML+JavaScript frontend**.

## Features

- Fetch and display articles by:
  - Specific date
  - Random selection within a category
  - Specific article ID
- View both **abstracts** and **AI-generated summaries**
- Store and update content in a **PostgreSQL** database
- Math rendering support via **MathJax**
- FastAPI backend with multiple endpoints
- Responsive UI with minimal styling

---

## Running Locally

This project is built on top of a postgres DB to store and serve both the article information and the intelligent content generated. You would need to run a DB locally and configure the interaction to the DB (IP/credentials/etc.). We recommend some containerized solution. Maybe a docker-compose solution with DB+administrative tool.

After that, you'd need to configure the interaction with some LLM provider (we currently recommend [OpenRouter](openrouter.ai)) so that you can generate some intelligence on top of the articles.

To build and run the containerized process

Running docker
```bash
docker build -t archhiver .
#docker run -d --name archiver --env-file <env_path> archhiver
```

The env file has the content
```
API_KEY=<API_KEY>
```


