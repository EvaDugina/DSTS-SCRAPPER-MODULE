#!/usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum

# НЕ МОЖЕТ БЫТЬ ДЕКОРАТОРОВ, ТК ДЕКОРАТОРЫ ИСПОЛЬЗУЮТ ЕГО!!
from HANDLERS import LOGHandler


class Error(Enum):
    SUCCESS = 0
    FIND_NOTHING = 0
    NOTHING_TO_SEARCH = 100
    INTERNET_CONNECTION = 101
    UNDEFIND_CHROME_DRIVER = 102
    UNLOAD_ARTICLE_PAGE = 201
    INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE = 300
    NOTHING_TO_PARSE = 400
    DB_ERROR = 500


class ErrorHandler:

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

        text = f"{function_name}() | {error_text}"
        LOGHandler.logError(text)

        exit(error_code)

