import atexit
import multiprocessing

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from HANDLERS.ERRORHandler import Error
from HANDLERS import LOGHandler
from PROVIDERS.Provider import ProviderHandler, Provider

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

from HANDLERS import FILEHandler as fHandler

import Decorators

_THREADS_LIMIT = 4
_process_list = []
_error = None


class WebWorker:
    _provider_name = ""
    _provider_code = None
    _search_request = ""

    _provider = None

    def __init__(self, provider_code, request):
        self._provider_name = ProviderHandler().getProviderNameByCode(provider_code)
        self._provider_code = provider_code
        self._search_request = request

        self._provider = self.getProvider()

        fHandler.createLINKSDir(self._provider_name)
        fHandler.createJSONSDir(self._provider_name)

    def __del__(self):
        cleanup("__del__()")


    @Decorators.log_decorator
    def getProvider(self) -> Provider:
        LOGHandler.logInfo(f"САЙТ-ПРОИЗВОДИТЕЛЬ: {self._provider_name.upper()}")
        return getProvider(self._provider_code)

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
        getArticleLINKSByThreads(self._provider_code, self._search_request, max_page)
        if _error is not None:
            return _error

        # Генерируем JSONS
        generateJSONSbyThreads(self._provider_code, self._search_request)
        if _error is not None:
            return _error

        return Error.SUCCESS


#
# UTILITIES
#

def getProvider(_provider_code) -> Provider:
    return ProviderHandler().getProviderByProviderCode(_provider_code)()

def cleanup(text=""):
    global _process_list
    proccess_count = len(_process_list)
    for process in _process_list:
        process.kill()
    _process_list = []
    text = f"{text}{':' if len(text) >= 0 else ''} "
    print(f'{text}{proccess_count} proccess cleaned up!')

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


@Decorators.log_decorator
def getBrowser():
    # service = ChromeDriverService.CreateDefaultService()
    # service.EnableVerboseLogging = true;
    #
    # webDriver = new
    # ChromeDriver(service, options);

    options = webdriver.ChromeOptions()
    options.add_experimental_option(
        "prefs", {
            # не загружаем видео, стили и изображения
            'profile.managed_default_content_settings.images': 2,
            'profile.managed_default_content_settings.media_stream': 2,
            'profile.managed_default_content_settings.stylesheets': 2
        },
    )
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')

    # https://stackoverflow.com/questions/29858752/error-message-chromedriver-executable-needs-to-be-available-in-the-path/52878725#52878725
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=options, service=service)
    return driver


def getCountThreads(count_elements):
    if count_elements // _THREADS_LIMIT > 0:
        return _THREADS_LIMIT
    else:
        return count_elements


@Decorators.time_decorator
@Decorators.log_decorator
def getArticleLINKSByThreads(_provider_code, _search_request, max_page):
    global _process_list

    _provider = getProvider(_provider_code)

    # Определяем количество потоков
    count_threads = getCountThreads(max_page)

    # Если HiFi то...
    if _provider.getName() == "HIFI":
        getLINKSbyPage(range(0, max_page))

    elif _provider.getName() == "FLEETGUARD":
        saveArticles(_provider.parseSearchResult(None), _search_request, _provider.getName())

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
        _process_list = []
        for i in range(0, count_threads):
            process = multiprocessing.Process(target=getLINKSbyPage,
                                              args=(_provider_code, _search_request, _provider.getName(), pages[i],))
            process.start()
            _process_list.append(process)
        for process in _process_list:
            process.join()

        cleanup("getArticleLINKSByThreads()")

    return


@Decorators.time_decorator
@Decorators.error_decorator
@Decorators.log_decorator
def getLINKSbyPage(_provider_code, _search_request, _catalogue_name, pages):
    _provider = getProvider(_provider_code)

    # ПОИСК БРАУЗЕРА ДЛЯ ИСПОЛЬЗОВАНИЯ
    driver = getBrowser()
    if driver is None:
        _error = Error.UNDEFIND_CHROME_DRIVER
        return Error.UNDEFIND_CHROME_DRIVER

    for page in pages:

        if _provider.getName() == "MANN":
            if page >= _provider.max_page_search:
                break

        if _provider.getName() == "MANN":
            a = _provider.searchProducts(driver, page, _search_request)
        else:
            a = _provider.search(driver, page, _search_request)

        if not a:
            _error = Error.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
            return Error.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

        articles = _provider.parseSearchResult(driver, page)
        if len(articles) > 0:
            saveArticles(articles, _search_request, _catalogue_name)

    if _provider.getName() == "MANN":

        for page in pages:

            if page >= _provider.max_page_cross_ref:
                break

            a = _provider.searchCrossRef(driver, page, _search_request)
            if not a:
                _error = Error.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
                return Error.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

            articles = _provider.parseCrossReferenceResult(driver, page)
            if len(articles) > 0:
                saveArticles(articles, _search_request, _catalogue_name)

    driver.close()
    driver.quit()

    return Error.SUCCESS


@Decorators.time_decorator
@Decorators.log_decorator
def generateJSONSbyThreads(_provider_code, _search_request):
    global _process_list

    _provider = getProvider(_provider_code)

    count_lines = fHandler.getCountLINKSLines(_provider.getName(), f"{_search_request}.txt")

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
    _process_list = []
    for index in range(0, count_threads):
        process = multiprocessing.Process(target=parseLINKS,
                                          args=(parts[index][0], parts[index][1], _provider_code, _search_request))
        process.start()
        _process_list.append(process)
    for process in _process_list:
        process.join()

    cleanup("generateJSONSbyThreads()")



@Decorators.time_decorator
@Decorators.error_decorator
@Decorators.log_decorator
def parseLINKS(start_line, end_line, _provider_code, search_request):
    provider = getProvider(_provider_code)

    # ПОИСК БРАУЗЕРА ДЛЯ ИСПОЛЬЗОВАНИЯ
    driver = getBrowser()
    if driver is None:
        _error = Error.UNDEFIND_CHROME_DRIVER
        return Error.UNDEFIND_CHROME_DRIVER

    articles = fHandler.getLINKSfromFileByLines(provider.getName(), search_request, start_line, end_line)

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

        fHandler.appendJSONToFile(provider.getName(), article_json, search_request)
        LOGHandler.logInfo(f'{article[0]} -- взят JSON!')

    driver.close()
    driver.quit()

    return 0



@Decorators.log_decorator
def saveArticles(articles, _search_request, _catalogue_name):

    for article in articles:
        LOGHandler.logInfo(f"{article[0]} - найден!")

        if len(article) == 4:
            fHandler.appendLINKtoFile(_catalogue_name,
                                      article[0] + " " + article[1] + " " + article[2] + " " + article[3],
                                      _search_request)
        elif len(article) == 3:
            fHandler.appendLINKtoFile(_catalogue_name, article[0] + " " + article[1] + " " + article[2],
                                      _search_request)
        else:
            fHandler.appendLINKtoFile(_catalogue_name, article[0] + " " + article[1], _search_request)
