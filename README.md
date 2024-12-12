## Запуск сервера:
uvicorn server:app --reload --port 8083 --host localhost

docker-compose -f docker-compose-chrome-selenium.yml up --detach 
