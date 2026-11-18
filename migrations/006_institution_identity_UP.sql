BEGIN;

CREATE TABLE Institution_identity (
    school_id INTEGER PRIMARY KEY REFERENCES Schools(school_id) ON DELETE CASCADE,
    api_ninjas_id BIGINT UNIQUE,
    native_name TEXT,
    acronym TEXT,
    aliases TEXT[] NOT NULL DEFAULT '{}',
    email_domains TEXT[] NOT NULL DEFAULT '{}',
    student_only_domains TEXT[] NOT NULL DEFAULT '{}',
    idp_entity_ids TEXT[] NOT NULL DEFAULT '{}',
    source_updated_at TIMESTAMPTZ,
    CHECK (NOT (email_domains @> ARRAY['edu']::TEXT[]))
);

COMMIT;