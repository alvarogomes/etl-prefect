from prefect import task, flow
from prefect.blocks.system import Secret
from sqlalchemy import (
    create_engine, MetaData, Table, Column, DateTime, String, Integer, Numeric,
    SMALLINT, Text
)
from sqlalchemy.dialects.postgresql import BYTEA

import hashlib
import json
from datetime import datetime


@task(name="Extract Task", description="Makes request.")
def extract():
    # source_db_url = "mysql+pymysql://root:rootpassword@localhost:3306/source_db"
    source_db_url = Secret.load("SOURCE_DB_URL").get()
    source_engine = create_engine(source_db_url)
    tables_query = "SHOW TABLES;"
    tables = source_engine.execute(tables_query).fetchall()

    data = {}
    metadata = MetaData()
    for table in tables:
        table_name = table[0]
        if table_name.startswith("mysql_"):  # Skip system tables
            continue
        table_ref = Table(table_name, metadata, autoload_with=source_engine)
        data[table_name] = {
            "schema": table_ref,
            "data": source_engine.execute(f"SELECT * FROM {table_name}").fetchall()
        }

    return data


@task(name="Transform Task", description="Transform MySQL schema to Postgres schema")
def transform(data):
    for table, table_data in data.items():
        schema = table_data['schema']
        
        # Transform the schema columns from MySQL specific types to Postgres compatible types
        for column in schema.columns:
            column_type_str = str(column.type).upper()

            if 'BINARY' in column_type_str:
                column.type = BYTEA()

        # Store the transformed schema back into the data dictionary
        data[table]['schema'] = schema

    return data


@task(name="Load Task", description="Persists data to disk.")
def load(data):
    # target_db_url = "postgresql://target_user:mysecretpassword@localhost:5432/target_db"
    target_db_url = Secret.load("TARGET_DB_URL").get()
    target_engine = create_engine(target_db_url)
    target_metadata = MetaData()

    # Create etl_history_log table if it does not exist
    etl_history = Table('etl_history_log', target_metadata,
                        Column('table_name', String),
                        Column('etl_date', DateTime),
                        Column('last_id', Integer),
                        Column('last_md5', String))
    target_metadata.create_all(target_engine, [etl_history])

    for table, table_data in data.items():
        schema = table_data['schema']
        records = table_data['data']

        # Check last loaded id from etl_history_log
        query = etl_history.select().where(etl_history.c.table_name == table)
        last_record = target_engine.execute(query).fetchone()
        last_id = last_record.last_id if last_record else 0

        # Filter new records based on id
        new_records = [r for r in records if r.id > last_id]

        if not new_records:
            continue

        # Create table if not exists
        schema.to_metadata(target_metadata)
        target_metadata.create_all(target_engine, [schema])

        # Insert new data into the table
        target_engine.execute(schema.insert(), new_records)

        # Update etl_history_log
        last_record = new_records[-1]
        last_id = last_record.id
        md5 = hashlib.md5(json.dumps(dict(last_record),
                          sort_keys=True).encode()).hexdigest()

        if last_record:
            update_values = {
                'etl_date': datetime.now(),
                'last_id': last_id,
                'last_md5': md5
            }

            if last_record:
                target_engine.execute(
                    etl_history.update().where(etl_history.c.table_name == table).values(update_values))
            else:
                update_values['table_name'] = table
                target_engine.execute(
                    etl_history.insert().values(update_values))


@flow(name="ETL Flow")
def etl_flow():
    extracted_data = extract()
    transformed_data = transform(extracted_data)
    load(transformed_data)


if __name__ == "__main__":
    etl_flow()
