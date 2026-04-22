from app.core.security import hash_password, verify_password


def test_password_hash_roundtrip():
    stored = hash_password("Admin12345")
    assert stored != "Admin12345"
    assert verify_password("Admin12345", stored)
    assert not verify_password("wrong", stored)

