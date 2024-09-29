FROM python:3.11

ENV PYTHONBUFFERED 1

WORKDIR /server

COPY requirements.txt /server/

RUN pip install -r requirements.txt

COPY . /server/

EXPOSE 8000

CMD ["python3 manage.py makemigrations user && python3 manage.py migrate user && python3 manage.py makemigrations api && python3 manage.py migrate api && python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8000"]
