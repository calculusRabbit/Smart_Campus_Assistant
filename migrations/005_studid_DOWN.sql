BEGIN;

DROP TABLE Studid_verifications;

DROP INDEX uq_students_studid_identity;

ALTER TABLE Students
    DROP COLUMN studid_identifier,
    DROP COLUMN studid_entity_id;

COMMIT;