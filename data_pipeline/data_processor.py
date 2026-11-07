import logging
import pandas as pd

logger = logging.getLogger(__name__)

def remove_duplicates(df):
    """Remove duplicate rows."""
    before = len(df)
    df = df.drop_duplicates()

    rows_removed = before - len(df)
    logger.debug(f"Removed {rows_removed} duplicate rows")

    return df

def handle_missing(df, axis="rows"):
    """Drop rows or columns containing missing values."""
    if axis == "rows":
        before = len(df)
        df = df.dropna(axis=0)
        removed = before - len(df)
        logger.debug(f"Removed {removed} rows with missing values")

    elif axis == "columns":
        before = len(df.columns)
        df = df.dropna(axis=1)
        removed = before - len(df.columns)
        logger.debug(f"Removed {removed} columns with missing values")

    else:
        logger.error(f"Unsupported axis: {axis}")
        raise ValueError(f"Unsupported axis: {axis}")

    return df

def remove_outliers(df, columns, method, threshold):
    """Remove outliers from the specified numeric columns."""
    if method not in ["iqr", "zscore"]:
        logger.error(f"Unsupported outlier method: {method}")
        raise ValueError(f"Unsupported outlier method: {method}")

    for column in columns:
        if column not in df.columns:
            logger.warning(f"Column not found: {column}")
            continue

        if not pd.api.types.is_numeric_dtype(df[column]):
            logger.warning(f"Column is not numeric: {column}")
            continue

        if method == "iqr":

            before = len(df)

            q1 = df[column].quantile(0.25)
            q3 = df[column].quantile(0.75)
            iqr = q3 - q1

            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr

            df = df[(df[column] >= lower) & (df[column] <= upper)]

            logger.debug(
                f"{column}: method = {method}, threshold = {threshold}, "
                f"removed = {before - len(df)} rows"
            )

        elif method == "zscore":
            before = len(df)
            mean = df[column].mean()
            std = df[column].std()

            if std == 0:
                logger.debug(f"{column}: method = {method}, threshold = {threshold}, "
                    "removed = 0 rows: standard deviation is zero"
                )
                continue

            z_scores = (df[column] - mean) / std
            df = df[z_scores.abs() <= threshold]

            logger.debug(
                f"{column}: method = {method}, threshold = {threshold}, "
                f"removed = {before - len(df)} rows"
            )

    return df

def process_data(df, config):
    """Apply the processing steps enabled in the configuration."""
    processing = config["processing"]

    if processing["remove_duplicates"]:
        df = remove_duplicates(df)

    if processing["missing"]["enabled"]:
        df = handle_missing(df, axis = processing["missing"]["axis"])

    if processing["outliers"]["enabled"]:
        df = remove_outliers(
            df,
            columns = processing["outliers"]["columns"],
            method = processing["outliers"]["method"],
            threshold = processing["outliers"]["threshold"]
        )

    return df

def create_cleaning_report(df_before, df_after):
    """Return a dictionary summarizing the cleaning results."""
    return{
        "rows_before" : len(df_before),
        "rows_after" : len(df_after),
        "rows_removed" : len(df_before) -  len(df_after),
        "columns_before" : len(df_before.columns),
        "columns_after" : len(df_after.columns),
        "columns_removed" : len(df_before.columns) - len(df_after.columns)
    }
