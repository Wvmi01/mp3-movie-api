import pytest
import pandas as pd

from src import MovieStorage
import main

def test_movies_persist(client, test_storage, uploaded_movies):
    new_storage = MovieStorage(test_storage.db_path)

    df = new_storage.get()
    total_rows = new_storage.count_movies()

    assert len(df) == 20
    assert total_rows == 20
    assert df.columns.tolist() == ["title", "release_year", "rating", "genre"]

    expected_df = pd.read_csv("fixtures/sample_movies.csv")

    assert df["title"].tolist() == expected_df["title"].tolist()

    stored_movies = new_storage.select_columns(["title", "release_year", "rating", "genre"], limit=100)

    response = client.get("/movies?limit=100")

    assert response.status_code == 200
    assert response.json()["total_rows"] == 20

    expected_ids = list(range(1, 21))

    assert [movie["id"] for movie in stored_movies] == expected_ids
    assert [movie["id"] for movie in response.json()["data"]] == expected_ids

def test_cache_and_processing(client, uploaded_movies, processing_body):
    response_100 = client.get("/movies?limit=100")
    response_1 = client.get("/movies?limit=1")

    assert response_100.status_code == 200
    assert response_1.status_code == 200

    assert main.cache.get(100) == response_100.json()
    assert main.cache.get(1) == response_1.json()

    

    repeated_response = client.get("/movies?limit=100")

    assert repeated_response.status_code == 200
    assert repeated_response.json() == response_100.json()


    process_response = client.post(
        "/movies/process",
        json=processing_body
    )

    assert process_response.status_code == 200

    report = process_response.json()

    assert report["validation_rows_removed"] == 0
    assert report["cleaning_report"]["rows_before"] == 20
    assert report["cleaning_report"]["rows_after"] == 16
    assert report["cleaning_report"]["rows_removed"] == 4

    assert main.cache.get(100) is None
    assert main.cache.get(1) is None


    cleaned_response = client.get("/movies?limit=100")

    assert cleaned_response.status_code == 200

    cleaned_data = cleaned_response.json()

    assert cleaned_data["total_rows"] == 16
    assert len(cleaned_data["data"]) == 16

    expected_titles = [
        f"Movie {chr(i)}" for i in range(ord("A"), ord("P") + 1)
    ]

    assert [movie["title"] for movie in cleaned_data["data"]] == expected_titles

    expected_ids = list(range(1, 17))

    assert [movie["id"] for movie in cleaned_data["data"]] == expected_ids

    assert main.cache.get(100) == cleaned_data



def test_cache_hit_skips_database(client, uploaded_movies, monkeypatch):
    first_response = client.get("/movies?limit=100")

    assert first_response.status_code == 200

   
    def fail_if_called(*args, **kwargs):
        pytest.fail("Database should not be accessed on a cache HIT")

    monkeypatch.setattr(main.storage, "select_columns", fail_if_called)
    monkeypatch.setattr(main.storage, "count_movies", fail_if_called)

   
    second_response = client.get("/movies?limit=100")

    assert second_response.status_code == 200
    assert second_response.json() == first_response.json()
