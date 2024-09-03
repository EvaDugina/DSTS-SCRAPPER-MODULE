#!/usr/bin/env python

from gevent import monkey

import datetime
import json
import threading

from loguru import logger

import Decorators
import init
from HANDLERS import WEBHandler as wHandler
from HANDLERS import FILEHandler as fHandler
from HANDLERS import DBHandler as dbHandler
from HANDLERS.ERRORHandler import Error
from PROVIDERS.Provider import ProviderHandler

_search_request = ""
_catalogue_name = ""
_dbHandler = None

_flag_has_error = False


@Decorators.time_decorator
@Decorators.error_decorator
@Decorators.log_decorator
def parseJSONSbyThreads(catalogue_name, search_request):

    global _catalogue_name, _search_request

    _catalogue_name = catalogue_name
    _search_request = search_request

    count_lines = fHandler.getCountJSONSLines(_catalogue_name, f"{_search_request}.txt")

    # Определяем количество потоков
    count_threads = wHandler.getCountThreads(count_lines)

    # Распределяем ссылки (части файла) по потокам
    parts = []
    count_lines_in_part = count_lines // count_threads
    offset = 0
    if count_lines // count_threads > 0:
        for i in range(0, count_threads):
            start_index = i * count_lines_in_part + offset
            if i < count_lines % count_threads:
                offset += 1
            end_index = (i + 1) * count_lines_in_part + offset
            parts.append([start_index, end_index])

    # Запускаем потоки
    tasks = []
    monkey.patch_all()
    for i in range(0, count_threads):
        tasks.append(threading.Thread(target=parseJSONS, args=(parts[i][0], parts[i][1])))
    for i in range(0, count_threads):
        tasks[i].start()
    for i in range(0, count_threads):
        tasks[i].join()

    if _flag_has_error:
        return Error.DB_ERROR

    return Error.SUCCESS


@Decorators.time_decorator
@Decorators.log_decorator
def parseJSONS(start_line, end_line):
    global _dbHandler

    json_lines = fHandler.getJSONSfromFileByLines(_catalogue_name, _search_request, start_line, end_line)

    for line_json in json_lines:
        line_json = json.loads(line_json)
        article_name = line_json['name']
        catalogue_name = line_json['catalogue_name']
        producer_name = line_json['producer_name']

        parseJSON(article_name, producer_name, line_json['type'], line_json['info'], catalogue_name)

    return 0


@Decorators.error_decorator
@Decorators.log_decorator
def parseJSON(main_article_name, main_producer_name, type, json_info, catalogue_name):
    global _dbHandler, _flag_has_error

    import psycopg2
    try:
        main_producer_id = _dbHandler.insertProducer(main_producer_name, catalogue_name)
        # print("----> PRODUCER_ID: " + str(main_producer_id))

        main_article_id = _dbHandler.insertArticle(main_article_name, main_producer_id, catalogue_name,
                                                   convertTypeToDigits(type))
    except psycopg2.Error as err:
        logger.error(err)
        _flag_has_error = True
        exit()

    fHandler.appendToFileOutput(f'{catalogue_name}|{main_article_name}|{main_producer_name}')

    cross_ref = json_info['crossReference']
    parseCrossReference(_dbHandler, catalogue_name, cross_ref, main_article_id)
    del json_info['crossReference']

    parseInfo(_dbHandler, catalogue_name, json_info, main_article_id, main_article_name)


@Decorators.error_decorator
@Decorators.log_decorator
def parseCrossReference(_dbHandler, catalogue_name, cross_ref, main_article_id):
    global _flag_has_error

    for elem in cross_ref:
        producer_name = elem['producerName']
        # print("\t--> PRODUCER_NAME: " + str(producer_name))

        import psycopg2
        try:
            producer_id = _dbHandler.insertProducer(producer_name, catalogue_name)
            analog_article_names = elem['articleNames']
            analog_article_ids = []
            for article_name in analog_article_names:
                analog_article_id = _dbHandler.insertArticle(article_name, producer_id, catalogue_name,
                                                             convertTypeToDigits(elem['type']))
                analog_article_ids.append(analog_article_id)
            _dbHandler.insertArticleAnalogs(main_article_id, analog_article_ids, catalogue_name)
        except psycopg2.Error as err:
            logger.error(err)
            _flag_has_error = True
            exit()

        for analog_article_name in analog_article_names:
            fHandler.appendToFileOutput(f'> {analog_article_name}|{producer_name}')


@Decorators.log_decorator
def parseInfo(_dbHandler, catalogue_name, json_info, main_article_id, main_article_name):

    _dbHandler.insertCharacteristics(json_info['articleMainInfo'])
    url = f"{ProviderHandler().getArticleBaseURLbyProviderName(catalogue_name, main_article_name)}/{json_info['articleSecondaryInfo']['articleId']}"
    _dbHandler.insertArticleInfo(main_article_id, catalogue_name, url, json_info['articleDescription'].upper(), json_info)



def convertTypeToDigits(type):
    if type == "old":
        return 1
    else:
        return 0

@Decorators.error_decorator
def main():
    init.init()

    _dbHandler = dbHandler.DBWorker()

    logger.debug("JSONParser.py")
    elements = fHandler.getElementsForParse()

    if len(elements) < 1:
        return Error.NOTHING_TO_PARSE

    for elem in elements:
        catalogue_name = elem[0]
        search_request = elem[1]

        parseElement(catalogue_name, search_request)


@Decorators.error_decorator
def parseElements(elements):
    # init.init()
    _dbHandler = dbHandler.DBWorker()

    logger.debug("parseElements()")

    if len(elements) < 1:
        return Error.NOTHING_TO_PARSE

    for elem in elements:
        catalogue_name = elem[0]
        search_request = elem[1]

        parseElement(catalogue_name, search_request)


def parseElement(catalogue_name, search_request):
    logger.debug(">>>> SEARCH REQUEST: " + search_request)
    parseJSONSbyThreads(catalogue_name, search_request)
    fHandler.moveJSONToCompleted(catalogue_name, search_request)
    logger.debug("<<<< SEARCH REQUEST: " + search_request)


if __name__ == "__main__":
    main()
