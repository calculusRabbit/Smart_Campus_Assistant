-- Rollback Professor Appointment Requests (Prototype 3).
-- WARNING: Running this rollback deletes all appointment records.
-- Existing students and instructors are not affected.

DROP TABLE IF EXISTS appointments;
