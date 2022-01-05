FROM python:3.7

RUN python -m pip install --upgrade pip

WORKDIR /app
COPY ./techtrends/ /app

RUN pip install -r requirements.txt
RUN python init_db.py

EXPOSE 3111
CMD ["python", "app.py"]