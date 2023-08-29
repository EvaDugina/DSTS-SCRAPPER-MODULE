import requests
import datetime
import threading

from selenium import webdriver

from PROVIDERS import Donaldson as dl, FilFilter as ff
# import Fleetguard as fl
from HANDLERS import FILEHandler as fHandler, DBHandler as db
from UTILS import strings


_provider = None
_search_request = ""
_catalogue_name = ""
_THREADS_LIMIT = 4


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
        driver = webdriver.Edge()
    except:
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0")
            options.add_argument("--disable-blink-features=AutomationControlled")
            # https://www.youtube.com/watch?v=EMMY9t6_R4A
            driver = webdriver.Chrome(options=options)
        except:
            try:
                driver = webdriver.Firefox()
            except:
                try:
                    driver = webdriver.Ie()
                except:
                    print("БРАУЗЕР НЕ НАЙДЕН!")
    return driver


def getLINKSbyPage(pages):
    global _provider, _search_request

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
                fHandler.appendLINKtoFile("DONALDSON", article[0] + " " + article[1])
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

    def getProvider(self):

        if self._catalogue_name == "DONALDSON":
            print("ПО САЙТУ-ПРОИЗВОДИТЕЛЮ: DONALDSON")
            producer_id = self._dbHandler.insertProducer(self._catalogue_name)
            provider = dl.Donaldson(producer_id, self._dbHandler)
        # elif site_name == "FLEETGUARD":
        #     producer_id = dbHandler.insertProducer(site_name)
        #     provider = fl.Fleetguard(producer_id)
        elif self._catalogue_name == "FIL-FILTER":
            print("ПО САЙТУ-ПРОИЗВОДИТЕЛЮ: FIL-FILTER")
            producer_id = self._dbHandler.insertProducer(self._catalogue_name)
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
        except requests.ConnectionError:
            print("#### ОШИБКА! Отсутствует интернет-соединение")
            return strings.INTERNET_ERROR


        # ДЛЯ КРОСС-РЕФЕРЕНСА ПО ПРЯМОЙ ССЫЛКЕ
        # if url is not None:
        #     print("--> Кросс-Референс по прямой ссылке:")
        #     article = self._provider.getArticleFromURL(url)
        #     if not article:
        #         return strings.INCORRECT_LINK
        #
        #     producer_id = self._provider.getProducerId(article)
        #     print("PRODUCER_ID: " + str(producer_id))
        #
        #     print(f"-- {url} : {article[0]}")
        #     article_id = dbHandler.insertArticle(article[0], producer_id)
        #     driver = self._provider.loadArticlePage(driver, article, True)
        #     if not driver:
        #         return "НЕ УДАЛОСЬ ЗАГРУЗИТЬ СТРАНИЦУ"
        #
        #     flag = doWhileNoSuccess(0, "parseCrossRef", self._provider.parseCrossReference, driver, article_id)
        #
        #     if flag == "SUCCESS":
        #         return flag
        #     else:
        #         return "СТРАНИЦА НЕ БЫЛА ОБРАБОТАНА!\n" + str(flag)
        # print()

        # ПОЛУЧАЕМ КОЛИЧЕСТВО СТРАНИЦ
        driver = getBrowser()
        if driver is None:
            print("#### ОШИБКА! Не найден браузер")
            return strings.UNDEFIND_BROWSER
        max_page = int(self._provider.getPageCount(driver, self._search_request))
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

            articles = fHandler.getLINKSfromFileByLines("DONALDSON", start_line, end_line)
            print()

            for article in articles:
                # producer_id = self._provider.getProducerId(article)
                # print("PRODUCER_ID: " + str(producer_id))
                # article[0] = dbHandler.insertArticle(article[0], producer_id)

                print(f'{article[0]}')

                # PARSE PAGE
                driver = provider.loadArticlePage(driver, article[1])
                if not driver:
                    return "НЕ УДАЛОСЬ ЗАГРУЗИТЬ СТРАНИЦУ АРТИКУЛА"
                if driver == strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE:
                    return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
                print("loadArticlePage() -> completed")
                provider.saveJSON(article[1], article[0])

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
        setGlobalCatalogueName(self._catalogue_name)

        count_lines = fHandler.getCountLINKSLines(f"{self._catalogue_name}.txt")

        tasks = []
        count_lines_in_part = count_lines // _THREADS_LIMIT
        for i in range(0, _THREADS_LIMIT):
            start_index = i * count_lines_in_part
            end_index = (i+1) * count_lines_in_part
            tasks.append(threading.Thread(target=self.parseLINKS, args=(start_index, end_index)))
        for index, task in enumerate(tasks):
            task.start()
            print(f"T{index} START!")
        for task in tasks:
            task.join()

        if count_lines % _THREADS_LIMIT != 0:
            t1 = threading.Thread(target=self.parseLINKS, args=(count_lines - (count_lines % _THREADS_LIMIT), count_lines))
            t1.start()
            t1.join()

    def getArticleLINKSByThreads(self, max_page):
        setGlobals(self._provider, self._search_request)

        pages = [[], [], [], []]
        for i in range(0, max_page // _THREADS_LIMIT * _THREADS_LIMIT, _THREADS_LIMIT):
            for j in range(0, _THREADS_LIMIT):
                pages[j].append(i + j)
        if max_page % _THREADS_LIMIT != 0:
            for i in range((max_page // _THREADS_LIMIT) * _THREADS_LIMIT, max_page):
                pages[i % 4].append(i)
        # print(pages)

        tasks = []
        for i in range(0, _THREADS_LIMIT):
            tasks.append(threading.Thread(target=getLINKSbyPage, args=(pages[i],)))
        for index, process in enumerate(tasks):
            process.start()
            print(f"T{index} START!")
        for process in tasks:
            process.join()

    def doWhileNoSuccess(self, try_count, type_function, function, driver, article):
        if try_count > 4:
            return "СЛАБОЕ ИНТЕРНЕТ-СОЕДИНЕНИЕ"
        else:
            flag = False
            if type_function == "parseCrossRef":
                if try_count > 0:
                    flag = function(driver, article, try_count * 2)
                else:
                    flag = function(driver, article, 1)

            elif type_function == "loadArticlePage":
                flag = function(driver, article)

            if flag == "SUCCESS" or flag == strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE:
                return flag
            else:
                return self.doWhileNoSuccess(try_count + 1, type_function, function, driver, article)
