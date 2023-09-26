import requests
import datetime
import threading

from selenium import webdriver
# from selenium.webdriver.chrome.service import Service as ChromeService
# from selenium.webdriver.edge.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

from PROVIDERS import Donaldson as Donaldson, FilFilter as FilFilter
from HANDLERS import FILEHandler as fHandler, DBHandler as db, JSONHandler
from UTILS import strings


_provider = None
_search_request = ""
_catalogue_name = ""
_THREADS_LIMIT = 4


def getProviderAndProducerId(catalogue_name, dbHandler):
    if catalogue_name == "DONALDSON":
        fHandler.appendToFileLog("ПО САЙТУ-ПРОИЗВОДИТЕЛЮ: DONALDSON")
        producer_id = dbHandler.insertProducer(catalogue_name, catalogue_name)
        provider = Donaldson.Donaldson(producer_id, dbHandler)
    # elif site_name == "FLEETGUARD":
    #     producer_id = dbHandler.insertProducer(site_name)
    #     provider = fl.Fleetguard(producer_id)
    elif catalogue_name == "FILFILTER":
        fHandler.appendToFileLog("ПО САЙТУ-ПРОИЗВОДИТЕЛЮ: FIL-FILTER")
        producer_id = dbHandler.insertProducer(catalogue_name, catalogue_name)
        provider = FilFilter.FilFilter(producer_id, dbHandler)

    else:
        fHandler.appendToFileLog("#### ОШИБКА! Выбран некорректный сайт производителя: " + str(catalogue_name))
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
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-extensions")
        # options.add_argument(f'user-agent={custom_user_agent}')
        # options.add_experimental_option("service_token", "3TuSgTm3MyS9ZL0adPDjYg==")
        # https://www.youtube.com/watch?v=EMMY9t6_R4A
        # https://habr.com/ru/companies/otus/articles/596071/

        driver = webdriver.Chrome(options=options)

        # headers = {
        #     'name': 'session',
        #     'value': 'token'
            # "cookie": "_ym_uid=1631135930373897084; velaro_firstvisit=^%^222021-09-08T21^%^3A19^%^3A53.213Z^%^22; velaro_visitorId=^%^22iVd6vCxQNEeputrfsVRsxA^%^22; _hjid=3ca22462-cbda-4de9-8c6e-890b1cd656a6; _hjSessionUser_64165=eyJpZCI6IjFhMGI4NzZlLTNiZDctNTZlMS05ODZiLTQ1Y2ZhODRiNjVkOSIsImNyZWF0ZWQiOjE2NzEwNDM0NTA4NTAsImV4aXN0aW5nIjp0cnVlfQ==; s_fid=6C0861A1CFD388C0-0A0E17E41816E781; s_vi=^[CS^]v1^|323E30732645E194-60001CD6C08918EB^[CE^]; _ga=GA1.3.325279740.1685872849; OptanonAlertBoxClosed=2023-06-04T10:01:13.407Z; _ym_d=1686815878; _fbp=fb.1.1692791546349.21032163; _gcl_au=1.1.1515802377.1693681082; _gid=GA1.2.771378523.1694085460; ln_or=eyIxOTkzOSI6ImQifQ^%^3D^%^3D; _ym_isad=2; _gid=GA1.3.771378523.1694085460; _fileDownloaded=false; at_check=true; s_cc=true; CartCount=1-9; s_sq=^%^5B^%^5BB^%^5D^%^5D; velaro_endOfDay=^%^222023-09-09T23^%^3A59^%^3A59.999Z^%^22; JSESSIONID=^\^hY3XIHfqcKO2sbo3-Bv_HCpmuKJKo6JkjQQGPnHG.gdcplecatg02:store-server-2^^; BIGipServerGDC_DMZ_dciorigin-shop=400649122.64288.0000; TS0159dbaf=01cef8c7d883b0a342294071a3f43faf8c60b4dfc94d0bea00c72c144bb2963ae7cf1c2b90abea7c21834a59e68417a710faf534d38aeaf29c9de1c0865a62c56148c50c8214dd5de070dd9f2191872fd21a2a0e3586e56f62b24b3c6dd87f7704e4593bc0; _hjSession_64165=eyJpZCI6ImU2MWIxMjBkLWIyZDYtNGIyNS05ZDNjLTMyODI0YzRhOWMyMyIsImNyZWF0ZWQiOjE2OTQyNTU2OTYwOTEsImluU2FtcGxlIjpmYWxzZX0=; _hjAbsoluteSessionInProgress=0; OptanonConsent=isGpcEnabled=0&datestamp=Sat+Sep+09+2023+13^%^3A34^%^3A56+GMT^%^2B0300+(^%^D0^%^9C^%^D0^%^BE^%^D1^%^81^%^D0^%^BA^%^D0^%^B2^%^D0^%^B0^%^2C+^%^D1^%^81^%^D1^%^82^%^D0^%^B0^%^D0^%^BD^%^D0^%^B4^%^D0^%^B0^%^D1^%^80^%^D1^%^82^%^D0^%^BD^%^D0^%^BE^%^D0^%^B5+^%^D0^%^B2^%^D1^%^80^%^D0^%^B5^%^D0^%^BC^%^D1^%^8F)&version=6.35.0&isIABGlobal=false&hosts=&consentId=4b50e940-fb46-468f-9592-b0e3d2ee37a1&interactionCount=3&landingPath=NotLandingPage&groups=C0001^%^3A1^%^2CC0003^%^3A1^%^2CC0002^%^3A1^%^2CC0004^%^3A1&AwaitingReconsent=false&geolocation=RU^%^3BMOW; mbox=PC^#111691350128204-676247.37_0^#1757500497^|session^#bbe3fa931d764a4b99a46ccff4ae3ed0^#1694257557; _uetsid=261dbaa04d7011ee8f50fb17959d466d; _uetvid=4cb96a007bdf11edb2bcbf04ba8acb36; gpv_p3=shop^%^3A^%^2Fstore^%^2Fru-ru^%^2Fproduct^%^2Fp551424^%^2F39794; _ga=GA1.2.325279740.1685872849; sessionExpiry=7200; AMCVS_211631365C190F8B0A495CFC^%^40AdobeOrg=1; AMCV_211631365C190F8B0A495CFC^%^40AdobeOrg=-1124106680^%^7CMCMID^%^7C69639804510096596081994692082918066722^%^7CMCAAMLH-1694860784^%^7C6^%^7CMCAAMB-1694860784^%^7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y^%^7CMCOPTOUT-1694263184s^%^7CNONE^%^7CMCSYNCSOP^%^7C411-19616^%^7CvVersion^%^7C5.2.0; ADRUM=s=1694255985568&r=https^%^3A^%^2F^%^2Fshop.donaldson.com^%^2Fstore^%^2Fru-ru^%^2Fproduct^%^2FP551424^%^2F39794^%^3F0; AKA_A2=A; _ga_9WYYFBQLF0=GS1.1.1694255695.72.0.1694255985.47.0.0; s_plt=^%^5B^%^5BB^%^5D^%^5D; s_pltp=^%^5B^%^5BB^%^5D^%^5D",
            # "accept-language": "ru;q=0.9",
            # "service_token": "3TuSgTm3MyS9ZL0adPDjYg==",
            # "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        # }
        # driver.add_cookie(headers)

    except Exception as ex:
        fHandler.appendToFileLog(ex)
        try:
            # https://www.youtube.com/watch?v=EMMY9t6_R4A
            # options = webdriver.ChromeOptions()
            # options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0")
            # options.add_argument("--disable-blink-features=AutomationControlled")
            # options.add_argument("--lang=ru")
            # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

            driver = webdriver.Edge()
        except:
            try:
                driver = webdriver.Firefox()
            except:
                try:
                    driver = webdriver.Ie()
                except:
                    fHandler.appendToFileLog("БРАУЗЕР НЕ НАЙДЕН!")
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
            fHandler.appendToFileLog("#### ОШИБКА! Не найден браузер")
            return strings.UNDEFIND_BROWSER

        for page in pages:

            driver = _provider.search(driver, page, _search_request)
            if driver == strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE:
                return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
            fHandler.appendToFileLog(f"T{page}: search() -> completed")

            articles = _provider.parseSearchResult(driver, page)
            if articles == strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE:
                return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
            fHandler.appendToFileLog(f"T{page}: parseSearchResult() -> completed")

            for article in articles:
                if len(article) == 4:
                    fHandler.appendLINKtoFile(_catalogue_name, article[0] + " " + article[1] + " " + article[2] + " " + article[3], _search_request)
                elif len(article) == 3:
                    fHandler.appendLINKtoFile(_catalogue_name, article[0] + " " + article[1] + " " + article[2], _search_request)
                else:
                    fHandler.appendLINKtoFile(_catalogue_name, article[0] + " " + article[1], _search_request)
            fHandler.appendToFileLog(f"T{page}: appendLINKtoFile() -> completed")

            fHandler.appendToFileLog(f'PAGE №{page} -> completed')
            fHandler.appendToFileLog("\n")

    except Exception as ex:
        fHandler.appendToFileLog(ex)

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

    def getProvider(self):

        if self._catalogue_name == "DONALDSON":
            fHandler.appendToFileLog("ПО САЙТУ-ПРОИЗВОДИТЕЛЮ: DONALDSON")
            producer_id = self._dbHandler.insertProducer(self._catalogue_name, self._catalogue_name)
            provider = Donaldson.Donaldson(producer_id, self._dbHandler)
        # elif site_name == "FLEETGUARD":
        #     producer_id = dbHandler.insertProducer(site_name)
        #     provider = fl.Fleetguard(producer_id)
        elif self._catalogue_name == "FILFILTER":
            fHandler.appendToFileLog("ПО САЙТУ-ПРОИЗВОДИТЕЛЮ: FIL-FILTER")
            producer_id = self._dbHandler.insertProducer(self._catalogue_name, self._catalogue_name)
            provider = FilFilter.FilFilter(producer_id, self._dbHandler)

        else:
            fHandler.appendToFileLog("#### ОШИБКА! Выбран некорректный сайт производителя: " + str(self._catalogue_name))
            return strings.UNDEFIND_PRODUCER + ": " + str(self._catalogue_name)

        return provider


    def pullCrossRefToDB(self):

        fHandler.appendToFileLog("----> pullCrossRefToDB() ")
        start_time = datetime.datetime.now()

        # ПРОВЕРКА ИНТЕРНЕТ СОЕДИНЕНИЯ
        try:
            requests.head(self._provider.getMainUrl(), timeout=1)
        except:
            fHandler.appendToFileLog("#### ОШИБКА! Отсутствует интернет-соединение")
            return strings.INTERNET_ERROR

        # ПОЛУЧАЕМ КОЛИЧЕСТВО СТРАНИЦ
        driver = getBrowser()
        if driver is None:
            fHandler.appendToFileLog("#### ОШИБКА! Не найден браузер")
            return strings.UNDEFIND_BROWSER
        max_page = self._provider.getPageCount(driver, self._search_request)
        if max_page == strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE:
            max_page = 1
        else:
            max_page = int(max_page)
        driver.close()
        driver.quit()

        fHandler.appendToFileLog("\n")

        # Вытаскиваем ссылки на элементы
        start_time_links = datetime.datetime.now()
        self.getArticleLINKSByThreads(max_page)
        end_time_links = datetime.datetime.now()
        fHandler.appendToFileLog("getArticleLinksByThreads() -> completed! ВРЕМЯ: " +
              str(int((end_time_links-start_time_links).total_seconds())) + " сек.")
        fHandler.appendToFileLog("\n")

        # Генерируем JSONS
        start_time_generating_jsons = datetime.datetime.now()
        self.generateJSONSbyThreads()
        end_time_generating_jsons = datetime.datetime.now()
        fHandler.appendToFileLog("getArticleLinksByThreads() -> completed! ВРЕМЯ: " +
              str(int((end_time_generating_jsons - start_time_generating_jsons).total_seconds())) + " сек.")
        fHandler.appendToFileLog("\n")

        end_time = datetime.datetime.now()
        fHandler.appendToFileLog("<---- END pullCrossRefToDB(): " + str(int((end_time-start_time).total_seconds())) + " сек.\n\n")

        return "ССЫЛКИ ВЫТАЩЕНЫ УСПЕШНО!"


    def parseLINKS(self, start_line, end_line):

        try:

            provider = self.getProvider()

            # ПОИСК БРАУЗЕРА ДЛЯ ИСПОЛЬЗОВАНИЯ
            driver = getBrowser()
            if driver is None:
                fHandler.appendToFileLog("#### ОШИБКА! Не найден браузер")
                return strings.UNDEFIND_BROWSER

            articles = fHandler.getLINKSfromFileByLines(self._provider.getCatalogueName(), self._search_request, start_line, end_line)
            fHandler.appendToFileLog("\n")

            for article in articles:

                fHandler.appendToFileLog(f'{article[0]}')

                # PARSE PAGE

                driver = provider.loadArticlePage(driver, article[1])

                type = provider.getArticleType(driver)
                if not driver:
                    return "НЕ УДАЛОСЬ ЗАГРУЗИТЬ СТРАНИЦУ АРТИКУЛА"
                if driver == strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE:
                    return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
                fHandler.appendToFileLog("loadArticlePage() -> completed")


                article_json = provider.saveJSON(driver, article[1], article[0], type, self._search_request, article)
                # print(article_json)


                # if len(article) == 3 and self._catalogue_name == "DONALDSON":
                #     article_json = JSONHandler.appendOldAnalogToJSON(article_json, article[2], provider.getCatalogueName())
                # if len(article) == 4 and self._catalogue_name == "FILFILTER":
                #     article_json = JSONHandler.appendAnalogToJSON(article_json, article[2], article[3])
                fHandler.appendJSONToFile(provider.getCatalogueName(), article_json, self._search_request)

                fHandler.appendToFileLog("\n")

                # self._provider.getAnalogs(article[1], article[0])
                # flag = doWhileNoSuccess(0, "parseCrossRef", self._provider.parseCrossReference, driver, article)

        except Exception as ex:
            fHandler.appendToFileLog(ex)

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
            fHandler.appendToFileLog(f"T{i} START!")
        for i in range(0, count_threads):
            tasks[i].join()
        if count_lines % count_threads != 0:
            index = len(parts)-1
            tasks.append(threading.Thread(target=self.parseLINKS, args=(parts[index][0], parts[index][1])))
            tasks[index].start()
            fHandler.appendToFileLog(f"T{index} START!")
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
            fHandler.appendToFileLog(f"T{index} START!")
        fHandler.appendToFileLog("\n")
        for process in tasks:
            process.join()
