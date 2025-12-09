import logging
from typing import Dict
from google.cloud import bigquery


def insert_member_row(
    project_id: str,
    dataset_id: str,
    table_id: str,
    row: Dict,
) -> None:
    """
    Menulis 1 row ke BigQuery: project.dataset.table
    Raise exception kalau ada error.
    """

    client = bigquery.Client(project=project_id)
    table_fqdn = f"{project_id}.{dataset_id}.{table_id}"

    logging.info(f"Writing row to BigQuery table {table_fqdn}: {row}")

    errors = client.insert_rows_json(table_fqdn, [row])

    if errors:
        logging.error(f"BigQuery insert errors: {errors}")
        raise RuntimeError(f"BigQuery insert errors: {errors}")

    logging.info("Row successfully inserted into BigQuery.")
