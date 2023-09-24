import logging
import time
import traceback

from playwright.sync_api import sync_playwright
from selenium.common import WebDriverException, JavascriptException
from selenium.webdriver.common.by import By

from PROVIDERS import Provider
from HANDLERS import FILEHandler as fHandler, JSONHandler as parseJSON
from UTILS import strings


logging.getLogger().setLevel(logging.INFO)


def wait_until(return_value, period=0.5):
    time.sleep(period)
    while return_value != 1:
        time.sleep(period)
    return False


class FilFilter(Provider.Provider):

    _main_url = "https://catalog.filfilter.com.tr/ru"
    _catalog_url = "https://catalog.filfilter.com.tr/ru/search/"
    _max_page = 1
    _dbHandler = None

    def __init__(self, producer_id, dbHandler):
        self._producer_id = producer_id
        self._dbHandler = dbHandler
        self._producer_name = dbHandler.getProducerById(self._producer_id)

    def getMainUrl(self):
        return self._main_url

    def getArticleFromURL(self, url):
        url_attr = url.split("/")
        if len(url_attr) < 4:
            return False
        return [url_attr[5], url]

    def getProducerId(self, article):
        return self._dbHandler.insertProducer(article[3])

    def getPageCount(self, driver, search_request):
        driver.get(self._catalog_url + search_request)

        # Отображаем максимальное количество элементов на странице
        # try:
        executing_return = driver.execute_script("let pageButton = document.getElementById(\"select_6\");"
                                                 "pageButton.click();"
                                                 "let select_arrayCountByPage = document.getElementById(pageButton.getAttribute(\"aria-owns\"));"
                                                 "let aa = select_arrayCountByPage.firstChild.firstChild;"
                                                 "let button_countByPage = aa.children[aa.children.length-1];"
                                                 "document.getElementById(button_countByPage.getAttribute(\"id\")).click();"
                                                 "document.getElementById(\"select_3\").click();"
                                                 "return 1;")
        wait_until(int(executing_return))
        # except JavascriptException:
        #     return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

        # Получаем максимальное количество страниц в поиске
        try:
            buttonPages = driver.find_elements(By.ID, "select_3")
            if buttonPages:
                selectElement = driver.find_elements(By.ID, buttonPages[0].get_attribute("aria-owns"))
                lastchildren = selectElement[0].find_elements(By.CSS_SELECTOR, "*")[
                    0].find_elements(By.CSS_SELECTOR, "*")[0].find_elements(By.TAG_NAME, "md-option")
                count = len(lastchildren)
                self._max_page = int(lastchildren[count - 1].get_attribute("value"))
                return self._max_page
        except JavascriptException or IndexError:
            return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

        return -1

    def endCondision(self, page):
        if page < self._max_page:
            return True
        return False



    # Поиск
    def search(self, driver, page_number, search_request):
        driver.get(self._catalog_url + search_request)

        # Отображаем максимальное количество элементов на странице
        # try:
        executing_return = driver.execute_script("let pageButton = document.getElementById(\"select_6\");"
                                                 "pageButton.click();"
                                                 "let select_arrayCountByPage = document.getElementById(pageButton.getAttribute(\"aria-owns\"));"
                                                 "let aa = select_arrayCountByPage.firstChild.firstChild;"
                                                 "let button_countByPage = aa.children[aa.children.length-1];"
                                                 "document.getElementById(button_countByPage.getAttribute(\"id\")).click();"
                                                 "document.getElementById(\"select_3\").click();"
                                                 "return 1;")
        wait_until(int(executing_return))
        # except JavascriptException:
        #     return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

        if page_number > 0:
            # Переходим на др. страницу
            executing_return = driver.execute_script("let pageButton = document.getElementById(\"select_6\");"
                                                     "pageButton.click();"
                                                     "let select_arrayCountByPage = document.getElementById(pageButton.getAttribute(\"aria-owns\"));"
                                                     "let aa = select_arrayCountByPage.firstChild.firstChild;"
                                                     "let button_countByPage = aa.children[" + str(
                page_number - 1) + "];"
                                   "button_countByPage.click();"
                                   "return 1;")
            wait_until(int(executing_return))
        # else:
        #
        #     # Получаем максимальное количество страниц в поиске
        #     try:
        #         buttonPages = driver.find_elements(By.ID, "select_3")
        #         if buttonPages:
        #             selectElement = driver.find_elements(By.ID, buttonPages[0].get_attribute("aria-owns"))
        #             lastchildren = selectElement[0].find_elements(By.CSS_SELECTOR, "*")[
        #                 0].find_elements(By.CSS_SELECTOR, "*")[0].find_elements(By.TAG_NAME, "md-option")
        #             count = len(lastchildren)
        #             self._max_page = int(lastchildren[count - 1].get_attribute("value"))
        #     except JavascriptException or IndexError:
        #         return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

        return driver

    # Парсинг одну страницу поиска
    def parseSearchResult(self, driver):
        # print("parseSearchResult")
        trs = driver.find_elements(By.TAG_NAME, "tr")
        trs.pop(0)
        articles = []
        for index, elem in enumerate(trs, start=0):
            try:
                tds = elem.find_elements(By.TAG_NAME, "td")
                articles.append([tds[0].get_attribute("innerHTML"), tds[2].get_attribute("innerHTML"),
                                 index, tds[1].get_attribute("innerHTML")])
            except JavascriptException or IndexError:
                return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
        return articles

    # Загрузка страницы товара
    def loadArticlePage(self, driver, article, search_type=False):
        if search_type:
            try:
                driver.get(article[1])
            except WebDriverException:
                return False
            return driver

        executing_return = \
            driver.execute_script("let trs = document.getElementsByTagName(\"tr\");"
                                  f"let tr = trs[{str(article[2]+1)}];"
                                  f"tr.children[tr.children.length-1].children[0].classList.add(\"button-link-{str(article[2])}\");"
                                  "document.getElementsByClassName(\"button-link-"+str(article[2])+"\")[0].click();"
                                  "return 1;")
        wait_until(int(executing_return), 2)

        return driver

    # Парсинг элементов кросс-референса, вытаскиваемых вручную
    # def parseCrossReference(self, driver, article, timeout=1):
    #     article_id = article[0]
    #
    #     fil_filter_article_id = self._dbHandler.insertArticle(article[1], self._dbHandler.getArticle(article_id)[2])
    #
    #     # print("parseCrossReference")
    #     # try:
    #     executing_return = \
    #         driver.execute_script("let buttons = document.getElementsByClassName(\"md-center-tabs\")[1];"
    #                               f"buttons.children[1].classList.add(\"IAmFromRussia\");"
    #                               "document.getElementsByClassName(\"IAmFromRussia\")[0].click();"
    #                               f"return 1;")
    #     wait_until(int(executing_return), timeout*2)
    #     # except JavascriptException:
    #     #     return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
    #
    #
    #     # try:
    #     text_maxPages = driver.find_elements(By.CLASS_NAME, "buttons")[0].find_elements(By.TAG_NAME, "div")[0]\
    #         .get_attribute("innerHTML")
    #     max_page = int(text_maxPages.split(" ")[2])
    #
    #     count_cross_reference_elements = int(text_maxPages.split(" ")[4])
    #     fHandler.appendToFileLog("НАЙДЕНО ЭЛЕМЕНТОВ КРОСС-РЕФЕРЕНСА:" + str(count_cross_reference_elements))
    #     # except IndexError:
    #     #     return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
    #
    #     count_pages = 1
    #     count_analogs = 0
    #
    #     while count_pages <= max_page:
    #
    #         try:
    #             div = driver.find_elements(By.CLASS_NAME, "md-body")[0]
    #             elements = div.find_elements(By.TAG_NAME, "tr")
    #         except IndexError:
    #             return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
    #
    #         analog_producer_name = ""
    #         analog_producer_id = -1
    #         analogs = [fil_filter_article_id]
    #
    #         for index, elem in enumerate(elements, start=0):
    #
    #             try:
    #                 now_analog_producer_name = elem.find_elements(By.TAG_NAME, "td")[0].get_attribute("innerHTML")
    #                 now_analog_article_name = elem.find_elements(By.TAG_NAME, "td")[1].get_attribute("innerHTML")
    #             except JavascriptException or IndexError:
    #                 return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
    #
    #             if now_analog_producer_name != analog_producer_name:
    #                 analog_producer_id = self._dbHandler.insertProducer(now_analog_producer_name)
    #                 if len(analogs) > 0:
    #                     self._dbHandler.insertArticleAnalogs(article_id, analogs)
    #                     count_analogs += len(analogs)
    #                     analogs = []
    #                 analog_producer_name = now_analog_producer_name
    #             else:
    #                 analog_article_id = self._dbHandler.insertArticle(now_analog_article_name, analog_producer_id)
    #                 analogs.append(analog_article_id)
    #
    #         # try:
    #         executing_return = \
    #             driver.execute_script("let buttons = document.getElementsByClassName(\"buttons\")[0];"
    #                                   f"buttons.children[2].classList.add(\"IAmFromRussia2\");"
    #                                   "document.getElementsByClassName(\"IAmFromRussia2\")[0].click();"
    #                                   f"return 1;")
    #         wait_until(int(executing_return), timeout)
    #         # except JavascriptException:
    #         #     return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
    #
    #         count_pages += 1
    #
    #     if count_analogs > 0 and count_cross_reference_elements > 0:
    #         return "SUCCESS"
    #
    #     return "НЕ ВЫЯВЛЕН НИ ОДИН АНАЛОГ!"



    def parseCrossReference(self, main_article_name, producer_name, cross_ref):
        main_producer_id = self._dbHandler.insertProducer(producer_name, self._catalogue_name)
        fHandler.appendToFileLog("----> PRODUCER_ID: " + str(main_producer_id))
        main_article_id = self._dbHandler.insertArticle(main_article_name, main_producer_id, self._catalogue_name)
        for elem in cross_ref:
            producer_name = elem['manufactureName']
            fHandler.appendToFileLog("\t--> PRODUCER_NAME: " + str(producer_name))
            producer_id = self._dbHandler.insertProducer(producer_name, self._catalogue_name)
            analog_article_names = elem['manufacturePartNumber']
            analog_article_ids = []
            for article_name in analog_article_names:
                analog_article_id = self._dbHandler.insertArticle(article_name, producer_id, self._catalogue_name)
                analog_article_ids.append(analog_article_id)
            self._dbHandler.insertArticleAnalogs(main_article_id, analog_article_ids, self._catalogue_name)



    def getAnalogs(self, article_url, article_id):
        pass

    def setInfo(self, article_name, producer_name, info_json):
        pass

    def saveJSON(self, article_url, article_name, type, search_request):

        fHandler.appendToFileLog("saveJSON():")

        with sync_playwright() as p:

            # Получаем Cross-Ref & Characteristics & Type
            index = 0
            limit_check = 4
            self._article_info_json = {}
            self._article_cross_ref_json = {}
            browser = p.chromium.launch()
            page = browser.new_page()
            while (len(self._article_info_json) == 0 or len(self._article_cross_ref_json) == 0) and index < limit_check:
                page.on("response", self.handle_response)
                page.goto(article_url, wait_until="load")
                index += 1
            type_json = dict([("productType", type)])
            page.context.close()
            browser.close()


            # Проверяем, что нашли
            if len(self._article_info_json) == 0:
                logging.info("\t_article_info_json is empty()")
                self._article_info_json['productMainInfo'] = {}
                self._article_info_json['productSecondaryInfo'] = {}
            if len(self._article_cross_ref_json) == 0:
                logging.info("\t_article_cross_ref_json is empty()")
                self._article_cross_ref_json['crossReference'] = []
            # print("\tJSONs получены!")


            # Склеиваем информацию в один JSON
            article_info_json = {**self._article_cross_ref_json, **self._article_info_json}
            article_info_json = {**article_info_json, **type_json}


            # Отправляем на генерацию полного JSON
            article_json = parseJSON.generateArticleJSON(article_name, "DONALDSON", "DONALDSON", article_info_json)
            # print("\tgenerateArticleJSON() -> completed")

            fHandler.appendJSONToFile("DONALDSON", article_json, search_request)
            fHandler.appendToFileLog("\tappendToFile() -> completed")
            fHandler.appendToFileLog("saveJSON() -> completed")


    with sync_playwright() as p:
        def handle_response(self, response):
            article_info_characteristic = dict()
            article_info_else = dict()
            if "fetchproductcrossreflist?" in response.url and len(self._article_cross_ref_json) == 0:
                try:
                    self._article_cross_ref_json['crossReference'] = response.json()['crossReferenceList']
                    fHandler.appendToFileLog("\t_article_cross_ref_json -> НАЙДЕН!")
                except:
                    logging.warning(traceback.format_exc())
            if "fetchProductAttrAndRecentlyViewed?" in response.url and len(self._article_info_json) == 0:
                # print(response.json())
                article_info_characteristic['productMainInfo'] = response.json()['productAttributesResponse']['dynamicAttributes']
                article_info_else['productSecondaryInfo'] = response.json()['recentlyViewedProductResponse']['recentlyViewedProducts'][0]
                self._article_info_json = {**article_info_characteristic, **article_info_else}
                fHandler.appendToFileLog("\t_article_info_json -> НАЙДЕН!")


    def goBack(self, driver):
        executing_return = driver.execute_script("window.history.back(); return 1;")
        wait_until(int(executing_return), 2)
        return driver
