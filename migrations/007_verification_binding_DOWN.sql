BEGIN;

DROP TABLE Student_sso_evidence;

DELETE FROM Studid_verifications;

ALTER TABLE Studid_verifications
    DROP COLUMN school_id;

UPDATE Enrollment_otps
SET consumed = TRUE;

ALTER TABLE Enrollment_otps
    DROP COLUMN locked_until,
    DROP COLUMN challenge_id,
    DROP COLUMN school_id;

COMMIT;