-- Migration rollback (down) file for sca_database_v0.2.0.sql
-- Naming for this file will follow the naming for its corresponding UP file

BEGIN;

DROP INDEX idx_offerings_course;
DROP INDEX idx_offerings_session;
DROP INDEX idx_reviews_student;
DROP INDEX idx_reviews_school;
DROP INDEX idx_review_replies_review;
DROP INDEX idx_review_votes_review;
DROP INDEX idx_registrations_student;

DROP TABLE IF EXISTS Attendance;

DROP TABLE IF EXISTS Scraped_information;

DROP TABLE IF EXISTS Event_responses;

DROP TABLE IF EXISTS Registrations;

DROP TABLE IF EXISTS Memberships;

DROP TABLE IF EXISTS Groups;

DROP TABLE IF EXISTS Notifications;

DROP TRIGGER trg_delete_auth_docs ON Authentications;

DROP FUNCTION delete_auth_documents;

DROP TABLE IF EXISTS Authentications;

DROP TABLE IF EXISTS Reviews_resources;

DROP TABLE IF EXISTS Dining_items;

DROP TABLE IF EXISTS Reviews_dining;

DROP TABLE IF EXISTS Reviews_educational;

DROP TABLE IF EXISTS Review_replies;

DROP TRIGGER trg_update_review_votes ON Review_votes;

DROP FUNCTION update_review_votes;

DROP TABLE IF EXISTS Review_votes;

DROP TABLE IF EXISTS Reviews_generic;

DROP TABLE IF EXISTS Instructors;

DROP TABLE IF EXISTS Deadlines;

DROP TABLE IF EXISTS Students;

DROP TABLE IF EXISTS Offerings;

DROP TABLE IF EXISTS Sessions;

DROP TABLE IF EXISTS Courses;

DROP TABLE IF EXISTS Dining;

DROP TABLE IF EXISTS Events;

DROP TABLE IF EXISTS Locations;

DROP TABLE IF EXISTS Departments;

DROP TABLE IF EXISTS Users;

DROP TABLE IF EXISTS Schools;

DROP EXTENSION vector;

COMMIT;