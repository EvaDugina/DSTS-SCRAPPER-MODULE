import threading

from selenium import webdriver
from Error import Error
from PROVIDERS.Provider import ProviderHandler, Providers

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
_thread_results = []


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
        self._dbHandler = db.DBWorker('5432')

        self._provider = self.getProvider()

        fHandler.createLINKSDir(self._provider_name)
        fHandler.createJSONSDir(self._provider_name)


    def getProvider(self):
        fHandler.appendToFileLog(f"ПО САЙТУ-ПРОИЗВОДИТЕЛЮ: {self._provider_name.upper()}")
        producer_id = self._dbHandler.insertProducer(self._provider_name, self._provider_name)

        provider = ProviderHandler().getProviderByProviderCode(self._provider_code)(producer_id, self._dbHandler)

        return provider


    @Decorators.time_decorator
    def pullCrossRefToDB(self):

        if not checkInternetConnection(self._provider.getMainUrl()):
            return Error.INTERNET_CONNECTION

        print("----> pullCrossRefToDB() ")

        # ПОЛУЧАЕМ КОЛИЧЕСТВО СТРАНИЦ
        driver = None
        if not self._provider_name == "HIFI":
            driver = getBrowser()
            if driver is None:
                print("#### ОШИБКА! Не найден браузер")
                return Error.UNDEFIND_BROWSER

        max_page = self._provider.getPageCount(driver, self._search_request)

        if not self._provider_name == "HIFI":
            driver.close()
            driver.quit()

        if max_page == -1:
            return Error.FIND_NOTHING
        else:
            if max_page == 0:
                max_page = 1
            else:
                max_page = int(max_page)

        print("\n")


        # Вытаскиваем ссылки на элементы
        self.getArticleLINKSByThreads(max_page)

        # Генерируем JSONS
        self.generateJSONSbyThreads()

        fHandler.moveLINKToCompleted(self._provider_name, self._search_request)

        return Error.SUCCESS


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
                end_index = (i+1) * count_lines_in_part + offset
                parts.append([start_index, end_index])

        # Запускаем потоки
        tasks = []
        for index in range(0, count_threads):
            tasks.append(threading.Thread(target=parseLINKS, args=(parts[index][0], parts[index][1], self._provider, self._search_request)))
        for i in range(0, count_threads):
            tasks[i].start()
        for i in range(0, count_threads):
            tasks[i].join()


    def getArticleLINKSByThreads(self, max_page):
        setGlobals(self._provider, self._search_request)
        setGlobalCatalogueName(self._provider_name)

        # Определяем количество потоков
        if max_page != 0:
            count_threads = getCountThreads(max_page)
        else:
            return ""

        # Если HiFi то...
        if self._provider_name == "HIFI":
            _thread_results.append(list())
            getLINKSbyPage(0, range(0, max_page))

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
                _thread_results.append(list())
                tasks.append(threading.Thread(target=getLINKSbyPage, args=(i, pages[i],)))
            for index, thread in enumerate(tasks):
                thread.start()
            for thread in tasks:
                thread.join()

        return


#
# Вспомогательные функции
#

@Decorators.time_decorator
def checkInternetConnection(url='http://www.google.com/'):
    # ПРОВЕРКА ИНТЕРНЕТ СОЕДИНЕНИЯ
    try:
        from urllib import request
        request.urlopen(url)
        return True
    except:
        print("#### ОШИБКА! Отсутствует интернет-соединение")

    return False


def setGlobals(provider, search_request):
    global _provider, _search_request
    _provider = provider
    _search_request = search_request


def setGlobalCatalogueName(catalogue_name):
    global _catalogue_name
    _catalogue_name = catalogue_name


def getBrowser():
    driver = None

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


def getLINKSbyPage(thread_id, pages):
    global _provider, _search_request, _catalogue_name

    # ПОИСК БРАУЗЕРА ДЛЯ ИСПОЛЬЗОВАНИЯ
    driver = None
    if not _catalogue_name == "HIFI":
        driver = getBrowser()
        if driver is None:
            print("#### ОШИБКА! Не найден браузер")
            return strings.UNDEFIND_BROWSER

    for page in pages:

        if _provider.getCatalogueName() == "MANN":
            if page >= _provider.max_page_search:
                break

        if _provider.getCatalogueName() == "MANN":
            a = _provider.searchProducts(driver, page, _search_request)
        else:
            a = _provider.search(driver, page, _search_request)

        if not a:
            return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

        articles = _provider.parseSearchResult(driver, page)
        if len(articles) < 1:
            fHandler.appendLINKtoFile(_catalogue_name, "", _search_request)
            return "ОТСУТСВУЮТ РЕЗУЛЬТАТЫ ПОИСКА"

        saveArticles(articles)


    if _provider.getCatalogueName() == "MANN":

        for page in pages:

            if page >= _provider.max_page_cross_ref:
                break

            a = _provider.searchCrossRef(driver, page, _search_request)
            if not a:
                return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

            articles = _provider.parseCrossReferenceResult(driver, page)
            if len(articles) < 1:
                fHandler.appendLINKtoFile(_catalogue_name, "", _search_request)
                return "ОТСУТСВУЮТ РЕЗУЛЬТАТЫ ПОИСКА"

            saveArticles(articles)



    # AttributeError: 'NoneType' object has no attribute 'close'
    # Exception in thread Thread-9 (getLINKSbyPage):
    if not _catalogue_name == "HIFI":
        driver.close()
        driver.quit()

    return "ССЫЛКИ ВЫТАЩЕНЫ УСПЕШНО!"


def saveArticles(articles):
    global _search_request, _catalogue_name

    for article in articles:
        print(f"{article[0]} - найден!")

        if len(article) == 4:
            fHandler.appendLINKtoFile(_catalogue_name,
                                      article[0] + " " + article[1] + " " + article[2] + " " + article[3],
                                      _search_request)
        elif len(article) == 3:
            fHandler.appendLINKtoFile(_catalogue_name, article[0] + " " + article[1] + " " + article[2],
                                      _search_request)
        else:
            fHandler.appendLINKtoFile(_catalogue_name, article[0] + " " + article[1], _search_request)


def parseLINKS(start_line, end_line, provider, search_request):
    # provider = self.getProvider()

    # ПОИСК БРАУЗЕРА ДЛЯ ИСПОЛЬЗОВАНИЯ
    driver = getBrowser()
    if driver is None:
        print("#### ОШИБКА! Не найден браузер")
        return Error.UNDEFIND_BROWSER

    articles = fHandler.getLINKSfromFileByLines(provider.getCatalogueName(), search_request, start_line, end_line)

    # Проходимся по линиям в файле
    for article in articles:

        # Загружаем страницу артикула по ссылке
        driver = provider.loadArticlePage(driver, article[1])
        type = provider.getArticleType(driver)
        if not driver:
            return Error.UNLOAD_ARTICLE_PAGE
        if driver == strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE:
            return Error.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

        # Вытаскиваем аналоги
        analog_article_name = ""
        analog_producer_name = ""
        if len(article) == 4:
            analog_article_name = article[2]
            analog_producer_name = article[3]
        elif len(article) == 3:
            analog_article_name = article[2]

        # Формируем JSON
        article_json = provider.saveJSON(driver, article[1], article[0], type, search_request, analog_article_name, analog_producer_name)

        # if len(article) == 3 and self._catalogue_name == "DONALDSON":
        #     article_json = JSONHandler.appendOldAnalogToJSON(article_json, article[2], provider.getCatalogueName())
        # if len(article) == 4 and self._catalogue_name == "FILFILTER":
        #     article_json = JSONHandler.appendAnalogToJSON(article_json, article[2], article[3])
        fHandler.appendJSONToFile(provider.getCatalogueName(), article_json, search_request)
        print(f'{article[0]} -- взят JSON!')

        # self._provider.getAnalogs(article[1], article[0])
        # flag = doWhileNoSuccess(0, "parseCrossRef", self._provider.parseCrossReference, driver, article)

    driver.close()
    driver.quit()

    return "JSONS вытащены успешно!"

