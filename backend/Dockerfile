# A Dockerfile is like a recipe for building a container.
# It says: "start with Python, copy my code in, install dependencies, then run."

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create the uploads directory so file uploads have a place to go
RUN mkdir -p /app/uploads/contracts

# In production, we do NOT use --reload (which watches for file changes).
# We use multiple workers to handle more users at once.
# WORKERS: Each worker can handle requests independently.
#   Think of workers like cashiers at a store — more workers = more customers served at once.
#   2 workers is fine for a small team; increase as your team grows.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
