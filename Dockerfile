FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

WORKDIR /app

# Install uv and use the system Python environment for the project
RUN python -m pip install --no-cache-dir uv
ENV UV_PROJECT_ENVIRONMENT=/usr/local

# Install project dependencies
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
RUN chmod -R 755 /app/src && uv sync --frozen --no-dev --extra lambda

ENV PYTHONPATH=/app/src

ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["src.shiftee.lambda_handler.handler"]
