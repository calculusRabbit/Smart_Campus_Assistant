BEGIN;

DROP TABLE Captcha_challenges;
DROP TABLE Enrollment_otps;
DROP TABLE Authentication_documents;

ALTER TABLE Authentications
    DROP COLUMN reason,
    DROP COLUMN method;

ALTER TABLE Users
    DROP COLUMN self_deactivated;

ALTER TABLE Schools
    DROP COLUMN scorecard_id;


COMMIT;