import psycopg2
from psycopg2.extras import execute_values

CLIENT_PAGINATION_LIMIT = 1000


class PGDB:
    DB_CONFIG = {
        "dbname": "archhive",
        "user": "postgres",
        "password": "psp",
        "host": "192.168.1.59",
        "port": "5432",
    }

    def __init__(self):
        self.connection = self.connect_db()
        self.cursor = self.connection.cursor()

    def connect_db(self, config=None):
        """Establish connection to PostgreSQL."""
        return psycopg2.connect(**(config or self.DB_CONFIG))

    def insert_article(self, articles) -> None:
        """Insert article into PostgreSQL, avoiding duplicates."""

        query = """
            INSERT INTO test.raw (
                title,
                authors,
                id,
                published,
                updated,
                inserted,
                abstract,
                comment,
                primary_category,
                categories
            )
            VALUES %s
            ON CONFLICT (id) DO NOTHING;
        """
        try:
            execute_values(
                self.cursor,
                query,
                articles,
                template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            )
        except Exception as e:
            print(f"Database error: {e}")
            raise
            # for article in articles:
            #    for el in article:
            #        print(el)
            #    print("")

    def __del__(self):
        if hasattr(self, "cursor"):
            self.cursor.close()
        if hasattr(self, "connection"):
            self.connection.close()

    def get_articles_stream(self, limit=200) -> dict:
        """

        :param limit: amount of articles to fetch. 200 is the default value for OpenRouter
        :return: N (id, abstract) pairs from the DB
        """

        query = """SELECT r.id, r.abstract
FROM test.raw r
LEFT JOIN test.llm_summary s ON r.id = s.id
WHERE s.id IS NULL OR s.replace IS TRUE
LIMIT %s;"""
        try:
            with self.connection.cursor() as cursor:  # Create a new cursor
                cursor.execute(query, (limit,))
                columns = [desc[0] for desc in cursor.description]
                for row in cursor:
                    yield dict(zip(columns, row))  # Fetch next row
        except Exception as e:
            print(f"Database error: {e}")
            raise

    def insert_summary(self, article_id, summary) -> None:
        query = """INSERT INTO test.llm_summary (
    id,
    summary,
    replace
)
VALUES (%s, %s, FALSE)
ON CONFLICT (id)
DO UPDATE SET 
    summary = EXCLUDED.summary,
    replace = EXCLUDED.replace;
        """
        try:
            self.cursor.execute(
                query,
                (
                    article_id,
                    summary,
                ),
            )
            self.connection.commit()
        except Exception as e:
            print(f"Database error: {e}")
            raise
