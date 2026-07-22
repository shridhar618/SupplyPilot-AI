"""
Unit tests for the User model in the User Management Service.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import the User model from the service
# Since we are not in the same directory, we need to adjust the path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../services/user-management'))

from main import User, Base, get_password_hash

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    # Use an in-memory SQLite database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()

def test_create_user(db_session):
    """Test creating a new user."""
    # Arrange
    username = "testuser"
    email = "test@example.com"
    password = "securepassword123"
    hashed_password = get_password_hash(password)

    # Act
    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        first_name="Test",
        last_name="User",
        role="admin",
        department="IT"
    )
    db_session.add(new_user)
    db_session.commit()

    # Assert
    assert new_user.id is not None
    assert new_user.username == username
    assert new_user.email == email
    assert new_user.first_name == "Test"
    assert new_user.last_name == "User"
    assert new_user.role == "admin"
    assert new_user.department == "IT"
    assert new_user.is_active == True

def test_password_hashing():
    """Test that passwords are hashed correctly."""
    password = "securepassword123"
    hashed = get_password_hash(password)

    # The hashed password should not be the same as the plain text
    assert hashed != password
    # The hash should be a bcrypt hash (starts with $2b$)
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$")

def test_duplicate_email(db_session):
    """Test that creating a user with an existing email raises an integrity error."""
    from sqlalchemy.exc import IntegrityError

    # Create first user
    user1 = User(
        username="user1",
        email="test@example.com",
        hashed_password=get_password_hash("password1"),
        first_name="User",
        last_name="One"
    )
    db_session.add(user1)
    db_session.commit()

    # Attempt to create second user with same email
    user2 = User(
        username="user2",
        email="test@example.com",  # Duplicate email
        hashed_password=get_password_hash("password2"),
        first_name="User",
        last_name="Two"
    )
    db_session.add(user2)

    # This should raise an IntegrityError
    with pytest.raises(IntegrityError):
        db_session.commit()