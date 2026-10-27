import pytest
from scrapers.scrape_wsu_faculty import parse_faculty


def make_html(cards):
    return f"""
    <main>
        <h2>Faculty</h2>
        <div class="collection__items profiles">
            {cards}
        </div>
        <h2>Staff</h2>
        <div class="collection__items profiles">
            <div class="teaser collection__item profile">
                <h3 class="profile-name">Staff Member</h3>
                <p class="profile-display-email">
                    <a href="mailto:staff@wichita.edu">staff@wichita.edu</a>
                </p>
            </div>
        </div>
    </main>
    """


def faculty_card(name, email, title="Assistant Professor"):
    return f"""
    <div class="teaser collection__item profile">
        <h3 class="profile-name">
            <a class="profile-name-link" href="/profiles/example.php">
                {name}
            </a>
        </h3>
        <p class="profile-display-profile_title">{title}</p>
        <p class="profile-display-email">
            <a href="mailto:{email}">{email}</a>
        </p>
        <p class="profile-display-phone">(316) 978-1234</p>
    </div>
    """


def test_extracts_faculty_information():
    html = make_html(faculty_card("Jane Smith", "jane.smith@wichita.edu"))

    result = parse_faculty(html)

    assert len(result) == 1
    assert result[0]["name"] == "Jane Smith"
    assert result[0]["title"] == "Assistant Professor"
    assert result[0]["email"] == "jane.smith@wichita.edu"
    assert result[0]["department"] == "School of Computing"
    assert result[0]["phone"] == "(316) 978-1234"
    assert result[0]["profile_url"].endswith("/profiles/example.php")


def test_staff_are_excluded():
    html = make_html(faculty_card("Jane Smith", "jane.smith@wichita.edu"))

    result = parse_faculty(html)

    assert len(result) == 1
    assert all(person["name"] != "Staff Member" for person in result)


def test_duplicate_emails_are_removed():
    card = faculty_card("Jane Smith", "jane.smith@wichita.edu")
    html = make_html(card + card)

    result = parse_faculty(html)

    assert len(result) == 1


def test_missing_email_is_skipped():
    html = make_html(faculty_card("Jane Smith", ""))

    result = parse_faculty(html)

    assert result == []


def test_missing_faculty_section_raises_error():
    with pytest.raises(ValueError, match="Faculty section not found"):
        parse_faculty("<main><h2>Staff</h2></main>")
