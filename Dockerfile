FROM python:3.11-slim (last pushed 1 week ago)

WORKDIR /app

COPY . .
RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "app/app.py"]