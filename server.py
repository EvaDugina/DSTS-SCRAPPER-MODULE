import multiprocessing
import websockets
import asyncio
import json
from fastapi import FastAPI, WebSocket
import uvicorn
from loguru import logger

import Decorators
import JSONScrapper
import init

HOST = "localhost"
PORT = 8083

_proccess = None

app = FastAPI()


@Decorators.log_decorator
def start_search(search_requests):
    global _proccess

    if _proccess is not None:
        stop_search()

    # init.init()
    # logger.debug(search_requests)

    # JSONScrapper.searchRequests(search_requests)

    _proccess = multiprocessing.Process(target=JSONScrapper.searchRequests, args=(search_requests, ))
    _proccess.start()
    _proccess.join()

    print("<< start_search()")


def stop_search():
    global _proccess

    if _proccess is not None and _proccess.is_alive():
        _proccess.kill()


@Decorators.log_decorator
def request_handler(request):
    if not "flag" in request:
        return "Некорректный flag!"

    if request["flag"] == "searchRequests":
        start_search(request["requests"])
        return "Поиск окончен!"

    elif request["flag"] == "stopSearch":
        stop_search()
        return "Поиск остановлен!"

    return "Неизвестный flag!"


def send_format(json_data):
    return json.dumps(json_data, ensure_ascii=False)


@app.websocket('/')
async def main(websocket: WebSocket):
    await websocket.accept()
    while True:
        print("SERVER ON")

        # получаем сообщение от клиента
        message = await websocket.receive_json()

        # преобразуем json к словарю для удобной обработки
        request = dict(message)
        print("\n\n\t[DATA FROM FRONT] ", request)
        answer = {}
        try:
            answer = request_handler(request)
        except Exception as E:
            answer = {'error', E}
            pass
        print("\t[DATA FOR FRONT] ", answer)

        await websocket.send_json(answer)


# КОМАНДА ЗАПУСКА
# uvicorn server:app --reload --port 8083 --host localhost

if __name__ == "__main__":
    asyncio.run(main())
    # uvicorn.run(app, host=HOST, port=PORT)
