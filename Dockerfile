FROM python:3.12-alpine
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple && rm -f requirements.txt
ENTRYPOINT ["python", "manage.py", "runserver","0:8000"]