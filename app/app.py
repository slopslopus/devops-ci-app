"""Учебное Flask-приложение для практикума по CI/CD."""

from flask import Flask, jsonify


def create_app() -> Flask:
    """Создать и настроить экземпляр Flask-приложения."""
    application = Flask(__name__)

    @application.get("/health")
    def health():
        """Проверка работоспособности сервиса."""
        return jsonify(status="ok")

    @application.get("/")
    def index():
        """Корневой маршрут с информацией о сервисе."""
        return jsonify(
            service="devops-ci-app",
            version="1.0.0",
            status="running",
        )

    return application


app = create_app()
