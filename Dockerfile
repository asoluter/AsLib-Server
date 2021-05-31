FROM python:3.8-slim

ENV PYTHONUNBUFFERED 1

EXPOSE 8000
WORKDIR /aslib


RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY poetry.lock pyproject.toml ./
RUN pip install poetry && \
    poetry config virtualenvs.in-project true && \
    poetry install

COPY . ./

CMD poetry run alembic upgrade head && \
    poetry run uvicorn app.api.server:app --reload --workers 1 --host 0.0.0.0 --port 8000