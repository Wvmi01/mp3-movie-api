import logging
import sqlite3

import pandas as pd

from .database import get_connection, initialize_database


logger = logging.getLogger(__name__)
MOVIE_COLUMNS = ["title", "release_year", "rating", "genre"]


class MovieStorage:
    def __init__(self, db_path="data/movies.db"):
        self.db_path = db_path
        initialize_database(self.db_path)

    def save(self, df):
        """Replace all movie rows in one transaction."""
        connection = get_connection(self.db_path)

        try:
            rows = df[MOVIE_COLUMNS].astype(object)
            rows = rows.where(pd.notna(rows), None)
            values = list(rows.itertuples(index=False, name=None))

            connection.execute("DELETE FROM movies")

            connection.executemany(
                """
                INSERT INTO movies (title, release_year, rating, genre)
                VALUES (?, ?, ?, ?)
                """,
                values
            )

            connection.commit()
            logger.debug(f"Stored movies in SQLite: rows={len(values)}")

        except sqlite3.Error:
            connection.rollback()
            raise

        finally:
            connection.close()

    def get(self):
        """Return the four movie columns as a DataFrame, ordered by id."""
        connection = get_connection(self.db_path)

        try:
            sql_statement = """
                SELECT title, release_year, rating, genre
                FROM movies
                ORDER BY id
            """

            rows = connection.execute(sql_statement).fetchall()

            df = pd.DataFrame([dict(row) for row in rows], columns=MOVIE_COLUMNS)

            return df

        finally:
            connection.close()