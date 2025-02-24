import multiprocessing
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from HANDLERS.FailureHandler import Error
from HANDLERS import LOGHandler, PLAYWRIGHTHandler
from HANDLERS.PLAYWRIGHTHandler import PlaywrightBrowser
from PROVIDERS import Provider

from HANDLERS import FILEHandler as fHandler

import Decorators

# _THREADS_LIMIT = int(multiprocessing.cpu_count() / 2)
_THREADS_LIMIT = 2


LOGHandler.logText(f"THREADS_LIMIT: {_THREADS_LIMIT}")
_error = None


class WebWorker:
    _provider_name = ""
    _provider_code = None
    _search_request = ""

    _provider = None
    _playwright_handler = None

    def __init__(self, provider_code, request):
        self._provider_name = Provider.getProviderNameByCode(provider_code)
        self._provider_code = provider_code
        self._search_request = request

        self._provider = self.getProvider()

        fHandler.createLINKSDir(self._provider_name)
        fHandler.createJSONSDir(self._provider_name)

    def __del__(self):
        pass

    @Decorators.log_decorator
    def getProvider(self) -> Provider:
        LOGHandler.logText(f"САЙТ-ПРОИЗВОДИТЕЛЬ: {self._provider_name.upper()}")
        return getProvider(self._provider_code)

    @Decorators.time_decorator
    @Decorators.failures_decorator
    @Decorators.log_decorator
    def pullCrossRefToDB(self):

        checkInternetConnection()
        checkInternetConnection(self._provider.getMainUrl())

        # ПОЛУЧАЕМ КОЛИЧЕСТВО СТРАНИЦ
        print("getPageCount() START!")
        with Browser() as browser:
            max_page = self._provider.getPageCount(browser.getDriver(), self._search_request)
        print("getPageCount() END!")

        if max_page == -1:
            return Error.FIND_NOTHING
        else:
            if max_page == 0:
                max_page = 1
            else:
                max_page = int(max_page)

        # Вытаскиваем ссылки на элементы
        print("----")
        print("getArticleLINKSByThreads() START!")
        getArticleLINKSByThreads(self._provider, self._search_request, max_page)
        if _error is not None:
            return _error
        print("getArticleLINKSByThreads() END!")

        # Генерируем JSONS
        print("----")
        print("generateJSONSbyThreads() START!")
        generateJSONSbyThreads(self._provider, self._search_request)
        if _error is not None:
            return _error
        print("generateJSONSbyThreads() END!")

        return 0


#
# UTILITIES
#

def getProvider(_provider_code) -> Provider:
    return Provider.getProviderByProviderCode(_provider_code)

@Decorators.time_decorator
@Decorators.failures_decorator
@Decorators.log_decorator
def checkInternetConnection(url='http://www.google.com/'):
    # ПРОВЕРКА ИНТЕРНЕТ СОЕДИНЕНИЯ
    try:
        from urllib import request
        request.urlopen(url)
        return 0
    except:
        return Error.INTERNET_CONNECTION


def getCountThreads(count_elements):
    if count_elements // _THREADS_LIMIT > 0:
        return _THREADS_LIMIT
    else:
        return count_elements


@Decorators.time_decorator
@Decorators.log_decorator
def getArticleLINKSByThreads(provider, _search_request, max_page):

    # Определяем количество потоков
    count_threads = getCountThreads(max_page)

    # Если HiFi то...
    if provider.getName() == "HIFI":
        getLINKSbyPage(range(0, max_page))

    elif provider.getName() == "FLEETGUARD":
        saveArticles(provider.parseSearchResult(None), _search_request, provider.getName())

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

        # with PoolHandler(count_threads) as poolHandler:
        #     for i in range(0, count_threads):
        #         poolHandler.start(getLINKSbyPage, Provider.cloneProvider(provider), _search_request, pages[i])

        with multiprocessing.Pool(processes=count_threads) as pool:
            for i in range(0, count_threads):
                pool.apply_async(getLINKSbyPage, args=(provider.getName(), _search_request, pages[i],))
            pool.close()
            pool.join()

    return


@Decorators.time_decorator
@Decorators.log_decorator
def generateJSONSbyThreads(provider, _search_request):

    count_lines = fHandler.getCountLINKSLines(provider.getName(), f"{_search_request}.txt")

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

    with multiprocessing.Pool(processes=count_threads) as pool:
        for i in range(0, count_threads):
            pool.apply_async(parseLINKS, args=(parts[i][0], parts[i][1], provider.getName(), _search_request))
        pool.close()
        pool.join()

    return


@Decorators.time_decorator
@Decorators.failures_decorator
@Decorators.log_decorator
def getLINKSbyPage(provider_name, _search_request, pages):

    print(f"{pages} getProviderByProviderName() START!")
    provider = Provider.getProviderByProviderName(provider_name)
    print(f"{pages} getProviderByProviderName() END!")

    catalogue_name = provider.getName()

    # ПОИСК БРАУЗЕРА ДЛЯ ИСПОЛЬЗОВАНИЯ
    with Browser() as browser:

        print(f"{pages} PAGES START!")
        for page in pages:

            print(f"{pages} --> Page: {page} START!")

            if provider.getName() == "MANN":
                if page >= provider.max_page_search:
                    break

            if provider.getName() == "MANN":
                print(f"{page} ----> searchProducts()")
                a = provider.searchProducts(browser.getDriver(), page, _search_request)
            else:
                print(f"{page} ----> search()")
                a = provider.search(browser.getDriver(), page, _search_request)

            if not a:
                _error = Error.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
                return Error.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

            print(f"{page} ----> parseSearchResult()")
            articles = provider.parseSearchResult(browser.getDriver(), page)
            if len(articles) > 0:
                print(f"{page} ----> saveArticles()")
                saveArticles(articles, _search_request, catalogue_name)
            else:
                return Error.NOTHING_TO_SEARCH

            print(f"{pages} --> Page: {page} END!")



        if provider.getName() == "MANN":

            print(f"{pages} PAGES START!")
            for page in pages:

                print(f"{pages} --> Page: {page} START!")

                if page >= provider.max_page_cross_ref:
                    break

                print(f"{page} ----> searchCrossRef()")
                a = provider.searchCrossRef(browser.getDriver(), page, _search_request)
                if not a:
                    _error = Error.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
                    return Error.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

                print(f"{page} ----> parseCrossReferenceResult()")
                articles = provider.parseCrossReferenceResult(browser.getDriver(), page)
                if len(articles) > 0:
                    print(f"{page} ----> saveArticles()")
                    saveArticles(articles, _search_request, catalogue_name)
                else:
                    return Error.NOTHING_TO_SEARCH

                print(f"{pages} --> Page: {page} END!")

            print(f"{pages} --> Page: {page} END!")

    return 0


@Decorators.time_decorator
@Decorators.failures_decorator
@Decorators.log_decorator
def parseLINKS(start_line, end_line, provider_name, search_request):

    print(f"{start_line}-{end_line} getProviderByProviderName() START!")
    provider = Provider.getProviderByProviderName(provider_name)
    print(f"{start_line}-{end_line} getProviderByProviderName() END!")

    # ПОИСК БРАУЗЕРА ДЛЯ ИСПОЛЬЗОВАНИЯ
    print(f"{start_line}-{end_line} Browser() START!")
    with Browser() as browser:
        print(f"{start_line}-{end_line} Browser() ENTER!!")

        print(f"{start_line}-{end_line} getLINKSfromFileByLines() START!")
        articles = fHandler.getLINKSfromFileByLines(provider.getName(), search_request, start_line, end_line)
        print(f"{start_line}-{end_line} getLINKSfromFileByLines() END!")

        # with PlaywrightBrowser(PLAYWRIGHTHandler.PLAYWRIGHT_HANDLER.getPlaywright()) as playwright_browser:
        playwright_browser = PlaywrightBrowser(PLAYWRIGHTHandler.PLAYWRIGHT_HANDLER.getPlaywright())

        # Проходимся по линиям в файле
        print(f"{start_line}-{end_line} Articles: {articles}")
        for article in articles:
            print(f"{start_line}-{end_line} --> Article: {article} START!")

            LOGHandler.logText(f">>>> parseLINKS({start_line}, {end_line}): {article}")

            # Загружаем страницу артикула по ссылке
            print(f"{start_line}-{end_line} ----> loadArticlePage()")
            provider.loadArticlePage(browser.getDriver(), article[1])

            print(f"{start_line}-{end_line} ----> getArticleType()")
            type = provider.getArticleType(browser.getDriver())

            # Вытаскиваем аналоги
            analog_article_name = ""
            analog_producer_name = ""
            if len(article) == 4:
                analog_article_name = article[2]
                analog_producer_name = article[3]
            elif len(article) == 3:
                analog_article_name = article[2]

            # Формируем JSON
            print(f"{start_line}-{end_line} ----> saveJSON()")
            article_json = provider.saveJSON(browser.getDriver(), article[1], article[0], type, search_request,
                                             analog_article_name, analog_producer_name, playwright_browser)
            print(f"Article JSON: {article_json}")

            fHandler.appendJSONToFile(provider.getName(), article_json, search_request)
            LOGHandler.logText(f'{article[0]} -- взят JSON!')

            print(f"{start_line}-{end_line} --> Article: {article} END!")

            print(f"{start_line}-{end_line} Articles END!")

    print(f"{start_line}-{end_line} Browser() EXIT!")

    LOGHandler.logText(f"<<<< parseLINKS({start_line}, {end_line})")

    LOGHandler.logText(f"Returning parseLINKS({start_line}, {end_line})")

    return 0


@Decorators.log_decorator
def saveArticles(articles, _search_request, _catalogue_name):
    for article in articles:
        LOGHandler.logText(f"{article[0]} - найден!")

        if len(article) == 4:
            fHandler.appendLINKtoFile(_catalogue_name,
                                      article[0] + " " + article[1] + " " + article[2] + " " + article[3],
                                      _search_request)
        elif len(article) == 3:
            fHandler.appendLINKtoFile(_catalogue_name, article[0] + " " + article[1] + " " + article[2],
                                      _search_request)
        else:
            fHandler.appendLINKtoFile(_catalogue_name, article[0] + " " + article[1], _search_request)


class Browser:
    # https://ru.stackoverflow.com/questions/735181/%D0%9A%D0%B0%D0%BA-%D1%81%D0%B4%D0%B5%D0%BB%D0%B0%D1%82%D1%8C-%D0%BC%D0%B5%D1%82%D0%BE%D0%B4-%D0%BF%D1%80%D0%B8%D0%B3%D0%BE%D0%B4%D0%BD%D1%8B%D0%BC-%D0%B4%D0%BB%D1%8F-with

    _driver = None

    @Decorators.failures_decorator
    def __enter__(self):
        MAX_COUNT = 3
        count = 0
        while self._driver is None and count < MAX_COUNT:
            self._driver = self.getBrowser()
            count += 1
        if self._driver is None:
            return Error.UNDEFIND_CHROME_DRIVER
        print(f"driver enter(): {self._driver}")
        return self

    @Decorators.failures_decorator
    def __exit__(self, exception_type, exception_value, traceback):
        print(f"driver exit(): {self._driver}")
        try:
            self._driver.close()
            self._driver.quit()
        except Exception as e:
            print("Не удалось закрыть driver:\n" + str(e))
            return Error.UNDEFIND_CHROME_DRIVER
        return 0

    #
    #
    #

    def getDriver(self):
        return self._driver

    @Decorators.time_decorator
    @Decorators.log_decorator
    def getBrowser(self):
        print(f"getBrowser()")
        options = webdriver.ChromeOptions()
        options.add_experimental_option(
            "prefs", {
                # не загружаем видео, стили и изображения
                'profile.managed_default_content_settings.images': 2,
                'profile.managed_default_content_settings.media_stream': 2,
                'profile.managed_default_content_settings.stylesheets': 2,
            },
        )

        # Add various options to make the browser more stable
        options.add_argument('--disable-gpu')  # Disable GPU hardware acceleration
        options.add_argument('--enable-unsafe-swiftshader')  # Disable WebRTC
        options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
        options.add_argument('--disable-web-security')  # Disable web security
        options.add_argument('--allow-running-insecure-content')  # Allow running insecure content
        options.add_argument('--disable-webrtc')  # Disable WebRTC

        options.add_argument('--blink-settings=imagesEnabled=false')

        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument("--incognito")

        options.add_argument('--no-sandbox')
        # options.add_argument('--headless')

        # https://stackoverflow.com/questions/29858752/error-message-chromedriver-executable-needs-to-be-available-in-the-path/52878725#52878725
        # https://stackoverflow.com/questions/78796828/i-got-this-error-oserror-winerror-193-1-is-not-a-valid-win32-application
        chrome_install = ChromeDriverManager().install()
        folder = os.path.dirname(chrome_install)
        chromedriver_path = os.path.join(folder, "chromedriver.exe")
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(options=options, service=service)
        return driver


class PoolHandler:
    _pool = None
    _count_threads = 0

    def __init__(self, count_threads):
        self._count_threads = count_threads

    def __enter__(self):
        self._pool = multiprocessing.Pool(processes=self._count_threads)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self._pool.close()
            self._pool.join()
            if self._pool is not None:
                LOGHandler.logText(f"{exc_val}: {self._pool._processes} cleaned processes")
                for i in range(self._pool._processes):
                    self._pool._pool[i].kill()
                self._pool.terminate()
                self._pool.join()
        except Exception as e:
            print("Не удалось закрыть Pool:\n" + str(e))
            return Error.UNDEFIND_CHROME_DRIVER
        return 0

    def start(self, func, *args):
        try:
            # https://sky.pro/wiki/python/primery-ispolzovaniya-pool-apply-apply-async-map-v-python/
            self._pool.apply_async(getLINKSbyPage, args=(*args,))
        except Exception as e:
            print("Не удалось запустить Pool:\n" + str(e))
            return Error.UNDEFIND_CHROME_DRIVER

        return 0

