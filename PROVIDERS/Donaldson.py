import json
import time
import logging
import traceback

from selenium.common import WebDriverException, JavascriptException
from selenium.webdriver.common.by import By
from playwright.sync_api import sync_playwright

from PROVIDERS import Provider
from HANDLERS import FILEHandler as fHandler, JSONHandler as parseJSON
from UTILS import strings


logging.getLogger().setLevel(logging.INFO)


def wait_until(return_value, period=1):
    time.sleep(period)
    while return_value != 1:
        time.sleep(period)
    return False


class Donaldson(Provider.Provider):
    _main_url = "https://shop.donaldson.com"
    _catalogue_url = "https://shop.donaldson.com/store/ru-ru/search?Ntt="
    _article_url = "https://shop.donaldson.com/store/ru-ru/product/"
    _catalogue_name = "DONALDSON"
    max_page = 1
    _dbHandler = None

    _article_cross_ref_json = dict()
    _article_info_json = dict()

    def __init__(self, producer_id, dbHandler):
        self._producer_id = producer_id
        self._dbHandler = dbHandler
        self._producer_name = dbHandler.getProducerById(self._producer_id)

    def getMainUrl(self):
        return self._main_url

    def getArticleFromURL(self, url):
        url_attr = url.split("/")
        if len(url_attr) < 5:
            return False
        return [url_attr[6], url]


    def search(self, driver, page_number, search_request):
        if page_number > 0:
            # Переходим на др. страницу
            driver.get(self._catalogue_url + search_request + f'&No={20 * page_number}')
        elif page_number <= self.max_page:
            self.max_page = self.getPageCount(driver, search_request)
        else:
            return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

        return driver

    def getPageCount(self, driver, search_request):
        driver.get(self._catalog_url + search_request)
        lastButton = driver.find_elements(By.CLASS_NAME, "lastButton")
        if len(lastButton) > 0:
            try:
                max_page = int(lastButton[0].find_elements(By.TAG_NAME, "a")[0].get_attribute("innerHTML"))
                return max_page
            except JavascriptException or IndexError:
                return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
        return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

    def endCondision(self, page):
        if page < self.max_page:
            return True
        return False

    def parseSearchResult(self, driver):
        elements = driver.find_elements(By.CLASS_NAME, "donaldson-part-details")
        articles = []
        for index, elem in enumerate(elements, start=0):
            if index % 2 == 0:
                try:
                    spans = elem.find_elements(By.TAG_NAME, "span")
                    articles.append([spans[0].get_attribute("innerHTML"), elem.get_attribute("href")])
                except JavascriptException or IndexError:
                    return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
        return articles

    def loadArticlePage(self, driver, article_url, search_type=False):
        try:
            driver.get(article_url)
        except WebDriverException:
            return False
        return driver

    # def parseCrossReference(self, driver, article, timeout=1.5):
    #
    #     article_id = article[0]
    #     # try:
    #     executing_return = driver.execute_script(
    #         "document.getElementById(\"showAllCrossReferenceListButton\").click();" +
    #         "let blocks = document.getElementsByClassName(\"searchCrossRef\");" +
    #         "for(let i = 0; i < blocks.length; i++){" +
    #         "blocks[i].style.display = \"unset\";" +
    #         "blocks[i].parentElement.className = \"\";" +
    #         "let tag_i = blocks[i].getElementsByTagName(\"i\");" +
    #         "if(tag_i.length > 0)" +
    #         "tag_i[0].click();" +
    #         "}"
    #         "return 1;")
    #     wait_until(int(executing_return), int(timeout * 3))
    #
    #     count_analogs = 0
    #
    #     try:
    #         elements = driver.find_elements(By.CLASS_NAME, "searchCrossRef")
    #         count_cross_reference_elements = len(elements)
    #         print("НАЙДЕНО ЭЛЕМЕНТОВ КРОСС-РЕФЕРЕНСА:" + str(count_cross_reference_elements))
    #     except JavascriptException or IndexError:
    #         return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
    #
    #     analog_producer_name = ""
    #     analog_producer_id = -1
    #     analogs = []
    #     for index, elem in enumerate(elements, start=0):
    #         if index % 3 == 0:
    #             if elem.text != analog_producer_name:
    #                 if len(analogs) > 0:
    #                     self._dbHandler.insertArticleAnalogs(article_id, analogs)
    #                     count_analogs += len(analogs)
    #                     analogs = []
    #                 analog_producer_name = elem.text
    #                 analog_producer_id = self._dbHandler.insertProducer(analog_producer_name)
    #         elif index % 3 == 1:
    #             analog_article_name = elem.text
    #             analog_article_id = self._dbHandler.insertArticle(analog_article_name, analog_producer_id)
    #             analogs.append(analog_article_id)
    #
    #     if count_analogs > 0 and count_cross_reference_elements > 0:
    #         return "SUCCESS"
    #
    #     return "НЕ ВЫЯВЛЕН НИ ОДИН АНАЛОГ!"


    def parseCrossReference(self, main_article_name, producer_name, cross_ref):
        main_producer_id = self._dbHandler.insertProducer(producer_name, self._catalogue_name)
        print("----> PRODUCER_ID: " + str(main_producer_id))
        main_article_id = self._dbHandler.insertArticle(main_article_name, main_producer_id)
        for elem in cross_ref:
            producer_name = elem['manufactureName']
            print("\t--> PRODUCER_NAME: " + str(producer_name))
            producer_id = self._dbHandler.insertProducer(producer_name, self._catalogue_name)
            analog_article_names = elem['manufacturePartNumber']
            analog_article_ids = []
            for article_name in analog_article_names:
                analog_article_id = self._dbHandler.insertArticle(article_name, producer_id)
                analog_article_ids.append(analog_article_id)
            self._dbHandler.insertArticleAnalogs(main_article_id, analog_article_ids, self._catalogue_name)


    def getAnalogs(self, article_url, article_id):
        with sync_playwright() as p:
            def handle_response(response):
                if ("fetchproductcrossreflist?" in response.url):
                    items = response.json()
                    parseJSON.parseCrossRef(items, article_id, self._dbHandler)

            browser = p.chromium.launch()
            page = browser.new_page()

            page.on("response", handle_response)
            page.goto(article_url, wait_until="networkidle")

            page.context.close()
            browser.close()


    def setInfo(self, article_name, producer_name, info_json):
        producer_id = self._dbHandler.getProducerIdByNameAndCatalogueName(producer_name, self._catalogue_name)
        article_id = self._dbHandler.getArticleByName(article_name, producer_id)[0]

        main_info = info_json['productMainInfo']
        secondary_info = info_json['productSecondaryInfo']
        output_json = {**main_info, **secondary_info}

        self._dbHandler.insertArticleInfo(article_id, self._catalogue_name, output_json)


    def saveJSON(self, article_url, article_name, search_request):

        print("saveJSON():")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            index = 0
            limit_check = 2
            self._article_info_json = {}
            self._article_cross_ref_json = {}
            while (len(self._article_info_json) == 0 or len(self._article_cross_ref_json) == 0) and index < limit_check:
                page.on("response", self.handle_response)
                page.goto(article_url, wait_until="load")
                index += 1
            page.context.close()
            if len(self._article_info_json) == 0:
                logging.info("\t_article_info_json is empty()")
                self._article_info_json['productMainInfo'] = {}
                self._article_info_json['productSecondaryInfo'] = {}
            if len(self._article_cross_ref_json) == 0:
                logging.info("\t_article_cross_ref_json is empty()")
                self._article_cross_ref_json['crossReference'] = []
            # print("\tJSONs получены!")

            article_info_json = {**self._article_cross_ref_json, **self._article_info_json}
            article_json = parseJSON.generateArticleJSON(article_name, "DONALDSON", "DONALDSON", article_info_json)
            # print("\tgenerateArticleJSON() -> completed")

            fHandler.appendJSONToFile("DONALDSON", article_json, search_request)
            print("\tappendToFile() -> completed")

            browser.close()
            print("saveJSON() -> completed")


    with sync_playwright() as p:
        def handle_response(self, response):
            article_info_characteristic = dict()
            article_info_else = dict()
            if "fetchproductcrossreflist?" in response.url and len(self._article_cross_ref_json) == 0:
                try:
                    self._article_cross_ref_json['crossReference'] = response.json()['crossReferenceList']
                    print("\t_article_cross_ref_json -> НАЙДЕН!")
                except:
                    logging.warning(traceback.format_exc())
            if "fetchProductAttrAndRecentlyViewed?" in response.url and len(self._article_info_json) == 0:
                article_info_characteristic['productMainInfo'] = response.json()['productAttributesResponse']['dynamicAttributes']
                article_info_else['productSecondaryInfo'] = response.json()['recentlyViewedProductResponse']['recentlyViewedProducts'][0]
                self._article_info_json = {**article_info_characteristic, **article_info_else}
                print("\t_article_info_json -> НАЙДЕН!")


    def goBack(self, driver):
        executing_return = driver.execute_script("window.history.back(); return 1;")
        wait_until(int(executing_return), 2)
        return driver
