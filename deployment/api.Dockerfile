ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/packages/contracts/src
ARG TBR_API_REQUIREMENTS=services/api/requirements.txt
COPY deployment/api-bootstrap.requirements.txt /tmp/bootstrap.requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/bootstrap.requirements.txt
COPY pyproject.toml ./
COPY src ./src
COPY services ./services
COPY packages/contracts ./packages/contracts
COPY deployment ./deployment
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
RUN if [ "$TBR_API_REQUIREMENTS" != "deployment/api-bootstrap.requirements.txt" ]; then \
      python -m pip install --no-cache-dir -r "$TBR_API_REQUIREMENTS"; \
    fi
RUN mkdir -p /var/lib/tbr-work && chown 10001:10001 /var/lib/tbr-work
USER 10001:10001
CMD ["python", "-m", "uvicorn", "services.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
