import os
import csv
from pathlib import Path
from dotenv import load_dotenv

import psycopg
from psycopg import sql

from generate_sql_schema import SchemaGenerator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILE = PROJECT_ROOT / "schema.sql"
CSV_DIRECTORY = PROJECT_ROOT / "data" / "1-lh_nautical_csv"

STAGING_TABLE = "_csv_loader_staging"
ROW_NUMBER_COLUMN = "_csv_loader_row_number"


def read_csv_header(csv_path):
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)

        try:
            return next(reader)
        except StopIteration as error:
            raise ValueError("Arquivo CSV vazio ou sem cabeçalho.") from error


def get_table_columns(cursor, table_name):
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table_name,),
    )
    return [row[0] for row in cursor.fetchall()]


def copy_csv(cursor, csv_path, table_name, columns, chunk_size):
    copy_statement = sql.SQL(
        "COPY {} ({}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"
    ).format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
    )

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        with cursor.copy(copy_statement) as copy:
            while chunk := csv_file.read(chunk_size):
                copy.write(chunk)


def validate_existing_prefix(cursor, table_name, columns, existing_count):
    column_list = sql.SQL(", ").join(map(sql.Identifier, columns))
    query = sql.SQL(
        """
        SELECT EXISTS (
            SELECT 1
            FROM (
                (
                    SELECT {columns} FROM {table}
                    EXCEPT ALL
                    SELECT {columns} FROM {staging}
                    WHERE {row_number} <= %s
                )
                UNION ALL
                (
                    SELECT {columns} FROM {staging}
                    WHERE {row_number} <= %s
                    EXCEPT ALL
                    SELECT {columns} FROM {table}
                )
            ) AS differences
        )
        """
    ).format(
        columns=column_list,
        table=sql.Identifier(table_name),
        staging=sql.Identifier(STAGING_TABLE),
        row_number=sql.Identifier(ROW_NUMBER_COLUMN),
    )
    cursor.execute(query, (existing_count, existing_count))
    return not cursor.fetchone()[0]


def load_csv(connection, csv_path, chunk_size):
    table_name = csv_path.stem
    columns = read_csv_header(csv_path)

    with connection.cursor() as cursor:
        table_columns = get_table_columns(cursor, table_name)

        if not table_columns:
            raise ValueError(
                f'Tabela "{table_name}" inexistente no schema ativo.'
            )

        if columns != table_columns:
            raise ValueError(
                "Cabeçalho incompatível com a tabela. "
                f"CSV: {columns}. Tabela: {table_columns}."
            )

        cursor.execute(
            sql.SQL("LOCK TABLE {} IN EXCLUSIVE MODE").format(
                sql.Identifier(table_name)
            )
        )
        cursor.execute(
            sql.SQL("SELECT COUNT(*) FROM {}").format(
                sql.Identifier(table_name)
            )
        )
        existing_count = cursor.fetchone()[0]

        if existing_count == 0:
            copy_csv(
                cursor,
                csv_path,
                table_name,
                columns,
                chunk_size,
            )
            return

        cursor.execute(
            sql.SQL(
                "CREATE TEMP TABLE {} (LIKE {}) ON COMMIT DROP"
            ).format(
                sql.Identifier(STAGING_TABLE),
                sql.Identifier(table_name),
            )
        )
        cursor.execute(
            sql.SQL("ALTER TABLE {} ADD COLUMN {} BIGSERIAL").format(
                sql.Identifier(STAGING_TABLE),
                sql.Identifier(ROW_NUMBER_COLUMN),
            )
        )

        copy_csv(
            cursor,
            csv_path,
            STAGING_TABLE,
            columns,
            chunk_size,
        )
        cursor.execute(
            sql.SQL("SELECT COUNT(*) FROM {}").format(
                sql.Identifier(STAGING_TABLE)
            )
        )
        csv_count = cursor.fetchone()[0]

        if existing_count > csv_count:
            raise ValueError(
                f"A tabela possui {existing_count} registros, mas o CSV "
                f"possui apenas {csv_count}."
            )

        if not validate_existing_prefix(
            cursor,
            table_name,
            columns,
            existing_count,
        ):
            raise ValueError(
                "Os registros existentes não correspondem ao início do CSV."
            )

        column_list = sql.SQL(", ").join(map(sql.Identifier, columns))
        cursor.execute(
            sql.SQL(
                """
                INSERT INTO {table} ({columns})
                SELECT {columns}
                FROM {staging}
                WHERE {row_number} > %s
                ORDER BY {row_number}
                """
            ).format(
                table=sql.Identifier(table_name),
                columns=column_list,
                staging=sql.Identifier(STAGING_TABLE),
                row_number=sql.Identifier(ROW_NUMBER_COLUMN),
            ),
            (existing_count,),
        )


def ensure_schema():
    if not SCHEMA_FILE.exists():
        SchemaGenerator().generate_schema(
            CSV_DIRECTORY,
            SCHEMA_FILE,
        )


def find_csv_files(csv_directory):
    if not csv_directory.is_dir():
        raise ValueError(
            f"Diretório de dados inexistente: {csv_directory}"
        )

    csv_files = sorted(
        path
        for path in csv_directory.iterdir()
        if path.is_file() and path.suffix.lower() == ".csv"
    )

    if not csv_files:
        raise ValueError(
            f"Nenhum arquivo CSV encontrado em: {csv_directory}"
        )

    return csv_files


def main():
    ensure_schema()

    csv_files = find_csv_files(CSV_DIRECTORY)
    copy_chunk_size = 1024 * 1024

    load_dotenv(PROJECT_ROOT / ".env")

    DATABASE_CONFIG = {
        "dbname": os.environ["POSTGRES_DB"],
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
        "host": os.environ["POSTGRES_HOST"],
        "port": os.environ["POSTGRES_PORT"],
    }

    with psycopg.connect(**DATABASE_CONFIG) as connection:
        connection.execute(
            SCHEMA_FILE.read_text(encoding="utf-8")
        )
        connection.commit()

        for csv_path in csv_files:
            table_name = csv_path.stem

            try:
                load_csv(
                    connection,
                    csv_path,
                    copy_chunk_size,
                )
                connection.commit()
                print(
                    f'CSV "{csv_path.name}" carregado na tabela "{table_name}".')
            except Exception as error:
                connection.rollback()
                raise RuntimeError(
                    f'Falha ao processar o CSV "{csv_path}" para a tabela '
                    f'"{table_name}": {error}'
                ) from error


if __name__ == "__main__":
    main()
