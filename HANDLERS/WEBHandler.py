import requests
import datetime
import threading

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from PROVIDERS import Donaldson as Donaldson, FilFilter as FilFilter
from HANDLERS import FILEHandler as fHandler, DBHandler as db
from UTILS import strings


_provider = None
_search_request = ""
_catalogue_name = ""
_THREADS_LIMIT = 4


def getProviderAndProducerId(catalogue_name, dbHandler):
    if catalogue_name == "DONALDSON":
        print("ПО САЙТУ-ПРОИЗВОДИТЕЛЮ: DONALDSON")
        producer_id = dbHandler.insertProducer(catalogue_name, catalogue_name)
        provider = Donaldson.Donaldson(producer_id, dbHandler)
    # elif site_name == "FLEETGUARD":
    #     producer_id = dbHandler.insertProducer(site_name)
    #     provider = fl.Fleetguard(producer_id)
    elif catalogue_name == "FIL-FILTER":
        print("ПО САЙТУ-ПРОИЗВОДИТЕЛЮ: FIL-FILTER")
        producer_id = dbHandler.insertProducer(catalogue_name, catalogue_name)
        provider = FilFilter.FilFilter(producer_id, dbHandler)

    else:
        print("#### ОШИБКА! Выбран некорректный сайт производителя: " + str(catalogue_name))
        return strings.UNDEFIND_PRODUCER + ": " + str(catalogue_name)

    return provider


def setGlobals(provider, search_request):
    global _provider, _search_request
    _provider = provider
    _search_request = search_request


def setGlobalCatalogueName(catalogue_name):
    global _catalogue_name
    _catalogue_name = catalogue_name


def getBrowser():
    driver = None

    try:
        # options = webdriver.EdgeOptions()
        # options.use_chromium = True
        # options.add_argument("--lang=ru")
        # options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # prefs = {
        #     "translate_whitelists": 'ru',
        #     "translate": {"enabled": "true"}
        # }
        # options.add_experimental_option("prefs", prefs)
        # driver = webdriver.Edge(options=options)
        driver = webdriver.Edge()
    except Exception as ex:
        print(ex)
        try:
            # options = webdriver.ChromeOptions()
            # options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0")
            # options.add_argument("--disable-blink-features=AutomationControlled")
            # https://www.youtube.com/watch?v=EMMY9t6_R4A
            # options.add_argument("--lang=ru")
            # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
            driver = webdriver.Chrome()
        except:
            try:
                driver = webdriver.Firefox()
            except:
                try:
                    driver = webdriver.Ie()
                except:
                    print("БРАУЗЕР НЕ НАЙДЕН!")
    return driver


def getCountThreads(count_elements):
    if count_elements // _THREADS_LIMIT > 0:
        return _THREADS_LIMIT
    else:
        return count_elements


def getLINKSbyPage(pages):
    global _provider, _search_request, _catalogue_name

    try:
        # ПОИСК БРАУЗЕРА ДЛЯ ИСПОЛЬЗОВАНИЯ
        driver = getBrowser()
        if driver is None:
            print("#### ОШИБКА! Не найден браузер")
            return strings.UNDEFIND_BROWSER

        for page in pages:

            driver = _provider.search(driver, page, _search_request)
            if driver == strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE:
                return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
            print(f"T{page}: search() -> completed")

            articles = _provider.parseSearchResult(driver)
            if articles == strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE:
                return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
            print(f"T{page}: parseSearchResult() -> completed")

            for article in articles:
                fHandler.appendLINKtoFile(_catalogue_name, article[0] + " " + article[1], _search_request)
            print(f"T{page}: appendLINKtoFile() -> completed")

            print(f'PAGE №{page} -> completed')
            print()

    except Exception as ex:
        print(ex)

    finally:
        driver.close()
        driver.quit()

        return "ССЫЛКИ ВЫТАЩЕНЫ УСПЕШНО!"


class WebWorker:

    _catalogue_name = ""
    _search_request = ""

    _provider = None
    _dbHandler = None

    def __init__(self, catalogue_name, request):
        self._catalogue_name = catalogue_name
        self._search_request = request
        self._dbHandler = db.DBWorker('5432')
        self._provider = self.getProvider()

        fHandler.createLINKSDir(self._catalogue_name)
        fHandler.createJSONSDir(self._catalogue_name)
        fHandler.createLOGSDir()

    def getProvider(self):

        if self._catalogue_name == "DONALDSON":
            print("ПО САЙТУ-ПРОИЗВОДИТЕЛЮ: DONALDSON")
            producer_id = self._dbHandler.insertProducer(self._catalogue_name, self._catalogue_name)
            provider = Donaldson.Donaldson(producer_id, self._dbHandler)
        # elif site_name == "FLEETGUARD":
        #     producer_id = dbHandler.insertProducer(site_name)
        #     provider = fl.Fleetguard(producer_id)
        elif self._catalogue_name == "FIL-FILTER":
            print("ПО САЙТУ-ПРОИЗВОДИТЕЛЮ: FIL-FILTER")
            producer_id = self._dbHandler.insertProducer(self._catalogue_name, self._catalogue_name)
            provider = ff.FilFilter(producer_id, self._dbHandler)

        else:
            print("#### ОШИБКА! Выбран некорректный сайт производителя: " + str(self._catalogue_name))
            return strings.UNDEFIND_PRODUCER + ": " + str(self._catalogue_name)

        return provider


    def pullCrossRefToDB(self):

        print("----> pullCrossRefToDB() ")
        start_time = datetime.datetime.now()

        # ПРОВЕРКА ИНТЕРНЕТ СОЕДИНЕНИЯ
        try:
            requests.head(self._provider.getMainUrl(), timeout=1)
        except:
            print("#### ОШИБКА! Отсутствует интернет-соединение")
            return strings.INTERNET_ERROR

        # ПОЛУЧАЕМ КОЛИЧЕСТВО СТРАНИЦ
        driver = getBrowser()
        if driver is None:
            print("#### ОШИБКА! Не найден браузер")
            return strings.UNDEFIND_BROWSER
        max_page = self._provider.getPageCount(driver, self._search_request)
        if max_page == strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE:
            max_page = 1
        else:
            max_page = int(max_page)
        driver.close()
        driver.quit()

        print()

        # Вытаскиваем ссылки на элементы
        start_time_links = datetime.datetime.now()
        self.getArticleLINKSByThreads(max_page)
        end_time_links = datetime.datetime.now()
        print("getArticleLinksByThreads() -> completed! ВРЕМЯ: " +
              str(int((end_time_links-start_time_links).total_seconds())) + " сек.")
        print()

        # Генерируем JSONS
        start_time_generating_jsons = datetime.datetime.now()
        self.generateJSONSbyThreads()
        end_time_generating_jsons = datetime.datetime.now()
        print("getArticleLinksByThreads() -> completed! ВРЕМЯ: " +
              str(int((end_time_generating_jsons - start_time_generating_jsons).total_seconds())) + " сек.")
        print()

        end_time = datetime.datetime.now()
        print("<---- END pullCrossRefToDB(): " + str(int((end_time-start_time).total_seconds())) + " сек.\n\n")

        return "ССЫЛКИ ВЫТАЩЕНЫ УСПЕШНО!"


    def parseLINKS(self, start_line, end_line):

        try:

            provider = self.getProvider()

            # ПОИСК БРАУЗЕРА ДЛЯ ИСПОЛЬЗОВАНИЯ
            driver = getBrowser()
            if driver is None:
                print("#### ОШИБКА! Не найден браузер")
                return strings.UNDEFIND_BROWSER

            articles = fHandler.getLINKSfromFileByLines("DONALDSON", self._search_request, start_line, end_line)
            print()

            for article in articles:

                print(f'{article[0]}')

                # PARSE PAGE
                driver = provider.loadArticlePage(driver, article[1])
                if not driver:
                    return "НЕ УДАЛОСЬ ЗАГРУЗИТЬ СТРАНИЦУ АРТИКУЛА"
                if driver == strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE:
                    return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
                print("loadArticlePage() -> completed")
                provider.saveJSON(article[1], article[0], self._search_request)

                print()

                # self._provider.getAnalogs(article[1], article[0])
                # flag = doWhileNoSuccess(0, "parseCrossRef", self._provider.parseCrossReference, driver, article)

        except Exception as ex:
            print(ex)

        finally:
            driver.close()
            driver.quit()

        return "JSONS вытащены успешно!"

    def generateJSONSbyThreads(self):

        count_lines = fHandler.getCountLINKSLines(self._catalogue_name, f"{self._search_request}.txt")

        # Определяем количество потоков
        count_threads = getCountThreads(count_lines)

        # Распределяем ссылки (части файла) по потокам
        parts = []
        count_lines_in_part = count_lines // count_threads
        if count_lines // count_threads != 0:
            for i in range(0, count_threads):
                start_index = i * count_lines_in_part
                end_index = (i+1) * count_lines_in_part
                parts.append([start_index, end_index])

        # Добавляем поток с нераспределёнными ссылками
        if count_lines % count_threads != 0:
            parts.append([count_lines - (count_lines % count_threads), count_lines])

        # Запускаем потоки

        tasks = []
        for i in range(0, count_threads):
            tasks.append(threading.Thread(target=self.parseLINKS, args=(parts[i][0], parts[i][1])))
        for i in range(0, count_threads):
            tasks[i].start()
            print(f"T{i} START!")
        for i in range(0, count_threads):
            tasks[i].join()
        if count_lines % count_threads != 0:
            index = len(parts)-1
            tasks.append(threading.Thread(target=self.parseLINKS, args=(parts[index][0], parts[index][1])))
            tasks[index].start()
            print(f"T{index} START!")
            tasks[index].join()

    def getArticleLINKSByThreads(self, max_page):
        setGlobals(self._provider, self._search_request)
        setGlobalCatalogueName(self._catalogue_name)

        # Определяем количество потоков
        count_threads = getCountThreads(max_page)

        pages = []
        for j in range(0, count_threads):
            pages.append([])

        # Распределяем страницы между потоками
        for i in range(0, max_page // count_threads * count_threads, count_threads):
            for j in range(0, count_threads):
                pages[j].append(i + j)
        if max_page % count_threads != 0:
            for i in range((max_page // count_threads) * count_threads, max_page):
                pages[i % 4].append(i)
        # print(pages)

        # Запускаем потоки
        tasks = []
        for i in range(0, count_threads):
            tasks.append(threading.Thread(target=getLINKSbyPage, args=(pages[i],)))
        for index, process in enumerate(tasks):
            process.start()
            print(f"T{index} START!")
        print()
        for process in tasks:
            process.join()
