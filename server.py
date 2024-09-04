import multiprocessing
import asyncio
import json
import time

from fastapi import FastAPI, WebSocket

import Decorators
import JSONScrapper

HOST = "localhost"
PORT = 8083

_proccess = None

app = FastAPI()


@Decorators.log_decorator
async def search(search_requests):
    global _proccess

    print(">> search()")

    if _proccess is not None:
        stop()

    _proccess = multiprocessing.Process(target=JSONScrapper.searchRequests, args=(search_requests,))
    _proccess.start()
    # _proccess.join()

    print("<< search()")


def getSearchProgress():
    return JSONScrapper.getSearchResults()


def stop():
    global _proccess

    if _proccess is not None:

        _proccess.terminate()
        time.sleep(0.1)
        if not _proccess.is_alive():
            _proccess.join()

        _proccess.kill()


@Decorators.log_decorator
async def request_handler(request):
    if not "flag" in request:
        return "Некорректный запрос!"

    if request["flag"] == "SearchRequests":
        await search(request["requests"])
        # asyncio.run(search(request["requests"]))
        return "Поиск начат!"

    elif request["flag"] == "StopSearch":
        stop()
        return "Поиск остановлен!"

    elif request["flag"] == "GetSearchProgress":
        return getSearchProgress()

    return "Неизвестный тип операции!"


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
        print("[DATA FROM FRONT] ", request)
        try:
            answer = await request_handler(request)
        except Exception as E:
            answer = {'error', E}
            pass
        print("[DATA FOR FRONT] ", answer)

        await websocket.send_json(answer)


# КОМАНДА ЗАПУСКА
# uvicorn server:app --reload --port 8083 --host localhost

if __name__ == "__main__":
    print("SERVER STARTING")
    asyncio.run(main())
    # uvicorn.run(app, host=HOST, port=PORT)
