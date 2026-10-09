# requires: psycopg, bcrypt
# populates existing postgres DB according to sca_database_v0.4.0.sql with dummy data

# run command: python <this_script_name> <DSN> --reset
    #DSN format: postgresql://[user[:password]@][netloc][:port][/dbname][?param1=value1&...]


import argparse

#import os
import random
import sys
from datetime import UTC, datetime, timedelta
from typing import LiteralString

import bcrypt
import psycopg

# from psycopg.rows import TupleRow
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

now = datetime.now(UTC)

anon_username_fields = ["student","campus","uni","college","whistleblower","reviewer","critic"]

#==================================================================


#wipes any existing dummy data from all tables for a fresh re-population
def erase_data(cur: psycopg.Cursor) -> None:
    cur.execute("""
        TRUNCATE Schools, Users, Departments, Locations, Events, Dining, 
        Courses, Sessions, Enrolments, Offerings, Students, Deadlines, Instructors, 
        Reviews_generic, Review_votes, Review_replies, Reviews_educational, 
        Reviews_dining, Dining_items, Reviews_resources, Authentications, Notifications,
        Groups, Memberships, Registrations, Event_responses, Scraped_information, 
        Attendance, Event_embeddings
        RESTART IDENTITY CASCADE""")


# runs an insert operation and returns the serials created
def insert(cur: psycopg.Cursor, query: LiteralString, params:tuple) -> int | str:
    cur.execute(query, params)
    return cur.fetchone()[0] # type: ignore

#inserts dummy data into all tables
def insert_all(cur: psycopg.Cursor):  # noqa: C901 - done since this is a dev script that just inserts data into many tables
    
    school_ids = []
    for i in range(min(10, user_count)):
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
        (school_id, 
        f"{random.randint(1,5000)} Test {random.choice(('St','Rd','Ln','Circle','Dr'))}",
        f"{random.choice(('room','Rm','suite'))} {random.randint(1,400)}", 
        f"Test City {random.randint(1,10)}", random.choice(("TX","KS","OK","CA","NY")), 
        f"{random.randint(0, 99999):05d}", True, "active",
        Jsonb([{'days': [0,6], 'times': []}, {'days': [1,2,3,4,5], 'times': [['09:00', '17:00']]}]))
        )
        location_ids.append((location_id, school_id))
        #update locations for schools
        cur.execute("UPDATE Schools SET location_id = %s WHERE school_id = %s", 
                    (location_id, school_id))

    usernames = []

    for i in range(user_count):
        admin_username = f"test_admin{i}"
        insert(cur, "INSERT INTO Users (username, account_type, hashed_password) "
        "VALUES (%s,%s,%s) RETURNING username", (admin_username,"admin",password_hash))
        usernames.append(admin_username)

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
        random.randint(1,12), random.randint(1,28), tzinfo=UTC).date(),
        f"student_personal-email{i}@test.com",
        f"test_edu_email-{username}@test.edu", f"{random.randint(0, 99999):05d}", 
        random.choice(["pending", "open", "denied", "closed"]), 
        now - timedelta(days=i+random.randint(1,10)), 
        random.choice((["coding", "software", "history"], ["research", 
        "geography", "music"], ["travelling", "art", "languages"]))))
        student_ids.append(student_id)
        usernames_by_student[student_id] = username
        usernames.append(username)



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
        (dept_id, "TEST", f"{random.randint(100,999)}{random.choice(('','AN','AQ','K'))}",
        f"Test Course from {dept_id}", "Test course description.", 3.0))
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
                           (student_id, enrolled_school, 
                            random.choice((None, ["BS Computer Science"], 
                            ["BS Biology"], ["BA History","BEng Mechanical Eng"])), 
                           random.choice([None,["Math"],["Math", "CE"]]), 
                           random.choice((True,False)),True,
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
            "offering_session, class_timings, school_id, primary_instructor) " 
            "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING offering_id",
            (f"{course_id+1234}",course_id, location_id, session_id, 
            Jsonb([{'days': [2,4], 'times': [['11:00','12:15']]}, 
                   {'days': [0,1,3,5,6], 'times': []}]), 
            school_id,
            random.choice(dept_instructors)))
        offering_ids.append((offering_id, course_id, dept_id, school_id, session_id))


    dining_locations = []
    for (location_id, school_id) in location_ids:
        dining_id = insert(cur, "INSERT INTO DINING (dining_name, location_id, cuisine, "
        "reservations, event_status) VALUES (%s, %s, %s, %s, %s) RETURNING dining_id", 
        (f"test restaurant {location_id}", location_id, 
        [random.choice(('indian','chinese','korean'))],
        random.choice((True,False)), random.choice((True,False))))
        dining_locations.append((dining_id, school_id, location_id))
    
    
    dining_items = []
    for dining_id, school_id, _location_id in dining_locations:
        # pick a random student from the school for review item added by
        student = random.choice(students_by_school[school_id])
        for i in range(10):
            item_name = f"test food item {i}"
            item_id = insert(cur, "INSERT INTO Dining_items (dining_id, item_name, item_price, "
            "item_calories, item_ingredients, dietary_tags, entered_by) VALUES "
            "(%s,%s,%s,%s,%s,%s,%s) RETURNING item_id", (dining_id, item_name, 
                                                         round(random.uniform(1,25),2),
            random.randint(100,1200),["sugar","spice","everything nice"], [], 
            usernames_by_student[student]))
            dining_items.append((dining_id, item_id, item_name))
        

    #one review per student
    reviews_generic = []
    review_times = {}
    for student_id in student_ids:
        school_id = school_by_student[student_id]
        review_time = now - timedelta(hours=random.randint(1,10))
        
        #splitting reviews into categories
        review_state = random.choice(("excellent", "very good", 
                                      "good", "mediocre", "bad", "very bad"))
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
                review_comment = "Very bad review!! Everything sucks, you should go out of business"
        
        #anonymous reviews
        is_anonymous = random.choice([True, False])
        anonymous_username = None
        if is_anonymous:
            anonymous_username = (
            f"{random.choice(anon_username_fields).title()}_"
            f"{random.choice(anon_username_fields).title()}"
            f"{random.randint(0,9)}{random.randint(0,9)}"
            )
        
        review_id = insert(cur, "INSERT INTO Reviews_generic (student_id, school_id, rating, "
        "review_tags, review_title, review_comment, anonymous, anonymous_username, submitted) " 
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING review_id", (student_id, school_id, 
        rating, random.choice((["Helpful","Comprehensive","Most upvoted"],["Good resources"],[])), 
        review_title, 
        review_comment, is_anonymous, anonymous_username, review_time))
        reviews_generic.append((review_id, student_id, school_id))
        review_times[review_id] = review_time


    for review_id, student_id, _school_id in reviews_generic:
        if random.choice((True, False)):
            random_student = random.choice(student_ids)
            #ensure voter is not the review author
            while random_student == student_id:
                random_student = random.choice(student_ids)
            insert(cur, "INSERT INTO Review_votes (review_id, voter_id, is_upvote, "
            "vote_time) VALUES (%s,%s,%s,%s) RETURNING review_id", 
            (review_id, random_student, random.choice((True, False)), 
            review_times[review_id] + timedelta(seconds=random.randint(
                0, int((now - review_times[review_id]).total_seconds())))))



    offerings_by_school = {school_id: [] for school_id in school_ids}
    #offerings_by_student = {student_id: [] for student_id in student_ids}
    dining_by_school = {school_id: [] for school_id in school_ids}
    items_by_dining = {}

    for offering_id, course_id, dept_id, school_id, session_id in offering_ids:
        offerings_by_school[school_id].append(
            (offering_id, course_id, dept_id, session_id)
        )

    for dining_id, school_id, _location_id in dining_locations:
        dining_by_school[school_id].append(dining_id)
        items_by_dining[dining_id] = []

    for dining_id, _item_id, item_name in dining_items:
        items_by_dining[dining_id].append(item_name)



    #TODO: insertions to remaining tables

    #Review_replies
    
    review_replies = []
    for review_id, student_id, _school_id in reviews_generic:
        if random.choice((True, False)):
            
            random_student = random.choice(student_ids)
            #ensure voter is not the review author
            while random_student == student_id:
                random_student = random.choice(student_ids)
            
            reply_type = random.choice(("agree", "disagree", "add-details", "question"))
            match reply_type:
                case "agree":
                    reply_content = "I agree with your review!"
                    #action = "upvote"
                case "disagree":
                    reply_content = "I disagree with your review!"
                    #action = "downvote"
                case "add-details":
                    reply_content = "Adding on more info!"
                case "question":
                    reply_content = "I'm asking a question!"

            is_anonymous = random.choice([True, False])
            anonymous_username = None
            if is_anonymous:
                anonymous_username = (
                f"{random.choice(anon_username_fields).title()}_"
                f"{random.choice(anon_username_fields).title()}"
                f"{random.randint(0,9)}{random.randint(0,9)}"
            )            
            reply_id = insert(cur, "INSERT INTO Review_replies (review_id, "
                              "replier_id, anonymous_reply, anonymous_username, "
                              "reply_content, reply_time) "
                              "VALUES (%s,%s,%s,%s,%s,%s) RETURNING reply_id",
                              (review_id, random_student, is_anonymous, anonymous_username,
                               reply_content, 
                               review_times[review_id]+
                               timedelta(seconds=random.randint(
                                   0, int((now - review_times[review_id]).total_seconds()))
                                   )
                                )
                        )
            review_replies.append((reply_id, review_id, random_student))

    
    #Reviews_educational, Reviews_dining, Reviews_resources
    for i, (review_id, student_id, school_id) in enumerate(reviews_generic):
        if i % 3 == 0:
            offering_id, _course_id, dept_id, _session_id = random.choice(
            offerings_by_school[school_id])
            instructor_id = random.choice([ instructor_id for instructor_id, department_id, 
                                           _school_id in instructor_ids if department_id == dept_id
            ])

            insert(cur, "INSERT INTO Reviews_educational (review_id, student_id, offering_id, "
                   "instructor_id, department_id, class_method, student_tips) "
                   "VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING review_id",
                   (review_id, student_id, offering_id, instructor_id, dept_id,
                    "in-person", "start on homework early and go to lectures!"))

        elif i % 3 == 1:
            dining_id = random.choice(dining_by_school[school_id])
            ordered_items = random.sample(items_by_dining[dining_id], random.randint(1,3))
            spent_min = random.randint(5,30)

            insert(cur, "INSERT INTO Reviews_dining (review_id, dining_id, ordered_items, "
                   "diner_count, spent_range, order_method, cleanliness_rating, service_rating, "
                   "spiciness_rating, recommended_food, avoid_food, accommodates_diets) "
                   "VALUES (%s,%s,%s,%s,%s::int4range,%s,%s,%s,%s,%s,%s,%s) RETURNING review_id",
                   (review_id, dining_id, ordered_items, random.randint(1,4),
                    f"[{spent_min},{spent_min+11})",
                    random.choice(("dine-in","drive-through","pickup","delivery",
                                   "other app delivery")), random.randint(2,10)/2,
                                   random.randint(2,10)/2, random.randint(2,10)/2,
                                   ordered_items[:1], [], []))

        else:
            insert(cur, "INSERT INTO Reviews_resources (review_id, resource_type, campus_staff) "
                   "VALUES (%s,%s,%s) RETURNING review_id", (review_id, random.choice((
                       "academic", "campus facilities", "tech support", "parking", "internet/WiFi",
                         "management", "club/org", "fundraising")), ["test staff"]))
    
    
    
    
    #Events
    event_ids = []
    for location_id, school_id in location_ids:
        event_creator = random.choice(usernames)
        event_name = random.choice(("Test club", "Test department", 
                                    "Test school", "Test org")) + " " + random.choice(("Party",
                                    "Social","Game night","Mixer","Hackathon")) 
        event_start = now + timedelta(days=random.randint(1,14))
        event_end = event_start + timedelta(hours=random.randint(1,5))

        event_time = ('{["' + event_start.isoformat()+ '","'+ event_end.isoformat() +'")}')

        event_id = insert(cur,"INSERT INTO Events (event_name, event_time, event_location, "
                          "event_description,event_creator, event_tags, public_cost, student_cost) "
                          "VALUES (%s,%s::tstzmultirange,%s,%s,%s,%s,%s,%s) RETURNING event_id",
                          (event_name, event_time, location_id,
                           "Test campus event", event_creator, ["test", "campus"], 10.00, 0.00))
        event_ids.append((event_id, school_id))
    
    #Event_responses
    for event_id, school_id in event_ids:
        for student_id in students_by_school[school_id]:
            insert(cur, "INSERT INTO Event_responses (username, event_id, response_time, "
                   "user_action) VALUES (%s,%s,%s,%s) RETURNING response_id",
                    (usernames_by_student[student_id], event_id, now, 
                    random.choice(("saved", "dismissed", "opened"))))
    
    #Deadlines
    for student_id in student_ids:
        insert(cur, "INSERT INTO Deadlines (student_id, deadline_action, deadline_datetime, "
               "deadline_description) VALUES (%s,%s,%s,%s) RETURNING deadline_id",
               (student_id, "assignment due", now + timedelta(days=random.randint(1,14)),
                "test assignment deadline"))

    
    #Authentications
    #pending status inserted, then updated to denied/approved so trigger runs as normal
    for student_id in student_ids:
        cur.execute("SELECT account_status, created_at FROM Students WHERE student_id = %s",
                    (student_id,))
        account_status, created_at = cur.fetchone() # pyright: ignore[reportGeneralTypeIssues]
        auth_id = insert(cur, "INSERT INTO Authentications (student_id, status, documents, "
                         "submitted_time) VALUES (%s,%s,%s,%s) RETURNING authentication_id",
            (student_id, "pending",[f"dummy://documents/{student_id}.pdf"], created_at))
        if account_status != "pending":
            if account_status == "denied":
                status = "denied"
            else:
                status = "approved"
            cur.execute("UPDATE Authentications SET status=%s, reviewed_time=%s, admin_message=%s "
                        "WHERE authentication_id = %s",(status, now, "dummy decision", auth_id))
    
    
    
    #Notifications
    for username in usernames:
        sent_time = now - timedelta(hours=random.randint(1,48))
        read_time = None
        if random.choice((True,False)):
            read_time = now - timedelta(seconds=random.randint(1,300))
        insert(cur, "INSERT INTO Notifications (username, notification_title,notification_message, "
               "sent_time, read_time) VALUES (%s,%s,%s,%s,%s) RETURNING notification_id",
               (username, "test notification", "test notification message", sent_time, read_time))

    
    #Groups
    group_ids = []
    for dept_id, school_id in department_ids:
        group_owner = usernames_by_student[students_by_school[school_id][0]]
        group_id = insert(cur, "INSERT INTO Groups (group_name, group_description, group_owner, "
                "is_verified, created_at, school_id, department_id, group_type, "
                 "group_contact, group_links) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                 "RETURNING group_id", (f"test group {school_id}", "test campus club", group_owner, 
                                        True, (now - timedelta(days=random.randint(5,120))).date(), 
                                        school_id, dept_id, "club",
                                        Jsonb({"email": f"club{school_id}@test.edu"}),
                                        Jsonb({"website": f"test.edu/orgs/{school_id}"})))
        group_ids.append((group_id, school_id, group_owner))



    #Memberships
    for group_id, school_id, group_owner in group_ids:
        for student_id in students_by_school[school_id]:
            username = usernames_by_student[student_id]
            if username == group_owner:
                membership_status = "active"
            else:
                membership_status= random.choice(("active", "pending", "denied", "cancelled"))

            roles = ["member"]
            if username == group_owner:
                roles.append("owner")
            membership_end = None
            if membership_status == "cancelled":
                membership_end = now
            
            insert(cur,"INSERT INTO Memberships (username, group_id, roles, membership_start, " 
            "membership_end, membership_status) VALUES (%s,%s,%s,%s,%s,%s) "
            "RETURNING username", (username, group_id, roles, 
                                        now - timedelta(days=random.randint(1,4)),
            membership_end, membership_status))
        
    
    #Registrations
    registrations = []
    for student_id in student_ids:
        school_id = school_by_student[student_id]
        for offering_id, _course_id, _dept_id, session_id in offerings_by_school[school_id]:
            insert(cur,"INSERT INTO Registrations (student_id, offering_id, study_group, auditing) "
                "VALUES (%s,%s,%s,%s) RETURNING student_id", 
                (student_id,offering_id, random.choice((True,False)),False))
            registrations.append((student_id, offering_id, session_id))

    
    #Attendance

    session_dates = {}
    for session_id, _school_id in session_ids:
        cur.execute("SELECT session_start, session_end FROM Sessions WHERE session_id = %s",
                    (session_id,))
        session_dates[session_id] = cur.fetchone()

    for student_id, offering_id, session_id in registrations:
        session_start, session_end = session_dates[session_id]
        for i in range(14):
            attendance_date = session_start + timedelta(days=i)
            class_day = (attendance_date.weekday() + 1) % 7
            if attendance_date<= min(session_end,now.date()) and class_day in (2,4):
                cur.execute("INSERT INTO Attendance (student_id, offering_id, attendance_date, " \
                "student_present) VALUES (%s,%s,%s,%s)", (student_id, offering_id, attendance_date,
                                                          random.choice((True,True,False))))



def main():
    
    # if len(sys.argv) != 2:
    #     sys.exit("Please provide exactly one argument: the postgres DSN / connection string")
    # dsn = sys.argv[1]       
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True, help="DSN connection string to existing database")
    parser.add_argument("--reset",'-r', action="store_true", 
                        help="delete existing data in database?")
    parser.add_argument("--seed",'-s', type=int, default=67) #will be used if seed is used for RNG
    parser.add_argument("--num-users",'-n', type=int, default=20)
    args = parser.parse_args()


    if not args.reset:
        parser.error("the script needs --reset to run, to prevent duplicates of unique records.")

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
            conn.commit()
            print("Fresh dummy data inserted into database")


    except psycopg.errors.OperationalError as ex:
        sys.exit(f"Failed to connect to / write to database: {ex}")
    except psycopg.errors.UniqueViolation as ex:
        sys.exit(f"Failed to write to field due to unique constraint: {ex}")
    except psycopg.DatabaseError as ex:
        sys.exit(f"A stopping database failure ocurred: {ex}")


if __name__ == "__main__":
    main()