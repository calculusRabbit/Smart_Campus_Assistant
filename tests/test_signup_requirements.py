import pytest
from pydantic import ValidationError

from auth_models import SignupRequest


@pytest.fixture
def signup_data():
    return dict(
        username="student_1",
        first_name="Test",
        last_name="Student",
        email="student@example.edu",
        dob="2000-01-01",
        zipcode="67260",
        password="Goodpass1!",
        scorecard_id=1,
        captcha="test",
        is_primary=True,
        degree_level="Bachelor",
    )


@pytest.mark.parametrize("username", ["abcde", "a" * 30, "ab_,@!-9"])
def test_valid_usernames(signup_data, username):
    SignupRequest(**(signup_data | {"username": username}))


@pytest.mark.parametrize(
    "username", ["abcd", "a" * 31, "some.name", "ab cd", "éabcd", "xAdMiNx", "SYSTEM_1", "aLeRt99"]
)
def test_invalid_usernames(signup_data, username):
    with pytest.raises(ValidationError):
        SignupRequest(**(signup_data | {"username": username}))


@pytest.mark.parametrize("password", ["Aa1!xxxx", "Aa1!" + "x" * 124])
def test_valid_password_boundaries(signup_data, password):
    SignupRequest(**(signup_data | {"password": password}))


@pytest.mark.parametrize(
    "password",
    ["Aa1!xxx", "Aa1!" + "x" * 125, "lowercase1!", "UPPERCASE1!", "NoDigits!!", "NoSpecial123"],
)
def test_invalid_passwords(signup_data, password):
    with pytest.raises(ValidationError):
        SignupRequest(**(signup_data | {"password": password}))


@pytest.mark.parametrize("special", " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
def test_each_allowed_special(signup_data, special):
    SignupRequest(**(signup_data | {"password": "Abcdef1" + special}))


def test_location_instead_of_zip(signup_data):
    request = SignupRequest(
        **(
            signup_data
            | {"zipcode": None, "latitude_approx": 37.6872, "longitude_approx": -97.3301}
        )
    )
    assert request.latitude_approx == 37.69
    assert request.longitude_approx == -97.33


@pytest.mark.parametrize(
    "location",
    [
        {},
        {"latitude_approx": 37},
        {"latitude_approx": 91, "longitude_approx": 0},
        {"latitude_approx": 0, "longitude_approx": float("nan")},
    ],
)
def test_missing_or_invalid_location(signup_data, location):
    with pytest.raises(ValidationError):
        SignupRequest(**(signup_data | {"zipcode": None} | location))


def test_optional_subjects_and_nonprimary(signup_data):
    request = SignupRequest(**(signup_data | {"is_primary": False}))
    assert request.majors == request.minors == []
    assert request.is_primary is False


@pytest.mark.parametrize(
    "field",
    ["first_name", "last_name", "email", "dob", "scorecard_id", "is_primary", "degree_level"],
)
def test_required_profile_fields(signup_data, field):
    del signup_data[field]
    with pytest.raises(ValidationError):
        SignupRequest(**signup_data)
