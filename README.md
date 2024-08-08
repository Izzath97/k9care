
# Apache Airflow with PostgreSQL

This repository contains the Docker Compose setup for running Apache Airflow and PostgreSQL with python.

## Prerequisites

- Docker
- Docker Compose

## Setup

### Environment Variables

Create a `.env` file in the root directory of the project with the following content:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_PASSWORD
POSTGRES_DB=k9care_db

# Backend DB - update your username and password
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://YOUR_USERNAME:YOUR_PASSWORD@postgres/YOUR_DATABASE
AIRFLOW__DATABASE__LOAD_DEFAULT_CONNECTIONS=False

# Airflow Init
_AIRFLOW_DB_MIGRATE=True
_AIRFLOW_WWW_USER_CREATE=True
_AIRFLOW_WWW_USER_USERNAME=postgres
_AIRFLOW_WWW_USER_PASSWORD=YOUR_PASSWORD
```

### Initialization SQL

Create an `init.sql` file in the root directory of the project with the following content:

```sql

\c k9care_db;

CREATE TABLE facts (
    id SERIAL PRIMARY KEY,
    fact TEXT NOT NULL,
    contains_numbers BOOLEAN NOT NULL,
    category TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_fact UNIQUE (fact)
);
```

### Directory Structure

Your directory structure should look like this:

```
.
├── dags
├── logs
├── plugins
├── .env
├── init.sql
├── Dockerfile
└── docker-compose.yml
```

### Docker Compose File

Here is the `docker-compose.yml` file:

```yaml
version: '3.8'

x-common: &common
  image: apache/airflow:2.9.3
  user: "${AIRFLOW_UID}:0"
  env_file: 
    - .env
  volumes:
    - ./dags:/opt/airflow/dags
    - ./logs:/opt/airflow/logs
    - ./plugins:/opt/airflow/plugins
    - /var/run/docker.sock:/var/run/docker.sock

x-depends-on: &depends-on
  depends_on:
    postgres:
      condition: service_healthy
    airflow-init:
      condition: service_completed_successfully

services:
  postgres:
    image: postgres:13
    container_name: postgres
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
      retries: 5
      start_period: 10s
    env_file:
      - .env
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-airflow}
      POSTGRES_USER: ${POSTGRES_USER:-airflow}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-airflow}
      POSTGRES_PORT: ${POSTGRES_PORT:-5432}
    volumes:
      - local_postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  scheduler:
    <<: [*common, *depends-on]
    container_name: airflow-scheduler
    command: scheduler
    restart: on-failure

  webserver:
    <<: [*common, *depends-on]
    container_name: airflow-webserver
    restart: always
    command: webserver
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 30s
      timeout: 30s
      retries: 5

  airflow-init:
    <<: *common
    container_name: airflow-init
    entrypoint: /bin/bash
    command:
      - -c
      - |
        mkdir -p /opt/airflow/logs /opt/airflow/dags /opt/airflow/plugins
        chown -R "${AIRFLOW_UID}:0" /opt/airflow/{logs,dags,plugins} # Ensure ownership
        exec /entrypoint airflow version

volumes:
  local_postgres_data:
```

### Creating PostgreSQL User and Database

To set up the PostgreSQL user and database, follow these steps:

1. Access the PostgreSQL container:
   ```bash
   docker exec -it postgres psql -U postgres
   ```

2. Create the Airflow user and database:
   ```sql
   CREATE USER airflow WITH PASSWORD 'airflow';
   CREATE DATABASE airflow;
   GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
   ```

3. Verify the user and database creation:
   ```sql
   \du
   \l
   ```

4. Exit the PostgreSQL prompt:
   Type `\q` to exit.

### Running the Services

To start the services, run the following command:

```bash
docker-compose up -d
```

### Stopping the Services

To stop the services, run the following command:

```bash
docker-compose down
```

### Accessing the Web Interface

The Airflow web interface will be available at [http://localhost:8080](http://localhost:8080).

### Logs

Logs for the Airflow services can be found in the `logs` directory.

## Test Results

All tests have successfully passed. Below are the results from running `pytest`:

test_clean_text.py . [ 16%]
test_filter_data.py . [ 33%]
test_main_pipeline.py . [ 50%]
test_pull_data.py .. [ 83%]
test_save_data.py . [100%]

===================================================================================== 6 passed in 0.32s ======================================================================================

## Code Quality

The project has achieved a perfect pylint score of `10/10`. This indicates that the code follows best practices and maintains a high level of quality.

### Troubleshooting

If you encounter any issues, you can check the logs for the individual services:

```bash
docker-compose logs -f
```

### Made by

This project is made by Mohamed Izzath
