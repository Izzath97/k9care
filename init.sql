\c k9care_db;

CREATE TABLE facts (
    id SERIAL PRIMARY KEY,
    fact TEXT NOT NULL,
    category TEXT NOT NULL,
    version INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW());