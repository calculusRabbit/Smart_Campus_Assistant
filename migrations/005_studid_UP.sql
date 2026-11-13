BEGIN;

ALTER TABLE Students
    ADD COLUMN studid_entity_id TEXT,
    ADD COLUMN studid_identifier TEXT;

CREATE UNIQUE INDEX uq_students_studid_identity ON Students(studid_entity_id, studid_identifier)
    WHERE studid_identifier IS NOT NULL;

CREATE TABLE Studid_verifications (
    student_id INTEGER PRIMARY KEY REFERENCES Students(student_id) ON DELETE CASCADE,
    verification_id UUID NOT NULL UNIQUE,
    secret_token TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '1 hour')
);

COMMIT;