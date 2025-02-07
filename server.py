import multiprocessing
import asyncio
import json
import time

from fastapi import FastAPI, WebSocket

import Decorators
import JSONScrapper
import init
from HANDLERS import FILEHandler, LOGHandler
from UTILS import parse

# HOST = "localhost"
# PORT = 8083

_proccess = None

app = FastAPI()


@Decorators.log_decorator
async def search(search_requests):
    global _proccess

    LOGHandler.splitLogs()
    FILEHandler.cleanLINKSAndJSONSDir()

    if _proccess is not None:
        stop()
        stop()

    JSONScrapper.FLAG_END = False

    _proccess = multiprocessing.Process(target=JSONScrapper.searchRequests, args=(search_requests,))
    _proccess.start()

    return f"Search({search_requests}) starting! "

@Decorators.log_decorator
def getSearchOutput():
    output = parse.parseOutputFile(FILEHandler.getOutputText())
    flag_end = JSONScrapper.FLAG_END
    return {"flag_end": flag_end, "output": output}

@Decorators.log_decorator
def getSearchProgress():
    output = LOGHandler.getProgressLog()
    flag_end = JSONScrapper.FLAG_END
    return {"flag_end": flag_end, "progress": output}

@Decorators.log_decorator
def getSearchLog():
    return {"logs": LOGHandler.getLogs()}

@Decorators.log_decorator
def stop():
    global _proccess

    if _proccess is not None:

        _proccess.terminate()
        time.sleep(0.1)
        if not _proccess.is_alive():
            _proccess.join()

        _proccess.kill()
        _proccess.kill()

    return f"Stopped! Current proccess: {_proccess}"

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

    elif request["flag"] == "GetSearchLog":
        return getSearchLog()

    return "Неизвестный тип операции!"


def send_format(json_data):
    return json.dumps(json_data, ensure_ascii=False)

@Decorators.log_decorator
def onOpen():
    print("SERVER ON")

@app.websocket('/')
async def main(websocket: WebSocket):
    await websocket.accept()
    onOpen()
    while True:
        # получаем сообщение от клиента
        message = await websocket.receive_json()

        # преобразуем json к словарю для удобной обработки
        request = dict(message)

        try:
            answer = await request_handler(request)
        except Exception as E:
            answer = {'error', E}
            pass

        LOGHandler.logText(answer)

        await websocket.send_json(answer)


# КОМАНДА ЗАПУСКА
# uvicorn server:app --reload --port 5000 --host localhost

if __name__ == "__main__":
    init.init()
    asyncio.run(main())
