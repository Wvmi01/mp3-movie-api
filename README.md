# MP3 Movie API #

This project uses FastAPI to create a REST API with different endpoints for uploading, retrieving, searching, and processing movie data. It builds onto MP2 by using SQLite to store movie data instead of keeping everything in memory. The uploaded movies are stored in a database and can be retrieved or searched using SQL queries. MP3 also reuses the functions from MP1 for data validation, removing duplicates, handling missing values, and removing outliers. It uses Pydantic models to organize requests and responses and middleware to log HTTP requests and errors. FakeRedis is used to temporarily cache retrieved movie data so the API doesn't have to query the database every time. This allow the retrieval time to be faster. When new movies are uploaded or processed, the cache is cleared to make sure the results are updated, and pytest is used to test whether the API works as expected.

# Running the API #
Install the required packages:
python3 -m pip install -r requirements.txt

Start the API:
python3 -m uvicorn main:app --reload

Open /docs to test the endpoints.

# Running Tests with Pytest #
python3 -m pytest tests -v

# Processing Request Example # 
POST /movies/process

**Upload file** 

{
  "validation": {
    "required_columns": ["title", "release_year", "rating", "genre"],
    "numeric_columns": ["release_year", "rating"]
  },
  "processing": {
    "remove_duplicates": true,
    "missing": {
      "enabled": true,
      "axis": "rows"
    },
    "outliers": {
      "enabled": true,
      "columns": ["rating"],
      "method": "iqr",
      "threshold": 1.5
    }
  }
}

**Expected Response:**

{
  "validation_rows_removed": 0,
  "cleaning_report": {
    "rows_before": 20,
    "rows_after": 16,
    "rows_removed": 4,
    "columns_before": 4,
    "columns_after": 4,
    "columns_removed": 0
  }
}

