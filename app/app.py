"""HTTP-приложение для проверки CI-конвейера."""

from flask import Flask, jsonify


def create_app():
    """Создаёт и настраивает экземпляр приложения."""
    application = Flask(__name__)

    @application.get("/health")
    def health():
        """Возвращает результат простой проверки жизнеспособности."""
        return jsonify(status="ok")

    @application.get("/")
    def index():
        """Возвращает сведения о службе."""
        return jsonify(
            service="devops-ci-app",
            version="1.0.0",
            status="running",
        )

    return application


app = create_app()
