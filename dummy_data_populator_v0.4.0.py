# requires: psycopg, bcrypt
# populates existing postgres DB according to sca_database_v0.3.0.sql with dummy data

# run command: python <this_script_name> <DSN>
    #DSN format: postgresql://[user[:password]@][netloc][:port][/dbname][?param1=value1&...]


import argparse

#import os
import random
import sys
from datetime import datetime, timedelta, timezone

import bcrypt
import psycopg
from psycopg.types.json import Jsonb

#=================================Static Values=================================

#seed = random.Random(67) #not used for now, we want some randomness

# same password for all dummy accounts
dummy_password = "password123"
#only hashing once and using this result for efficiency
salt = bcrypt.gensalt()
password_hash = bcrypt.hashpw(dummy_password.encode("utf-8"), salt).decode("utf-8")

#script creates this many admin users and this many student users
user_count = 20

now = datetime.now(timezone.utc)

anon_username_fields = ["student","campus","uni","college","whistleblower","reviewer","critic"]

#==================================================================


#wipes any existing dummy data from all tables for a fresh re-population
def erase_data(cur):
    cur.execute("""
        TRUNCATE Schools, Users, Departments, Locations, Events, Dining, 
        Courses, Sessions, Enrolments, Offerings, Students, Deadlines, Instructors, 
        Reviews_generic, Review_votes, Review_replies, Reviews_educational, 
        Reviews_dining, Dining_items, Reviews_resources, Authentications, Notifications,
        Groups, Memberships, Registrations, Event_responses, Scraped_information, 
        Attendance
        RESTART IDENTITY CASCADE""")


# runs an insert operation and returns the serials created
def insert(cur, query, params):
    cur.execute(query, params)
    return cur.fetchone()[0]

#inserts dummy data into all tables
def insert_all(cur):
    
    school_ids = []
    for i in range(10):
        school_id = insert(cur, "INSERT INTO Schools (school_name) VALUES (%s) RETURNING school_id",
        (f"{random.choice(('University', 'College'))} of Test {i+1}",)
        )
        school_ids.append(school_id)


    department_ids = []
    i = 1
    for school_id in school_ids:
        dept_id = insert(cur, "INSERT INTO Departments (school_id, " 
        "department_name, department_code) "
        "VALUES (%s, %s, %s) RETURNING department_id", (school_id, 
        f"Test {random.choice(('Department', 'School'))} {i}", f"TEST{i}")
        )
        i+=1
        department_ids.append((dept_id, school_id))


    location_ids = []
    for school_id in school_ids:
        location_id = insert(cur, "INSERT INTO LOCATIONS (school_id, address_street, "
        "address_room, city, state_code, zipcode, on_campus, location_status, "
        "open_hours) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING location_id",
        (school_id, f"{random.randint(1,5000)} Test {random.choice(('St','Rd','Ln','Circle','Dr'))}",
        f"{random.choice(('room','Rm','suite'))} {random.randint(1,400)}", 
        f"Test City {random.randint(1,10)}", random.choice(("TX","KS","OK","CA","NY")), f"{random.randint(0, 99999):05d}", True, "active",
        Jsonb([{'days': [0,6], 'times': []}, {'days': [1,2,3,4,5], 'times': [['09:00', '17:00']]}]))
        )
        location_ids.append((location_id, school_id))
        #update locations for schools
        cur.execute("UPDATE Schools SET location_id = %s WHERE school_id = %s", (location_id, school_id))



    for i in range(user_count):
        insert(cur, "INSERT INTO Users (username, account_type, hashed_password) "
        "VALUES (%s,%s,%s) RETURNING username", (f"test_admin{i}","admin",password_hash))


    student_ids = []
    usernames_by_student = {}
    for i in range(user_count):
        username = f"test_student{i}"
        insert(cur,"INSERT INTO Users (username, account_type, hashed_password) VALUES "
        "(%s,%s,%s) RETURNING username", (username, "student", password_hash))
        
        student_id = insert(cur, "INSERT INTO Students (username, first_name, last_names, dob, "
        "email, edu_email, zipcode, account_status, created_at, interests) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING student_id", (username, 
        f"TestFirstName{i}", f"Test last Names{i}", datetime(random.randint(1970,2009),
        random.randint(1,12), random.randint(1,28), tzinfo=timezone.utc).date(),f"student_personal-email{i}@test.com",
        f"test_edu_email-{username}@test.edu", f"{random.randint(0, 99999):05d}", 
        random.choice(["pending", "open", "denied", "closed"]), 
        now - timedelta(days=i+random.randint(1,10)), random.choice((["coding", "software", "history"], ["research", 
        "geography", "music"], ["travelling", "art", "languages"]))))
        student_ids.append(student_id)
        usernames_by_student[student_id] = username



    session_ids = []
    for school_id in school_ids:
        session_id = insert(cur, "INSERT INTO Sessions (school_id, session_name, academic_year, "
        "session_start, session_end) VALUES (%s,%s,%s,%s,%s) RETURNING session_id",
        (school_id, "Fall 2026", 2026, "2026-08-17", "2026-12-03"))
        
        session_ids.append((session_id, school_id))


    
    course_ids = []
    for (dept_id, school_id) in department_ids:
        course_id = insert(cur, "INSERT INTO Courses (department_id, course_code, course_number, "
        "course_name, course_description, course_credits) "
        "VALUES (%s,%s,%s,%s,%s,%s) RETURNING course_id",
        (dept_id, "TEST", f"{random.randint(100,999)}{random.choice(('','AN','AQ','K'))}", f"Test Course from {dept_id}", "Test course description.", 3.0))
        course_ids.append((course_id, dept_id, school_id))

    
    session_by_school = {school_id: session_id for session_id, school_id in session_ids}
    location_by_school = {school_id: location_id for location_id, school_id in location_ids}
    students_by_school = {school_id: [] for school_id in school_ids}
    
    #to assign students to schools randomly 
    # but also preserve the order of students being added
    students_randomised = random.sample(student_ids, len(student_ids))

    enrolments = []
    for index, student_id in enumerate(students_randomised):
        #enrolled_school = random.choice(school_ids)
        enrolled_school = school_ids[index % len(school_ids)]
        students_by_school[enrolled_school].append(student_id) 
        
        session = session_by_school[enrolled_school]
        enrolment_id = insert(cur, """INSERT INTO Enrolments (student_id, school_id, 
                           majors, minors, is_primary, degree_seeking, first_semester)
                           VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING enrolment_id""",
                           (student_id, enrolled_school, random.choice((None, ["BS Computer Science"], 
                            ["BS Biology"], ["BA History","BEng Mechanical Eng"])), 
                           random.choice([None,["Math"],["Math", "CE"]]), random.choice((True,False)),True,
                           session))
        enrolments.append((enrolment_id, student_id, enrolled_school))

    
    school_by_student = {student_id: school_id for _, student_id, school_id in enrolments}

                
    
    instructor_ids = []
    for dept_id, school_id in department_ids:
        location_id = location_by_school[school_id]
        instructor_id = insert(cur, "INSERT INTO INSTRUCTORS (instructor_fname, "
        "instructor_lnames, instructor_department, instructor_email, instructor_office) "
        "VALUES(%s,%s,%s,%s,%s) RETURNING instructor_id", ("TestFname", "Test last name", dept_id,
        f"test.instructoremail_{dept_id}@testuniversity.edu", location_id))
        instructor_ids.append((instructor_id, dept_id, school_id))


    offering_ids = []
    for course_id, dept_id, school_id in course_ids:
        session_id = session_by_school[school_id]
        location_id = location_by_school[school_id]
        dept_instructors = []
        for instructor_id, department_id, _ in instructor_ids:
            if department_id == dept_id:
                dept_instructors.append(instructor_id)
        offering_id = insert(cur, "INSERT INTO Offerings (course_crn, course_id, location_id, " 
            "offering_session, class_timings, school_id, primary_instructor) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING offering_id",
            (f"{course_id+1234}",course_id, location_id, session_id, 
            Jsonb([{'days': [0,2], 'times': [['11:00','12:15']]}, {'days': [1,3,4,5,6], 'times': []}]), school_id,
            random.choice(dept_instructors)))
        offering_ids.append((offering_id, course_id, dept_id, school_id, session_id))


    dining_locations = []
    for (location_id, school_id) in location_ids:
        dining_id = insert(cur, "INSERT INTO DINING (dining_name, location_id, cuisine, "
        "reservations, event_status) VALUES (%s, %s, %s, %s, %s) RETURNING dining_id", 
        (f"test restaurant {location_id}", location_id, [random.choice(('indian','chinese','korean'))],
        random.choice((True,False)), random.choice((True,False))))
        dining_locations.append((dining_id, school_id, location_id))
    
    
    dining_items = []
    for dining_id, school_id, location_id in dining_locations:
        # pick a random student from the school for review item added by
        student = random.choice(students_by_school[school_id])
        for i in range(10):
            item_name = f"test food item {i}"
            item_id = insert(cur, "INSERT INTO Dining_items (dining_id, item_name, item_price, "
            "item_calories, item_ingredients, dietary_tags, entered_by) VALUES "
            "(%s,%s,%s,%s,%s,%s,%s) RETURNING item_id", (dining_id, item_name, round(random.uniform(1,25),2),
            random.randint(100,1200),["sugar","spice","everything nice"], [], usernames_by_student[student]))
            dining_items.append((dining_id, item_id, item_name))
        

    #one review per student
    reviews_generic = []
    review_times = {}
    for student_id in student_ids:
        school_id = school_by_student[student_id]
        review_time = now - timedelta(hours=random.randint(1,100))
        
        #splitting reviews into categories
        review_state = random.choice(("excellent", "very good", "good", "mediocre", "bad", "very bad"))
        match review_state:
            case "excellent":
                review_title = "Amazing quality!! :D"
                review_comment = "Excellent review!!! This is the best thing on Earth!!!"
                rating = 5.0
            case "very good":
                rating = 4.0
                review_title = "Great service! :)"
                review_comment = "Very good review! Great job!"
            case "good":
                rating = 3.5
                review_title = "Good support"
                review_comment = "Good review. This is pretty good value for money."
            case "mediocre":
                rating = 2.5
                review_title = "Was okay, but could be better :/"
                review_comment = "Mediocre review. Half good, half not so good."
            case "bad":
                rating = 1.5
                review_title = "Not great :("
                review_comment = "Bad review. Lots of things to improve"
            case "very bad":
                rating = 1.0
                review_title = "Horrible :<"
                review_comment = "Very bad review!! Everything sucks, y'all should go out of business"
        
        #anonymous reviews
        is_anonymous = random.choice([True, False])
        anonymous_username = None
        if is_anonymous:
            anonymous_username = f"{random.choice(anon_username_fields).title()}_{random.choice(anon_username_fields).title()}{random.randint(0,9)}{random.randint(0,9)}"
        
        review_id = insert(cur, "INSERT INTO Reviews_generic (student_id, school_id, rating, "
        "review_tags, review_title, review_comment, anonymous, anonymous_username, submitted) VALUES "
        "(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING review_id", (student_id, school_id, 
        rating, random.choice((["Helpful","Comprehensive","Most upvoted"],["Good resources"],[])), review_title, 
        review_comment, is_anonymous, anonymous_username, review_time))
        reviews_generic.append((review_id, student_id, school_id))
        review_times[review_id] = review_time


    for review_id, student_id, school_id in reviews_generic:
        if random.choice((True, False)) == True:
            random_student = random.choice(student_ids)
            #ensure voter is not the review author
            while random_student == student_id:
                random_student = random.choice(student_ids)
            insert(cur, "INSERT INTO Review_votes (review_id, voter_id, is_upvote, "
            "vote_time) VALUES (%s,%s,%s,%s) RETURNING review_id", 
            (review_id, random_student, random.choice((True, False)), review_times[review_id] + timedelta(minutes=random.randint(1, 7 * 24 * 60))))



    offerings_by_school = {school_id: [] for school_id in school_ids}
    #offerings_by_student = {student_id: [] for student_id in student_ids}
    dining_by_school = {school_id: [] for school_id in school_ids}
    items_by_dining = {}

    for offering_id, course_id, dept_id, school_id, session_id in offering_ids:
        offerings_by_school[school_id].append(
            (offering_id, course_id, dept_id, session_id)
        )

    for dining_id, school_id, location_id in dining_locations:
        dining_by_school[school_id].append(dining_id)
        items_by_dining[dining_id] = []

    for dining_id, item_id, item_name in dining_items:
        items_by_dining[dining_id].append(item_name)



    #TODO: insertions to remaining tables

    #Review_replies
    
    #Reviews_educational
    
    #Reviews_dining
    
    #Reviews_resources
    
    #Events
    
    #Event_responses
    
    #Deadlines
    
    #Authentications
    
    #Notifications
    
    #Groups
    
    #Memberships
    
    #Registrations
    
    #Attendance


def main():
    
    # if len(sys.argv) != 2:
    #     sys.exit("Please provide exactly one argument: the postgres DSN / connection string")
    # dsn = sys.argv[1]       
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True, help="DSN connection string to existing database")
    parser.add_argument("--reset",'-r', action="store_true", help="delete existing data in database?")
    parser.add_argument("--seed",'-s', type=int, default=67) #will be used if seed is used for RNG
    parser.add_argument("--num-users",'-n', type=int, default=20)
    args = parser.parse_args()


    if not args.reset:
        parser.error("the script currently needs --reset to run without error, to not have duplicate records that conflict since they're supposed to be unique.")

    # if args.reset:
    #     environment = os.environ.get("APP_ENV")
    #     if environment not in {"development", "test"}:
    #         raise RuntimeError(
    #             "Database won't be truncated unless APP_ENV is development or test"
    #         )
    global user_count
    if args.num_users < 2:
        parser.error("--num-users must be >=2 for valid review vote data to be populated")
    user_count = args.num_users
    
    try:
        with psycopg.connect(args.dsn) as conn, conn.cursor() as cur:
            if args.reset:
                erase_data(cur)
            
            insert_all(cur)
            print("Fresh dummy data inserted into database")
            conn.commit()

    except psycopg.errors.OperationalError as ex:
        sys.exit(f"Failed to connect to / write to database: {ex}")
    except psycopg.errors.UniqueViolation as ex:
        print(f"Failed to write to field due to unique constraint: {ex}")
    except psycopg.DatabaseError as ex:
        sys.exit(f"A stopping database failure ocurred: {ex}")


if __name__ == "__main__":
    main()
