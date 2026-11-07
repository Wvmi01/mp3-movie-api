import logging

logger = logging.getLogger(__name__)


class DatasetStorage:
    def __init__(self):
        self._store = {}
        self._counter = 0

    def save(self, df, filename):
        """Store a copy of the data and return a new integer ID."""
        self._counter += 1
        dataset_id = self._counter

        self._store[dataset_id] = {
            "filename": filename,
            "df": df.copy()
        }

        logger.debug(f"Stored dataset: id={dataset_id}, rows={len(df)}")

        return dataset_id

    def get(self, dataset_id):
        """Return a copy of the stored DataFrame, or None."""
        dataset = self._store.get(dataset_id)

        if dataset is None:
            logger.debug(f"Dataset not found: id={dataset_id}")
            return None

        df = dataset["df"].copy()

        logger.debug(f"Retrieved dataset copy: id={dataset_id}, rows={len(df)}")

        return df

    def get_metadata(self, dataset_id):
        """Return the dataset metadata, or None."""
        dataset = self._store.get(dataset_id)

        if dataset is None:
            return None

        df = dataset["df"]

        return {
            "id": dataset_id,
            "filename": dataset["filename"],
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist()
        }

    def update(self, dataset_id, df):
        """Replace an existing dataset; return True, or False if missing."""
        if dataset_id not in self._store:
            return False

        self._store[dataset_id]["df"] = df.copy()

        logger.debug(f"Updated dataset: id={dataset_id}, rows={len(df)}")

        return True

    def clear(self):
        """Clear all data and reset the ID counter."""
        self._store.clear()
        self._counter = 0