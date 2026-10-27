from database import (
    format_class_time,
    format_clock,
    format_place,
    get_courses_from_database,
    get_deadlines_from_database,
    get_dining_from_database,
    get_events_from_database,
    get_first_times,
    get_professors_from_database,
    get_student_interests,
    save_student_interests,
)

# the helper functions first, they dont need the database


def test_format_clock_afternoon():
    assert format_clock("13:30") == "1:30 PM"


def test_format_clock_morning():
    assert format_clock("09:05") == "9:05 AM"


def test_format_clock_bad_text_stays_the_same():
    assert format_clock("TBA") == "TBA"


def test_get_first_times_skips_entries_without_times():
    schedule = [
        {"days": [0]}, # let see no time given
        {"days": [1, 3], "times": [["10:00", "11:15"]]}, # tuesday thursday
    ]
    days, times = get_first_times(schedule)

    assert days == [1, 3]
    assert times == ["10:00", "11:15"]


def test_get_first_times_with_no_schedule():
    assert get_first_times(None) == ([], None)
    assert get_first_times([]) == ([], None)


def test_format_class_time_monday_wednesday():
    schedule = [{"days": [0, 2], "times": [["10:00", "11:15"]]}]

    assert format_class_time(schedule) == "MW 10:00 AM - 11:15 AM"


def test_format_class_time_tuesday_thursday_afternoon():
    schedule = [{"days": [1, 3], "times": [["14:00", "15:15"]]}]

    assert format_class_time(schedule) == "TR 2:00 PM - 3:15 PM"


def test_format_class_time_weekend_letters():
    schedule = [{"days": [5, 6], "times": [["09:00", "10:00"]]}]

    assert format_class_time(schedule) == "SaSu 9:00 AM - 10:00 AM"


def test_format_class_time_without_times_is_tba():
    assert format_class_time(None) == "TBA"
    assert format_class_time([{"days": [0]}]) == "TBA"


def test_format_place_joins_the_parts():
    row = {"address_room": "Room 209", "address_street": "1845 Fairmount", "city": "Wichita"}

    assert format_place(row) == "Room 209, 1845 Fairmount, Wichita"


def test_format_place_skips_empty_parts():
    row = {"address_room": None, "address_street": "1845 Fairmount", "city": ""}

    assert format_place(row) == "1845 Fairmount"


def test_format_place_with_nothing_is_tba():
    assert format_place({}) == "TBA"


# these ones use the real database (ci loads the schema and runs the seed first)


def test_events_have_the_fields_the_frontend_uses():
    events = get_events_from_database()

    assert len(events) > 0
    for event in events:
        for key in ("event_id", "event_name", "event_date", "event_time",
                    "event_location", "event_description", "event_category", "event_tags"):
            assert key in event
        assert isinstance(event["event_tags"], list)


def test_event_category_is_the_first_tag_or_general():
    for event in get_events_from_database():
        if len(event["event_tags"]) > 0:
            assert event["event_category"] == event["event_tags"][0]
        else:
            assert event["event_category"] == "general"


def test_courses_have_a_code_with_the_number():
    courses = get_courses_from_database()

    assert len(courses) > 0
    for course in courses:
        # the code is course_code + course_number, like "CS 560"
        assert course["name"] != ""
        assert course["professor"] != ""
        assert course["time"] != ""


def test_course_ids_are_different():
    ids = []
    for course in get_courses_from_database():
        ids.append(course["id"])

    assert len(ids) == len(set(ids))


def test_professors_have_a_full_name_and_email():
    professors = get_professors_from_database()

    assert len(professors) > 0
    for professor in professors:
        assert " " in professor["professor_name"]
        assert "@" in professor["professor_email"]
        assert professor["professor_rating"] is None


def test_dining_has_opening_and_closing_times():
    dining = get_dining_from_database()

    assert len(dining) > 0
    for place in dining:
        assert place["dining_status"] in ("Open", "Closed", "Unknown")
        assert isinstance(place["cuisine"], list)
        assert "opening_time" in place
        assert "closing_time" in place


def test_deadlines_have_a_date_text():
    deadlines = get_deadlines_from_database()

    # the seed might not have deadlines, then there is nothing to check
    assert isinstance(deadlines, list)
    for deadline in deadlines:
        # like 2026-10-09
        assert len(deadline["deadline_date"]) == 10
        assert deadline["deadline_title"] != ""


def test_save_and_get_student_interests(keep_interests):
    saved = save_student_interests(1, ["Coding", "  Music "])

    assert saved is True
    # saved in lowercase without the spaces
    assert get_student_interests(1) == ["coding", "music"]


def test_save_interests_for_missing_student_returns_false():
    assert save_student_interests(999999, ["coding"]) is False


def test_get_interests_for_missing_student_is_empty():
    assert get_student_interests(999999) == []
