import csv
import os
from datetime import datetime


class SchemaGenerator:

    TYPE_PRIORITY = {
        "BOOLEAN": 1,
        "INTEGER": 2,
        "NUMERIC": 3,
        "TIMESTAMP": 4,
        "TEXT": 5
    }

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
            int(value)
            return "INTEGER"
        except ValueError:
            pass

        try:
            float(value)
            return "NUMERIC"
        except ValueError:
            pass

        return "TEXT"

    def __infer_columns(self, file_path):
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
                    value = row.get(header)

                    if value is None or not value.strip():
                        continue

                    detected_type = self.__detect_type(value)
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

                    if {
                        current_type,
                        detected_type
                    } <= {"INTEGER", "NUMERIC"}:
                        column_types[header] = "NUMERIC"
                        continue

                    if (
                        self.TYPE_PRIORITY[detected_type]
                        > self.TYPE_PRIORITY[current_type]
                    ):
                        column_types[header] = detected_type

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
            f'CREATE TABLE "{table_name}" (\n'
            + ",\n".join(column_definitions)
            + "\n);"
        )


schema_generator = SchemaGenerator()
schema_generator.generate_schema("Caminho/diretorio_csv")
