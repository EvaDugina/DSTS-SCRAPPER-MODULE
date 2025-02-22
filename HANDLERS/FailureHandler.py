#!/usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum

from HANDLERS import LOGHandler

class Error(Enum):
    FIND_NOTHING = 0
    NOTHING_TO_SEARCH = 100
    INTERNET_CONNECTION = 101
    UNDEFIND_CHROME_DRIVER = 102
    UNLOAD_ARTICLE_PAGE = 201
    INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE = 300
    NOTHING_TO_PARSE = 400
    DB_ERROR = 500


class Warning(Enum):
    CLEAN_LINKS_AND_JSONS = 1


class FailureHandler:

    def handleError(self, error_code, function_name):

        if error_code == Error.NOTHING_TO_SEARCH:
            error_text = "ОШИБКА! Пустой запрос поиска!"
        elif error_code == Error.INTERNET_CONNECTION:
            error_text = "ОШИБКА! Отсутствует интернет-соединение!"
        elif error_code == Error.UNDEFIND_CHROME_DRIVER:
            error_text = "ОШИБКА! Не найден ChromeDriver! Отсутствует браузер для поиска!"
        elif error_code == Error.UNLOAD_ARTICLE_PAGE:
            error_text = "ОШИБКА! Невозможно загрузить страницу товара!"
        elif error_code == Error.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE:
            error_text = "Ошибка! Некорректная ссылка или изменилась структура сайта!"
        elif error_code == Error.NOTHING_TO_PARSE:
            error_text = "Ошибка! Отсутствуют элементы для добавления в базу данных!"
        elif error_code == Error.DB_ERROR:
            error_text = "Ошибка! Сбой в работе с базой данных!"
        else:
            error_text = error_code

        LOGHandler.logError(f"{function_name}() | {error_text}")

        exit(error_code)

    def handleWarning(self, warning_code, warnings, function_name):

        if warning_code == Warning.CLEAN_LINKS_AND_JSONS:
            warning_text = "Предупреждение. Не удалось удалить используемые папки."
        else:
            warning_text = warning_code

        LOGHandler.logWarning(f"{function_name}() | {warning_text}")

        if len(warnings) > 0:
            for text in warnings:
                LOGHandler.logText(text)


