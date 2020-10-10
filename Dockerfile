FROM python:3.7.7
LABEL Author="Thrivikram Mudunuri"
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt 
ENV PORT 8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 90 wsgi:app