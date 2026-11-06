BEGIN;

ALTER TABLE Schools
    ADD COLUMN scorecard_id INTEGER UNIQUE;


-- preserve student verification status if they self-deactivate accounnt
ALTER TABLE Users
    ADD COLUMN self_deactivated BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE Authentications
    ADD COLUMN method TEXT NOT NULL DEFAULT 'manual',
    ADD COLUMN reason TEXT;

-- until cloud delployment: private, small auth doc uploads stored in postgres db
CREATE TABLE Authentication_documents (
    authentication_id INTEGER PRIMARY KEY REFERENCES Authentications(authentication_id) ON DELETE CASCADE,
    content BYTEA NOT NULL CHECK (octet_length(content) <= 5242880)
);

CREATE TABLE Enrollment_otps (
    student_id INTEGER PRIMARY KEY REFERENCES Students(student_id) ON DELETE CASCADE,
    email TEXT NOT NULL CHECK (email ~ '^[a-z0-9._%+-]+@[a-z0-9.-]+\.edu$'),
    code_hash TEXT NOT NULL,
    failures INTEGER NOT NULL DEFAULT 0 CHECK (failures BETWEEN 0 AND 3),
    expires_at TIMESTAMPTZ NOT NULL,
    last_sent TIMESTAMPTZ NOT NULL,
    consumed BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE Captcha_challenges (
    signature TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);


COMMIT;