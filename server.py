import multiprocessing
import asyncio
import json
import time

from fastapi import FastAPI, WebSocket

import Decorators
import JSONScrapper
import init
from HANDLERS import FILEHandler, LOGHandler, STATEHandler
from UTILS import parse

_proccess = None

app = FastAPI()


# @Decorators.log_decorator
async def search(search_requests):
    global _proccess

    FILEHandler.cleanLINKSAndJSONSDir()

    if _proccess is not None:
        stop()

    STATEHandler.setFlagEnd(False)

    _proccess = multiprocessing.Process(target=JSONScrapper.searchRequests, args=(search_requests,))
    _proccess.start()

    return f"Search({search_requests}) starting! "

#
#
#

# @Decorators.log_decorator
def getSearchFlagEnd():
    return {"flag_end": STATEHandler.getFlagEnd()}

# @Decorators.log_decorator
def getSearchLogProgressResult():
    return getSearchLog() | getSearchProgress() | getSearchResult()

# @Decorators.log_decorator
def getSearchLog():
    return {"logs": LOGHandler.getLogs()}

# @Decorators.log_decorator
def getSearchProgress():
    return {"progress": LOGHandler.getProgress()}

# @Decorators.log_decorator
def getSearchResult():
    output = parse.parseOutputFile(FILEHandler.getOutputText())
    return {"result": output}

# @Decorators.log_decorator
def stop():
    global _proccess

    if _proccess is not None:

        _proccess.terminate()
        time.sleep(0.1)
        if not _proccess.is_alive():
            _proccess.kill()

    return f"Stopped! Current proccess: {_proccess}"

# @Decorators.log_decorator
async def request_handler(request):
    if not "flag" in request:
        return "Некорректный запрос!"

    if request["flag"] == "SearchRequests":
        LOGHandler.splitLogs()
        await search(request["requests"])
        # asyncio.run(search(request["requests"]))
        return "Поиск начат!"

    elif request["flag"] == "StopSearch":
        stop()
        return "Поиск остановлен!"

    #
    #
    #

    elif request["flag"] == "GetSearchFlagEnd":
        return getSearchFlagEnd()

    elif request["flag"] == "GetSearchLog":
        return getSearchLog()

    elif request["flag"] == "GetSearchProgress":
        return getSearchProgress()

    elif request["flag"] == "GetSearchResult":
        return getSearchResult()

    elif request["flag"] == "GetSearchLogProgressResult":
        return getSearchLogProgressResult()

    return "Неизвестный тип операции!"


def send_format(json_data):
    return json.dumps(json_data, ensure_ascii=False)

@Decorators.log_decorator
def onOpen():
    # LOGHandler.logText("Connection open!")
    pass

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

        await websocket.send_json(answer)


async def debug():
    try:
        await request_handler({"flag": "SearchRequests", "requests": ["DONALDSON", "P550777"]})
    except Exception as E:
        pass


# КОМАНДА ЗАПУСКА
# uvicorn server:app --reload --port 5000 --host localhost

if __name__ == "__main__":
    init.init()
    asyncio.run(main())
    # asyncio.run(debug())


