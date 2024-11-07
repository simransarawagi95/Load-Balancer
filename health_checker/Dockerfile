FROM python:3.13-slim

WORKDIR /app
COPY health_checker.py ./
COPY requirements.txt /app/
RUN pip install -r requirements.txt


CMD ["python", "health_checker.py"]
