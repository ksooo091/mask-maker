FROM python:3.9-slim AS build
WORKDIR /app


COPY requirements.txt .
RUN pip3 install --target=/app/dependencies -r requirements.txt

FROM python:3.9-slim
WORKDIR /app

COPY --from=build	/app .
ENV PYTHONPATH="${PYTHONPATH}:/app/dependencies"
#COPY config.ini .
COPY main.py .
ENTRYPOINT ["python", "main.py"]
