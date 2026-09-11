# requires: psycopg, bcrypt
# populates (already-created) postgres database (according to schema in sca_database_v0.2.0.sql) with dummy data

# run command: python <this_script_name> <dsn>

import os
import sys
import psycopg
from psycopg.types.json import Jsonb
import random
from datetime import datetime, timedelta
import bcrypt

#seed = random.Random(67) #not used for now, we want some randomness

# same password for all dummy accounts
dummy_password = "password123"
#only hashing once and using this result for efficiency
salt = bcrypt.gensalt()
hash = bcrypt.hashpw(dummy_password.encode("utf-8"), salt).decode("utf-8")

#wipes any existing dummy data from all tables for a fresh re-population
def erase_data(cur):
    cur.execute("""
        TRUNCATE Schools, Users, Departments, Locations, Events, Dining, 
        Courses, Sessions, Offerings, Students, Deadlines, Instructors, 
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
        dept_id = insert(cur, "INSERT INTO Departments (school_id, department_name, department_code) "
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
        f"{random.choice(("room","Rm","suite"))} {random.randint(1,400)}", 
        f"Test City {random.randint(1,10)}", random.choice(("TX","KS","OK","CA","NY")), 10000+random.randint(89999), True, "active",
        Jsonb([{'days': [0,6], 'times': []}, {'days': [1,2,3,4,5], 'times': [['09:00', '17:00']]}]))
        )
        location_ids.append((location_id, school_id))
    
    for i in range(10):
        insert(cur, "INSERT INTO Users (username, account_type, hashed_password) "
        "VALUES (%s,%s,%s) RETURNING username", (f"test_admin{i}","admin",hash))
        insert(cur, "INSERT INTO Users (username, account_type, hashed_password) "
        "VALUES (%s,%s,%s) RETURNING username", (f"test_student{i}","student",hash))

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
        (dept_id, "TEST", f"{random.randint(100,900)}", "Test Course", "Test course description.", 3.0))
        course_ids.append((course_id, dept_id, school_id))

    
    session_by_school = {school_id: session_id for session_id, school_id in session_ids}
    location_by_school = {school_id: location_id for location_id, school_id in location_ids}
    session_id = session_by_school[school_id]
    location_id = location_by_school[school_id]
    insert(cur, "INSERT INTO Offerings (course_crn, course_id, location_id, " 
        "offering_session, class_timings) VALUES (%s, %s, %s, %s, %s) RETURNING offering_id",
        (f"{course_id+1234}",course_id, location_id, session_id, 
        Jsonb([{'days': [0,2], 'times': [['11:00','12:15']]}, {'days': [0,1,3,4,5,6,7], 'times': []}]))
        )
                
    
    instructor_ids = []
    for (dept_id, school_id) in department_ids:
         for (location_id2, school_id2) in location_ids:
            if school_id2 == school_id:
                location_id = location_id2
                break
    instructor_id = insert(cur, "INSERT INTO INSTRUCTORS (instructor_fname, "
    "instructor_lnames, instructor_department, instructor_email, instructor_office) "
    "VALUES(%s,%s,%s,%s,%s) RETURNING instructor_id", ("TestFname", f"Test last name", dept_id,
    f"test.instructoremail{dept_id}@testuniversity.edu", location_id))
    instructor_ids.append(instructor_id, dept_id, school_id)

    dining_ids = []
    for (location_id, school_id) in location_ids:
        dining_id = insert(cur, "INSERT INTO DINING (dining_name, location_id, cuisine, "
        "reservations, event_status) VALUES (%s, %s, %s, %s, %s) RETURNING dining_id", 
        (f"test restaurant {location_id}", location_id, [random.choice(('indian','chinese','korean'))],
        random.choice((True,False)), random.choice((True,False))))
        dining_ids.append(dining_id)
    
        
    dining_items = []
    for dining_id in dining_ids:
        for i in range(10):
            item_id = insert(cur, "INSERT INTO Dining_items (dining_id, item_name, item_price, "
            "item_calories, item_ingredients, dietary_tags, entered_by) VALUES "
            "(%s,%s,%s,%s,%s,%s,%s) RETURNING item_id", (dining_id, f"test food item {i}", round(random.uniform(1,25),2),
            ["flour","sugar","spice","everything nice"], [], 
            random.choice((f"test_admin{i}",f"test_student{i}"))))
            dining_items.append(item_id)
        

    student_ids = []
    for i in range(20):
        username = f"TestStudent{i+10}_actual"
        insert(cur,"INSERT INTO Users (username, account_type, hashed_password) VALUES "
        "(%s,%s,%s) RETURNING username", (username, "student", hash))
        
        student_id = insert(cur, "INSERT INTO Students (username, first_name, last_names, dob, "
        "email, edu_email, zipcode, account_status, created_at, majors, interests) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING student_id", (username, 
        f"TestFirstName{i}", f"Test last Names{i}", datetime(random.randint(1970,2009),
        random.randint(1,12), random.randint(1,28)).date(),f"student_personal-email{i}@test.com",
        f"test_edu_email-{username}@test.edu", random.randint(12345,98765), 
        random.choice("pending", "open", "denied", "closed"), 
        datetime.now() - timedelta(days=i+random.randint(1,10)), random.choice((["BS Computer Science"], 
        ["BS Biology"], ["BA History"])), random.choice((["coding", "software", "history"], ["research", 
        "geography", "music"], ["travelling", "art", "languages"]))))
        student_ids.append(student_id)


    #one review per student
    #random values does mean ratings and review text may not match
        #e.g. review might say "good review" and have a 1.0 rating
    reviews_generic = []
    for student_id in student_ids:
        school_id = random.choice(school_ids)
        review_id = insert(cur, "INSERT INTO Reviews_generic (student_id, school_id, rating, "
        "review_tags, review_title, review_comment, anonymous, submitted) VALUES "
        "(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING review_id", (student_id, school_id, 
        random.choice([x / 2 for x in range(2, 11)]), random.choice(("Helpful","Good resources")), random.choice(("good review!","bad review", 
        "meh review")), "I left a review!!!!!!", random.choice((True, False)), datetime.now() - 
        timedelta(hours=random.randint(1,100))))
        reviews_generic.append(review_id)


    for review_id in reviews_generic:
        if random.choice((True, False)) == True:
            insert(cur, "INSERT INTO Review_votes (review_id, voter_id, is_upvote, "
            "vote_time) VALUES (%s,%s,%s,%s)", 
            (review_id, random.choice(student_ids), random.choice((True, False)), datetime.now()))
    #there is a chance a student votes on their own review
    #setting timestamp to now means vote time is always after review time



#TODO: insertions to remaining tables



def main():
    # future: possibly substitute argv with argparse, to be more robust
    if len(sys.argv) != 2:
        sys.exit("Please provide exactly one argument: the postgres DSN / connection string")
    dsn = sys.argv[1]       
    #DSN format: postgresql://[user[:password]@][netloc][:port][/dbname][?param1=value1&...]
    
    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                erase_data(cur)
                
                insert_all(cur)
                print("Fresh dummy data inserted into database")
                conn.commit()
                
    except Exception as ex:
        sys.exit(f"Failed to open/write to database: {ex}")
