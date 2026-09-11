def events_data():
    return [
        {
            "event_id": 1,
            "event_name": "C++ Competition",
            "event_date": "2026-03-20",
            "event_time": "10:00 AM",
            "event_location": "Rhatigan Student Center",
            "event_description": "A coding competition for students"
        },
        {
            "event_id": 2,
            "event_name": "Career Fair",
            "event_date": "2026-03-25",
            "event_time": "1:00 PM",
            "event_location": "John Bardo Center",
            "event_description": "Meet employers and explore job opportunities"
        }
    ]


def dining_data():
    return [
        {
            "dining_id": 1,
            "dining_name": "Chick-fil-A",
            "opening_time": "7:00 AM",
            "closing_time": "10:00 PM",
            "dining_location": "Rhatigan Student Center",
            "dining_status": "Open"
        },
        {
            "dining_id": 2,
            "dining_name": "Panda Express",
            "opening_time": "7:00 AM",
            "closing_time": "10:00 PM",
            "dining_location": "Rhatigan Student Center",
            "dining_status": "Open"
        }
    ]


def courses_data():
    return [
        {
            "id": 1,
            "code": "CS 560",
            "name": "Machine Learning",
            "time": "TR 2:00-3:15 PM",
            "room": "Jabara 210",
            "professor": "Dr. Yang",
            "department": "Computer Science",
            "description": "Introduction to machine learning concepts and models",
            "credits": 3
        },
        {
            "id": 2,
            "code": "CS 598",
            "name": "Senior Design Project",
            "time": "MW 10:00-11:15 AM",
            "room": "RSC 261",
            "professor": "Dr. Smith",
            "department": "Computer Science",
            "description": "Capstone project course for senior students",
            "credits": 3
        }
    ]


def professors_data():
    return [
        {
            "professor_id": 101,
            "professor_name": "Professor Cody AI",
            "professor_department": "Computer Science",
            "professor_email": "codyai@wsu.edu",
            "office_location": "Room 209",
            "professor_rating": 4.7
        },
        {
            "professor_id": 102,
            "professor_name": "Professor Thomas AI",
            "professor_department": "Computer Science",
            "professor_email": "thomasai@wsu.edu",
            "office_location": "Room 201",
            "professor_rating": 4.5
        }
    ]


def deadlines_data():
    return [
        {
            "deadline_id": 1,
            "deadline_title": "Course Registration Deadline",
            "deadline_date": "2026-04-15",
            "deadline_description": "Last day to register for Summer classes"
        },
        {
            "deadline_id": 2,
            "deadline_title": "Add/Drop Deadline",
            "deadline_date": "2026-03-10",
            "deadline_description": "Last day to add or drop a course without penalty"
        }
    ]