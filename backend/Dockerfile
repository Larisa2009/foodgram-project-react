FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

WORKDIR /app/foodgram

RUN python manage.py makemigrations users

RUN python manage.py migrate

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]