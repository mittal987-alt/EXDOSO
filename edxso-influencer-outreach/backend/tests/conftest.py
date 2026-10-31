import os
import sys

# Ensure backend directory is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.influencer import Influencer
from app.models.outreach_message import OutreachMessage
from app.models.delivery_log import DeliveryLog


# Use in-memory SQLite with StaticPool for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test function."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client with database dependency overridden."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_qualified_influencer(db_session):
    """Seed a qualified influencer in the test database."""
    influencer = Influencer(
        name="Alex Trainer",
        platform="YouTube",
        profile_url="https://www.youtube.com/channel/UC_ALEX_TRAINER_01",
        follower_count=25000,
        engagement_rate=3.5,
        category="Fitness & Wellness",
        content_themes="Workout and Training, Nutrition and Diet",
        contact_email="alex@example.com",
        website="https://alextrainer.com",
        geography="United States",
        source_url="https://www.youtube.com/channel/UC_ALEX_TRAINER_01",
        qualification_status="Qualified",
    )
    db_session.add(influencer)
    db_session.commit()
    db_session.refresh(influencer)
    return influencer


@pytest.fixture
def sample_pending_influencer(db_session):
    """Seed a pending influencer in the test database."""
    influencer = Influencer(
        name="Sam Wellness",
        platform="YouTube",
        profile_url="https://www.youtube.com/channel/UC_SAM_WELLNESS_02",
        follower_count=50000,
        engagement_rate=4.2,
        category="Fitness",
        content_themes="Yoga and Wellness",
        contact_email=None,
        website=None,
        geography="Canada",
        source_url="https://www.youtube.com/channel/UC_SAM_WELLNESS_02",
        qualification_status="Pending",
    )
    db_session.add(influencer)
    db_session.commit()
    db_session.refresh(influencer)
    return influencer
