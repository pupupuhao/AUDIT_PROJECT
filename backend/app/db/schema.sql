CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(50) UNIQUE,
    law_name VARCHAR(255),
    clause_label VARCHAR(100),
    full_title TEXT,
    content TEXT NOT NULL,
    category VARCHAR(50),
    keywords JSONB DEFAULT '[]'::jsonb,
    logic_rules JSONB DEFAULT '{}'::jsonb,
    required_fields JSONB DEFAULT '[]'::jsonb,
    embedding VECTOR(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_data (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255),
    raw_data JSONB,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_results (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES project_data(id),
    rule_id VARCHAR(50),
    compliance BOOLEAN,
    audit_opinion TEXT,
    evidence TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_knowledge_base_category
    ON knowledge_base(category);

CREATE INDEX IF NOT EXISTS idx_project_data_upload_time
    ON project_data(upload_time DESC);

CREATE INDEX IF NOT EXISTS idx_audit_results_project_id
    ON audit_results(project_id);
