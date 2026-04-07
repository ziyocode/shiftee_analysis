FROM --platform=linux/amd64 mcr.microsoft.com/playwright/python:v1.58.0-jammy

WORKDIR /app

# Install uv
RUN python -m pip install --no-cache-dir uv

# Install project dependencies into venv
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
RUN chmod -R 755 /app/src && uv sync --frozen --no-dev --extra lambda

ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["src.shiftee.lambda_handler.handler"]
