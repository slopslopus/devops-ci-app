FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/slopslopus/devops-ci-app" \
      org.opencontainers.image.description="Учебное Flask-приложение для практикума по CI/CD"

RUN useradd --create-home --shell /bin/false app

WORKDIR /app

COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

USER app

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "app.app:app"]
