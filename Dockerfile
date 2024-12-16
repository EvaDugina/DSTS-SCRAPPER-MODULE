FROM selenium/standalone-chrome:4.27

WORKDIR ./python_scrapper

USER root
COPY requirements.txt ./
RUN python3 -m pip install -r requirements.txt --break-system-packages

COPY . .

EXPOSE 5000

CMD ["uvicorn", "server:app", "--reload", "--port", "5000", "--host", "0.0.0.0"]


