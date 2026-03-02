import os
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Ensure "import app.*" works when pytest is run from backend/ or project root.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(scope="session")
def test_database_url() -> str:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip(
            "TEST_DATABASE_URL is not set. "
            "Set a dedicated PostgreSQL URL for tests before running pytest.",
            allow_module_level=True,
        )
    return url


@pytest.fixture(scope="session")
def app_and_session_factory(test_database_url: str):
    os.environ["DATABASE_URL"] = test_database_url

    # Import after injecting DATABASE_URL so the app binds to the test DB.
    import app.models  # noqa: F401
    from app.core.db import Base
    from app.api.deps import get_db
    from app.main import app
    import app.api.routers.missions as missions_router
    import app.api.routers.allocator as allocator_router

    engine = create_engine(test_database_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    SessionTesting = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # Keep tests deterministic (no background thread/sleep/random side effects).
    missions_router.start_mission_simulation = lambda _mission_id: None
    allocator_router.start_mission_simulation = lambda _mission_id: None

    def override_get_db():
        db = SessionTesting()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return app, SessionTesting


@pytest.fixture(autouse=True)
def clean_tables(app_and_session_factory):
    _, SessionTesting = app_and_session_factory
    db = SessionTesting()
    try:
        db.execute(
            text(
                """
                TRUNCATE TABLE
                  allocator_run_items,
                  allocator_runs,
                  telemetry,
                  events,
                  mission_steps,
                  missions,
                  orders,
                  robots
                RESTART IDENTITY CASCADE
                """
            )
        )
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def client(app_and_session_factory):
    app, _ = app_and_session_factory
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def unique_suffix():
    return uuid.uuid4().hex[:8]
