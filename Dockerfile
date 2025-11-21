FROM python:3.12-alpine
WORKDIR /app
RUN pip install -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple
COPY . .
ENTRYPOINT ["python", "manage.py", "runserver","0:8000"]