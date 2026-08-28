# syntax=docker/dockerfile:1
# NebrasCRM application image. Database services are defined in docker-compose.yml.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN python3 -m pip install --upgrade pip \
    && python3 -m pip install -r requirements.txt

RUN groupadd --gid 10001 nebras \
    && useradd --uid 10001 --gid nebras --create-home --shell /usr/sbin/nologin nebras

COPY --chown=nebras:nebras . ./

USER nebras
EXPOSE 8008

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8008"]
