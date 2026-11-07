import logging
import pandas as pd
logger = logging.getLogger(__name__)

def validate_dataframe(df, required_columns, numeric_columns):
    """Validate the DataFrame and return valid data.

    required_columns: a list of column names that must exist.
    numeric_columns: a list of column names whose values should be
    numeric."""

    before = len(df)

    for col in numeric_columns:
        if col not in df.columns:
            logger.error(f"Required column missing: {col}")
            raise ValueError(f"Required column missing: {col}")

    for col in numeric_columns:
        invalid_rows = []
        
        for i, value in df[col].items():
            if pd.notna(value):
                try:
                    float(value)
                except ValueError:
                    logger.warning(f"Invalid numeric value in {col}, row{i}: {value}")
                    invalid_rows.append(i)

        df = df.drop(invalid_rows)
        df[col] = pd.to_numeric(df[col])

    logger.debug(
        f"Validation: {len(df)} valid rows, "
        f"{before - len(df)} rows removed")
    
    return df