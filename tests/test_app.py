"""Тесты учебного Flask-приложения."""

import pytest
from app.app import create_app


@pytest.fixture(name="client")
def client_fixture():
    """Тестовый клиент Flask-приложения."""
    application = create_app()
    application.config.update(TESTING=True)
    with application.test_client() as client:
        yield client


def test_health(client):
    """Маршрут /health возвращает статус ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_index(client):
    """Корневой маршрут возвращает описание сервиса."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json() == {
        "service": "devops-ci-app",
        "version": "1.0.0",
        "status": "running",
    }
