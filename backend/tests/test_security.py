from datetime import timedelta

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_is_salted_and_verifiable():
    h1, h2 = hash_password("password123"), hash_password("password123")
    assert h1 != h2
    assert verify_password("password123", h1)
    assert not verify_password("wrong", h1)


def test_verify_password_handles_garbage_hash():
    assert verify_password("x", "not-a-bcrypt-hash") is False


def test_token_round_trip():
    assert decode_access_token(create_access_token(42)) == 42


def test_expired_token_is_rejected():
    assert decode_access_token(create_access_token(1, timedelta(seconds=-5))) is None


def test_garbage_token_is_rejected():
    assert decode_access_token("not.a.token") is None
