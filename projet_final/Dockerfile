FROM python:3.10

RUN apt-get update && apt-get install -y portaudio19-dev python3-pyaudio libasound2-dev

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "projet_final.wsgi:application", "--bind", "0.0.0.0:8000"]