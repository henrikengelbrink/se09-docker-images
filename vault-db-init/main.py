import http.client
import mimetypes
import json
import os
import psycopg2
import time

import kubernetes.client
from kubernetes import client, config

db_host = os.environ['POSTGRES_HOST']
db_port = os.environ['POSTGRES_PORT']
db_user = os.environ['POSTGRES_USER']
db_password = os.environ['POSTGRES_PASSWORD']
db_name = os.environ['POSTGRES_DB_NAME']

# Create Vault schema in Postgres
postgres_connection = psycopg2.connect(host=db_host, port=db_port, user=db_user, password=db_password, dbname=db_name)
cursor = postgres_connection.cursor()
cursor.execute("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename  = 'vault_kv_store');")
exist_response = cursor.fetchall()

if exist_response[0][0] != True:
  print("Create vault table in postgres")
  sql_file = open('schema.sql','r')
  cursor.execute(sql_file.read())
  postgres_connection.commit()
  cursor.close()
else:
  print("Vault table already created")
