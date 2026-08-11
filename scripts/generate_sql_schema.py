import csv
import os
from datetime import datetime
from pathlib import Path


class SchemaGenerator:
    def __init__(self):
        pass

    def generate_schema(
        self,
        csv_directory,
        output_file="schema.sql"
    ):
        statements = []

        for file_name in sorted(os.listdir(csv_directory)):
            if not file_name.lower().endswith(".csv"):
                continue

            file_path = os.path.join(
                csv_directory,
                file_name
            )

            if not os.path.isfile(file_path):
                continue

            create_table = self.__generate_create_table(file_path)

            statements.append(create_table)

        if not statements:
            raise ValueError(
                f"Nenhum arquivo CSV encontrado em: {csv_directory}"
            )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as file:
            file.write("\n\n".join(statements))
            file.write("\n")

    def __detect_type(self, value):
        value = value.strip()

        if not value:
            return None

        if value.lower() in ("true", "false"):
            return "BOOLEAN"

        try:
            if "-" not in value:
                raise ValueError
            datetime.fromisoformat(value)
            return "TIMESTAMP"
        except ValueError:
            pass

        if (
            value.startswith("0")
            and len(value) > 1
            and "." not in value
        ):
            return "TEXT"

        try:
            integer_value = int(value)

            INTEGER_MIN = -(2 ** 31)
            INTEGER_MAX = (2 ** 31) - 1
            BIGINT_MIN = -(2 ** 63)
            BIGINT_MAX = (2 ** 63) - 1

            if INTEGER_MIN <= integer_value <= INTEGER_MAX:
                return "INTEGER"

            if BIGINT_MIN <= integer_value <= BIGINT_MAX:
                return "BIGINT"

            return "NUMERIC"
        except ValueError:
            pass

        try:
            float(value)
            return "NUMERIC"
        except ValueError:
            pass

        return "TEXT"

    def __infer_columns(self, file_path):
        text_columns = {
            "cpf"
        }

        numeric_priority = {
            "INTEGER": 1,
            "BIGINT": 2,
            "NUMERIC": 3,
        }

        with open(
            file_path,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:
            reader = csv.DictReader(file)

            headers = reader.fieldnames

            if not headers:
                raise ValueError(
                    f"Arquivo sem cabeçalho: {file_path}"
                )

            column_types = {
                header: None
                for header in headers
            }

            for row in reader:
                for header in headers:
                    if header.lower() in text_columns:
                        column_types[header] = "TEXT"
                        continue

                    row_value = row.get(header)

                    if row_value is None or not row_value.strip():
                        continue

                    detected_type = self.__detect_type(row_value)
                    current_type = column_types[header]

                    if current_type is None:
                        column_types[header] = detected_type
                        continue

                    if current_type == detected_type:
                        continue

                    if current_type == "TEXT":
                        continue

                    if detected_type == "TEXT":
                        column_types[header] = "TEXT"
                        continue

                    if (
                        current_type in numeric_priority.keys()
                        and detected_type in numeric_priority.keys()
                    ):
                        if (
                            numeric_priority[detected_type]
                            > numeric_priority[current_type]
                        ):
                            column_types[header] = detected_type
                        continue

                    column_types[header] = "TEXT"

            for header in headers:
                if column_types[header] is None:
                    column_types[header] = "TEXT"

            return headers, column_types

    def __generate_create_table(self, file_path):
        headers, column_types = self.__infer_columns(file_path)

        file_name = os.path.basename(file_path)
        table_name = os.path.splitext(file_name)[0]

        column_definitions = [
            f'    "{header}" {column_types[header]}'
            for header in headers
        ]

        return (
            f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n'
            + ",\n".join(column_definitions)
            + "\n);"
        )


def main():
    project_root = Path(__file__).resolve().parent.parent
    csv_directory = project_root / "data" / "1-lh_nautical_csv"
    output_file = project_root / "schema.sql"

    SchemaGenerator().generate_schema(csv_directory, output_file)
    print(f"Schema gerado em: {output_file}")


if __name__ == "__main__":
    main()
