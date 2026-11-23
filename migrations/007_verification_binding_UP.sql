BEGIN;

ALTER TABLE Enrollment_otps
    ADD COLUMN school_id INTEGER REFERENCES Schools(school_id),
    ADD COLUMN challenge_id UUID,
    ADD COLUMN locked_until TIMESTAMPTZ;

UPDATE Enrollment_otps
SET consumed = TRUE,
    failures = 0;

ALTER TABLE Studid_verifications
    ADD COLUMN school_id INTEGER REFERENCES Schools(school_id);

DELETE FROM Studid_verifications;

CREATE TABLE Student_sso_evidence (
    student_id INTEGER PRIMARY KEY
        REFERENCES Students(student_id) ON DELETE CASCADE,
    school_id INTEGER NOT NULL
        REFERENCES Schools(school_id),
    entity_id TEXT NOT NULL,
    identifier TEXT,
    affiliations TEXT[] NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);

COMMIT;