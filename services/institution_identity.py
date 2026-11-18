from email_validator import EmailNotValidError, validate_email
from fastapi import HTTPException


def normalize_edu_email(value: str) -> str:
    try:
        parsed = validate_email(
            value.strip(),
            check_deliverability=False,
        )
    except EmailNotValidError as exc:
        raise HTTPException(400, "Please enter a valid email address.") from exc

    domain = parsed.ascii_domain
    if domain is None or not domain.lower().endswith(".edu"):
        raise HTTPException(400, "Please enter your .edu email address.")

    return parsed.normalized.lower()


def matches_domain(
    domain: str,
    allowed_domains: list[str],
    *,
    allow_subdomains: bool = False,
) -> bool:
    domain = domain.lower().rstrip(".")

    for value in allowed_domains:
        allowed = value.strip().lower().rstrip(".")

        if not allowed or allowed == "edu":
            continue

        if domain == allowed:
            return True

        if allow_subdomains and domain.endswith("." + allowed):
            return True

    return False


def require_institution_email(
    email: str,
    allowed_domains: list[str],
) -> str:
    email = normalize_edu_email(email)
    domain = email.rsplit("@", 1)[1]

    if not allowed_domains:
        raise HTTPException(
            503,
            "Sorry, institution email domains are temporarily unavailable. "
            "Please try again later or use manual verification.",
        )

    if not matches_domain(
        domain,
        allowed_domains,
        allow_subdomains=True,
    ):
        raise HTTPException(
            400,
            "This email doesn't match your selected institution.",
        )

    return email