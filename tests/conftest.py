from __future__ import annotations

import pytest

from cloudalloc import create_app
from cloudalloc.extensions import db


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.sqlite3'}",
            "ARTIFACT_DIR": str(tmp_path / "artifacts"),
            "SECRET_KEY": "test",
        }
    )
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()

