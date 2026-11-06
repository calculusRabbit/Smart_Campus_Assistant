BEGIN;
ALTER TABLE Enrolments ADD COLUMN degree_level TEXT CHECK (length(trim(degree_level)) BETWEEN 1 AND 100);
COMMIT;
