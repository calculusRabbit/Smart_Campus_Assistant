BEGIN;

CREATE TABLE IF NOT EXISTS Auth_sessions (
    session_id UUID PRIMARY KEY,
    username TEXT NOT NULL REFERENCES Users(username)
        ON UPDATE CASCADE ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    CHECK (expires_at > created_at)
);

CREATE INDEX idx_auth_sessions_username ON Auth_sessions(username);

-- fails if existing rows contain collisions (intended)
-- email is case-insensitive
CREATE UNIQUE INDEX uq_students_email ON Students(lower(email));


COMMIT;