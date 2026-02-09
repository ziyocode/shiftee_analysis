FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

WORKDIR /app

# Lambda runtime interface client
RUN pip install --no-cache-dir awslambdaric boto3

# Install project dependencies
COPY pyproject.toml setup.py ./
COPY src/ ./src/
RUN chmod -R 755 /app/src && pip install --no-cache-dir .

ENV PYTHONPATH=/app/src

ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["src.shiftee.lambda_handler.handler"]
