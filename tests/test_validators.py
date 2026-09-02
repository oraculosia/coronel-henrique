import pytest

from src.utils.validators import (
    normalize_email,
    normalize_whatsapp,
    validate_email_address,
    validate_password,
    validate_whatsapp,
)


def test_normalize_email_trims_and_lowercases() -> None:
    assert normalize_email("  William@Example.COM ") == "william@example.com"


def test_validate_email_address_accepts_valid_email() -> None:
    ok, result = validate_email_address("programador.descpro@gmail.com")
    assert ok
    assert result == "programador.descpro@gmail.com"


def test_validate_email_address_rejects_invalid_email() -> None:
    ok, message = validate_email_address("not-an-email")
    assert not ok
    assert message


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("31998417976", "+5531998417976"),
        ("(31) 99841-7976", "+5531998417976"),
        ("5531998417976", "+5531998417976"),
        ("+5531998417976", "+5531998417976"),
    ],
)
def test_normalize_whatsapp_adds_country_code(raw: str, expected: str) -> None:
    assert normalize_whatsapp(raw) == expected


def test_normalize_whatsapp_empty_input() -> None:
    assert normalize_whatsapp("") == ""
    assert normalize_whatsapp(None) == ""  # type: ignore[arg-type]


def test_validate_whatsapp_accepts_valid_number() -> None:
    ok, result = validate_whatsapp("31998417976")
    assert ok
    assert result == "+5531998417976"


def test_validate_whatsapp_rejects_too_short_number() -> None:
    ok, message = validate_whatsapp("123")
    assert not ok
    assert "válido" in message


def test_validate_password_requires_minimum_length() -> None:
    ok, message = validate_password("Ab1")
    assert not ok
    assert "8 caracteres" in message


def test_validate_password_requires_uppercase() -> None:
    ok, message = validate_password("abcdefg1")
    assert not ok
    assert "maiúscula" in message


def test_validate_password_requires_lowercase() -> None:
    ok, message = validate_password("ABCDEFG1")
    assert not ok
    assert "minúscula" in message


def test_validate_password_requires_digit() -> None:
    ok, message = validate_password("Abcdefgh")
    assert not ok
    assert "número" in message


def test_validate_password_accepts_strong_password() -> None:
    ok, message = validate_password("William@2026")
    assert ok
    assert message == ""
