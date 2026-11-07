# devops-ci-app

Учебное Flask-приложение для практической работы «Непрерывная интеграция
и публикация образа»: Pylint → pytest → Docker build → smoke-test → GHCR.

Образ публикуется в GHCR только из ветки `main`; в pull request
выполняются проверки без push образа.
