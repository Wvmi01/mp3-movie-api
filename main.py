import io
import json
import logging
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import DatasetInfo, DatasetStorage, HealthResponse, ProcessConfig, ProcessingReport, setup_logging, log_requests, MovieStorage, MovieUploadInfo, MovieDataResponse, MovieProcessingReport
from src.storage import MOVIE_COLUMNS
from data_pipeline import create_cleaning_report, process_data, validate_dataframe

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
app.middleware("http")(log_requests)
storage = MovieStorage()


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/upload", response_model=MovieUploadInfo)
async def upload_movies(file: UploadFile = File(...)):
    """Read and store a CSV upload."""
    path = Path(file.filename or "").suffix.lower()

    if path != ".csv":
        logger.warning(f"Unsupported file format: {path}")
        raise HTTPException(
            status_code=400,
            detail = "Only CSV files are supported"
        )

    contents = await file.read()

    try:
        df = pd.read_csv(io.BytesIO(contents))
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError
    ):
        logger.warning("Invalid CSV upload")
        raise HTTPException(
            status_code=400,
            detail="Unable to read CSV file"
    )

    if set(df.columns) != set(MOVIE_COLUMNS):
        logger.warning("Invalid movie columns")
        raise HTTPException(
            status_code=400,
            detail="CSV must contain exactly the required movie columns"
        )

    if df.empty:
        logger.warning("Uploaded CSV has no movie rows")
        raise HTTPException(
            status_code=400,
            detail="CSV must contain at least one movie"
        )

    df = df[MOVIE_COLUMNS]

    storage.save(df)

    logger.info(f"Uploaded movies: filename={file.filename}, rows={len(df)}")

    return {
        "filename": file.filename,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": df.columns.tolist()
    }


@app.get("/movies", response_model=MovieDataResponse)
def get_movies(limit: int = Query(default=100, ge=1)):
    """Retrieve stored movies."""

    data = storage.select_columns(MOVIE_COLUMNS, limit)
    total_rows = storage.count_movies()

    logger.info(f"Retrieved movies: rows={len(data)}")

    return {
        "data": data,
        "total_rows": total_rows
    }

@app.get("/movies/search", response_model=list[dict])
def query_movies(
    columns: list[str] = Query(default=["title"]),
    min_rating: float = Query(default=0, ge=0, le=10),
    limit: int = Query(default=100, ge=1)
):
    """Search movies by minimum rating."""

    try:
        movies = storage.query_movies(columns, min_rating, limit)

    except ValueError as error:
        logger.warning(f"Movie search failed: {error}")
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    logger.info(
        f"Queried movies: columns={columns}, "
        f"min_rating={min_rating}, returned_rows={len(movies)}"
    )

    return movies

@app.post("/movies/process", response_model=MovieProcessingReport)
def process_movies(config: ProcessConfig):
    """Validate and process the stored movies."""

    df = storage.get()

    if df.empty:
        logger.warning("No movies available for processing")
        raise HTTPException(
            status_code=400,
            detail="No movies available for processing"
        )

    config_dict = config.model_dump()

    try:
        validation = config_dict["validation"]

        for column in validation["numeric_columns"]:
            if column not in df.columns:
                raise ValueError(f"Missing numeric column: {column}")

        validated_df = validate_dataframe(
            df,
            validation["required_columns"],
            validation["numeric_columns"]
        )

        rows_removed = len(df) - len(validated_df)

        before_processing = validated_df.copy()

        processed_df = process_data(validated_df, config_dict)

        cleaning_report = create_cleaning_report(before_processing, processed_df)

    except ValueError as error:
        logger.warning(f"Processing failed: {error}")
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    storage.save(processed_df)

    logger.info(
        f"Processed movies: "
        f"validation_removed={rows_removed}, "
        f"rows_before={cleaning_report['rows_before']}, "
        f"rows_after={cleaning_report['rows_after']}"
    )

    return {
        "validation_rows_removed": rows_removed,
        "cleaning_report": cleaning_report
    }

