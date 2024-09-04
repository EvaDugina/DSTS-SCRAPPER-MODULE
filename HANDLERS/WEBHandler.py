import threading

from loguru import logger
from selenium import webdriver

import PROVIDERS.Provider
from HANDLERS.ERRORHandler import Error
from PROVIDERS.Provider import ProviderHandler, Providers, Provider

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

from HANDLERS import FILEHandler as fHandler, DBHandler as db, JSONHandler
from UTILS import strings
import Decorators

_THREADS_LIMIT = 4

_provider = None
_search_request = ""
_catalogue_name = ""

_error = None


class WebWorker:
    _provider_name = ""
    _provider_code = None
    _search_request = ""

    _provider = None
    _dbHandler = None

    def __init__(self, provider_code, request):
        self._provider_name = ProviderHandler().getProviderNameByCode(provider_code)
        self._provider_code = provider_code
        self._search_request = request
        self._dbHandler = db.DBWorker()

        self._provider = self.getProvider()

        fHandler.createLINKSDir(self._provider_name)
        fHandler.createJSONSDir(self._provider_name)

    @Decorators.log_decorator
    def getProvider(self) -> Provider:

        logger.info(f"САЙТ-ПРОИЗВОДИТЕЛЬ: {self._provider_name.upper()}")
        producer_id = self._dbHandler.insertProducer(self._provider_name, self._provider_name)

        provider = ProviderHandler().getProviderByProviderCode(self._provider_code)(producer_id, self._dbHandler)

        return provider

    @Decorators.time_decorator
    @Decorators.error_decorator
    @Decorators.log_decorator
    def pullCrossRefToDB(self):

        checkInternetConnection(self._provider.getMainUrl())

        # ПОЛУЧАЕМ КОЛИЧЕСТВО СТРАНИЦ
        driver = getBrowser()
        if driver is None:
            return Error.UNDEFIND_CHROME_DRIVER
        max_page = self._provider.getPageCount(driver, self._search_request)
        driver.close()
        driver.quit()

        if max_page == -1:
            return Error.FIND_NOTHING
        else:
            if max_page == 0:
                max_page = 1
            else:
                max_page = int(max_page)

        # Вытаскиваем ссылки на элементы
        self.getArticleLINKSByThreads(max_page)
        if _error is not None:
            return _error

        # Генерируем JSONS
        self.generateJSONSbyThreads()
        if _error is not None:
            return _error

        return Error.SUCCESS

    @Decorators.time_decorator
    @Decorators.log_decorator
    def generateJSONSbyThreads(self):

        count_lines = fHandler.getCountLINKSLines(self._provider_name, f"{self._search_request}.txt")

        # Определяем количество потоков
        count_threads = getCountThreads(count_lines)

        # Распределяем ссылки (части файла) по потокам
        parts = []
        count_lines_in_part = count_lines // count_threads
        offset = 0
        if count_lines // count_threads != 0:
            for i in range(0, count_threads):
                start_index = i * count_lines_in_part + offset
                if i < count_lines % count_threads:
                    offset += 1
                end_index = (i + 1) * count_lines_in_part + offset
                parts.append([start_index, end_index])

        # Запускаем потоки
        tasks = []
        from gevent import monkey
        monkey.patch_all()
        for index in range(0, count_threads):
            tasks.append(threading.Thread(target=parseLINKS, args=(
            parts[index][0], parts[index][1], self._provider, self._search_request)))
        for i in range(0, count_threads):
            tasks[i].start()
        for i in range(0, count_threads):
            tasks[i].join()

    @Decorators.time_decorator
    @Decorators.log_decorator
    def getArticleLINKSByThreads(self, max_page):

        setGlobals(self._provider, self._search_request)
        setGlobalCatalogueName(self._provider_name)

        # Определяем количество потоков
        count_threads = getCountThreads(max_page)

        # Если HiFi то...
        if self._provider_name == "HIFI":
            getLINKSbyPage(range(0, max_page))

        elif self._provider_name == "FLEETGUARD":
            saveArticles(self._provider.parseSearchResult(None))

        else:

            pages = []
            for j in range(0, count_threads):
                pages.append([])

            # Распределяем страницы между потоками
            for i in range(0, max_page // count_threads * count_threads, count_threads):
                for j in range(0, count_threads):
                    pages[j].append(i + j)
            if max_page % count_threads != 0:
                for i in range((max_page // count_threads) * count_threads, max_page):
                    pages[i % _THREADS_LIMIT].append(i)

            # Запускаем потоки
            tasks = []
            for i in range(0, count_threads):
                tasks.append(threading.Thread(target=getLINKSbyPage, args=(pages[i],)))
            for index, thread in enumerate(tasks):
                thread.start()
            for thread in tasks:
                thread.join()

        return


#
# Вспомогательные функции
#

@Decorators.time_decorator
@Decorators.error_decorator
@Decorators.log_decorator
def checkInternetConnection(url='http://www.google.com/'):
    # ПРОВЕРКА ИНТЕРНЕТ СОЕДИНЕНИЯ
    try:
        from urllib import request
        request.urlopen(url)
        return Error.SUCCESS
    except:
        return Error.INTERNET_CONNECTION


def setGlobals(provider, search_request):
    global _provider, _search_request
    _provider = provider
    _search_request = search_request


def setGlobalCatalogueName(catalogue_name):
    global _catalogue_name
    _catalogue_name = catalogue_name


@Decorators.log_decorator
def getBrowser():
    options = webdriver.ChromeOptions()
    options.add_experimental_option(
        "prefs", {
            # не загружаем видео, стили и изображения
            'profile.managed_default_content_settings.images': 2,
            'profile.managed_default_content_settings.media_stream': 2,
            'profile.managed_default_content_settings.stylesheets': 2
        }
    )
    driver = webdriver.Chrome(
        options=options
    )
    return driver


def getCountThreads(count_elements):
    if count_elements // _THREADS_LIMIT > 0:
        return _THREADS_LIMIT
    else:
        return count_elements


@Decorators.time_decorator
@Decorators.error_decorator
@Decorators.log_decorator
def getLINKSbyPage(pages):
    global _provider, _search_request, _catalogue_name

    # ПОИСК БРАУЗЕРА ДЛЯ ИСПОЛЬЗОВАНИЯ
    driver = getBrowser()
    if driver is None:
        _error = Error.UNDEFIND_CHROME_DRIVER
        return Error.UNDEFIND_CHROME_DRIVER

    for page in pages:

        if _provider.getCatalogueName() == "MANN":
            if page >= _provider.max_page_search:
                break

        if _provider.getCatalogueName() == "MANN":
            a = _provider.searchProducts(driver, page, _search_request)
        else:
            a = _provider.search(driver, page, _search_request)

        if not a:
            _error = Error.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
            return Error.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

        articles = _provider.parseSearchResult(driver, page)
        if len(articles) > 0:
            saveArticles(articles)

    if _provider.getCatalogueName() == "MANN":

        for page in pages:

            if page >= _provider.max_page_cross_ref:
                break

            a = _provider.searchCrossRef(driver, page, _search_request)
            if not a:
                _error = Error.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
                return Error.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

            articles = _provider.parseCrossReferenceResult(driver, page)
            if len(articles) > 0:
                saveArticles(articles)

    driver.close()
    driver.quit()

    return Error.SUCCESS


@Decorators.log_decorator
def saveArticles(articles):
    global _search_request, _catalogue_name

    for article in articles:
        logger.info(f"{article[0]} - найден!")

        if len(article) == 4:
            fHandler.appendLINKtoFile(_catalogue_name,
                                      article[0] + " " + article[1] + " " + article[2] + " " + article[3],
                                      _search_request)
        elif len(article) == 3:
            fHandler.appendLINKtoFile(_catalogue_name, article[0] + " " + article[1] + " " + article[2],
                                      _search_request)
        else:
            fHandler.appendLINKtoFile(_catalogue_name, article[0] + " " + article[1], _search_request)


@Decorators.time_decorator
@Decorators.error_decorator
@Decorators.log_decorator
def parseLINKS(start_line, end_line, provider, search_request):
    # provider = self.getProvider()

    # ПОИСК БРАУЗЕРА ДЛЯ ИСПОЛЬЗОВАНИЯ
    driver = getBrowser()
    if driver is None:
        _error = Error.UNDEFIND_CHROME_DRIVER
        return Error.UNDEFIND_CHROME_DRIVER

    articles = fHandler.getLINKSfromFileByLines(provider.getCatalogueName(), search_request, start_line, end_line)

    # Проходимся по линиям в файле
    for article in articles:

        # Загружаем страницу артикула по ссылке
        driver = provider.loadArticlePage(driver, article[1])
        type = provider.getArticleType(driver)
        if not driver:
            _error = Error.UNLOAD_ARTICLE_PAGE
            return Error.UNLOAD_ARTICLE_PAGE

        # Вытаскиваем аналоги
        analog_article_name = ""
        analog_producer_name = ""
        if len(article) == 4:
            analog_article_name = article[2]
            analog_producer_name = article[3]
        elif len(article) == 3:
            analog_article_name = article[2]

        # Формируем JSON
        article_json = provider.saveJSON(driver, article[1], article[0], type, search_request, analog_article_name,
                                         analog_producer_name)

        fHandler.appendJSONToFile(provider.getCatalogueName(), article_json, search_request)
        logger.success(f'{article[0]} -- взят JSON!')

    driver.close()
    driver.quit()

    return 0
