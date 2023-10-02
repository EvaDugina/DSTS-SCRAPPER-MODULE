import json
import time
import logging
import traceback

from bs4 import BeautifulSoup
from selenium.common import WebDriverException, JavascriptException
from selenium.webdriver.common.by import By
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from PROVIDERS import Provider
from HANDLERS import FILEHandler as fHandler, JSONHandler as parseJSON, JSONHandler
from UTILS import strings, parse

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

    def getMaxPage(self):
        return self.max_page

    def getCatalogueName(self):
        return self._catalogue_name

    # def getArticleFromURL(self, url):
    #     url_attr = url.split("/")
    #     if len(url_attr) < 5:
    #         return False
    #     return [url_attr[6], url]

    def search(self, driver, page_number, search_request):
        if page_number > 0:
            # Переходим на др. страницу
            driver.get(self._catalogue_url + search_request + f'&No={20 * page_number}')
        elif page_number == 0:
            driver.get(self._catalogue_url + search_request)
            # self.max_page = self.getPageCount(driver, search_request)
            return driver
        else:
            return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE


    def getPageCount(self, driver, search_request):
        driver.get(self._catalogue_url + search_request)
        lastButton = driver.find_elements(By.CLASS_NAME, "lastButton")
        if len(lastButton) > 0:
            try:
                max_page = int(lastButton[0].find_elements(By.TAG_NAME, "a")[0].get_attribute("innerHTML"))
                self.max_page = max_page
                return max_page
            except JavascriptException or IndexError:
                return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
        return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE

    def endCondision(self, page):
        if page < self.max_page:
            return True
        return False

    def parseSearchResult(self, driver, pageNumber=None):
        div_elements = driver.find_elements(By.CLASS_NAME, "listTile")
        articles = []
        for index, div in enumerate(div_elements, start=0):
            first_div_children = div.find_elements(By.TAG_NAME, "div")[0]
            a_elem = first_div_children.find_elements(By.CLASS_NAME, "donaldson-part-details")[0]
            changed_detail = first_div_children.find_elements(By.CLASS_NAME, "hideInMobile")
            changedDetailArticleName = ""
            # print(changed_detail.get_attribute('class'))
            if len(changed_detail) > 0:
                changed_detail = changed_detail[0]
                changed_detail = changed_detail.find_elements(By.TAG_NAME, "span")
                if len(changed_detail) > 1:
                    changedDetailArticleName = changed_detail[1].get_attribute(
                        "innerHTML")
                    if len(changedDetailArticleName.split(" ")) > 1 and parse.hasDigits(changedDetailArticleName.split(" ")[1]):
                        changedDetailArticleName = changedDetailArticleName.split(" ")[1]
                else:
                    changedDetailArticleName = ""

            flag_analog = False
            analog_producer_name = ""
            analog_article_name = ""
            div_analog_producer = first_div_children.find_elements(By.CLASS_NAME, "manufacturer-details")
            if len(div_analog_producer) > 0:
                analog_by_search = div_analog_producer[0]
                if len(analog_by_search.find_elements(By.TAG_NAME, "span")) == 4:
                    analog_producer_name = analog_by_search.find_elements(By.TAG_NAME, "span")[0] \
                        .find_elements(By.TAG_NAME, "span")[0].get_attribute("innerHTML")
                    analog_article_name = analog_by_search.find_elements(By.TAG_NAME, "span")[2] \
                        .find_elements(By.TAG_NAME, "span")[0].get_attribute("innerHTML")
                    flag_analog = True

            try:
                spans = a_elem.find_elements(By.TAG_NAME, "span")
                if changedDetailArticleName != "":
                    articles.append(
                        [spans[0].get_attribute("innerHTML"), a_elem.get_attribute("href"), changedDetailArticleName])
                else:
                    if flag_analog:
                        articles.append(
                            [spans[0].get_attribute("innerHTML"), a_elem.get_attribute("href"), analog_article_name,
                             analog_producer_name])
                    else:
                        articles.append([spans[0].get_attribute("innerHTML"), a_elem.get_attribute("href")])
            except JavascriptException or IndexError:
                return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
        return articles

    def loadArticlePage(self, driver, article_url, search_type=False):
        try:
            driver.get(article_url)
        except WebDriverException:
            return False
        return driver

    def getArticleType(self, driver) -> str:
        parsed_html = BeautifulSoup(driver.page_source.encode('utf-8'), "html.parser")
        return parsed_html.body.find('div', attrs={'class': 'prodSubTitleMob'}).text

    def parseCrossReference(self, main_article_name, producer_name, type, cross_ref):
        main_producer_id = self._dbHandler.insertProducer(producer_name, self._catalogue_name)
        fHandler.appendToFileLog("----> PRODUCER_ID: " + str(main_producer_id))
        main_article_id = self._dbHandler.insertArticle(main_article_name, main_producer_id, self._catalogue_name)
        for elem in cross_ref:
            producer_name = elem['producerName']
            fHandler.appendToFileLog("\t--> PRODUCER_NAME: " + str(producer_name))
            producer_id = self._dbHandler.insertProducer(producer_name, self._catalogue_name)
            analog_article_names = elem['articleNames']
            analog_article_ids = []
            for article_name in analog_article_names:
                if elem['type'] == "old":
                    analog_article_id = self._dbHandler.insertArticle(article_name, producer_id, self._catalogue_name,
                                                                      1)
                else:
                    analog_article_id = self._dbHandler.insertArticle(article_name, producer_id, self._catalogue_name)
                analog_article_ids.append(analog_article_id)
            self._dbHandler.insertArticleAnalogs(main_article_id, analog_article_ids, self._catalogue_name)

    # def getAnalogs(self, article_url, article_id):
    #     with sync_playwright() as p:
    #         def handle_response(response):
    #             if ("fetchproductcrossreflist?" in response.url):
    #                 items = response.json()
    #                 parseJSON.parseCrossRef(items, article_id, self._dbHandler)
    #
    #         browser = p.chromium.launch()
    #         page = browser.new_page()
    #
    #         page.on("response", handle_response)
    #         page.goto(article_url, wait_until="networkidle")
    #
    #         page.context.close()
    #         browser.close()

    def setInfo(self, article_name, producer_name, info_json):
        producer_id = self._dbHandler.getProducerIdByNameAndCatalogueName(producer_name, self._catalogue_name)
        article_id = self._dbHandler.getArticleByName(article_name, producer_id)[0]

        main_info = info_json['articleMainInfo']
        secondary_info = info_json['articleSecondaryInfo']
        output_json = {**main_info, **secondary_info}

        self._dbHandler.insertCharacteristics(main_info)

        type = info_json['articleDescription']
        url = f"{self._article_url}{article_name}/{info_json['articleSecondaryInfo']['articleId']}"

        self._dbHandler.insertArticleInfo(article_id, self._catalogue_name, url, type, output_json)

    def saveJSON(self, driver, article_url, article_name, type, search_request, article):

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
                try:
                    page.set_default_timeout(5000)
                    page.on("response", self.handle_response)
                    page.goto(article_url, wait_until="networkidle")
                except PlaywrightTimeoutError:
                    fHandler.appendToFileLog("PlaywrightTimeoutError!")
                index += 1
            page.context.close()
            browser.close()

            # Проверяем, что нашли
            if len(self._article_info_json) == 0:
                logging.info("\t_article_info_json is empty()")
                self._article_info_json['articleMainInfo'] = {}
                self._article_info_json['articleSecondaryInfo'] = {}
            if len(self._article_cross_ref_json) == 0:
                logging.info("\t_article_cross_ref_json is empty()")
                self._article_cross_ref_json['crossReference'] = []
            # print("\tJSONs получены!")

            # Приводим JSONS к нужному формату
            cross_ref_json = []
            for elem in self._article_cross_ref_json['crossReference']:
                new_json = {
                    "producerName": elem['manufactureName'],
                    "articleNames": elem['manufacturePartNumber'],
                    "type": "real"
                }
                cross_ref_json.append(new_json)
            self._article_cross_ref_json['crossReference'] = cross_ref_json

            self._article_info_json['articleMainInfo'] = self._article_info_json['productMainInfo']
            self._article_info_json.pop('productMainInfo')

            self._article_info_json['articleSecondaryInfo'] = {
                "articleId": self._article_info_json['productSecondaryInfo']['productId'],
                "imageUrls": [self._article_info_json['productSecondaryInfo']['imageUrl']]
            }
            self._article_info_json.pop('productSecondaryInfo')

            type_json = dict([("articleDescription", type)])

            # Склеиваем информацию в один JSON
            article_info_json = {**self._article_cross_ref_json, **self._article_info_json}
            article_info_json = {**article_info_json, **type_json}

            # Отправляем на генерацию полного JSON
            article_json = parseJSON.generateArticleJSON(article_name, self._catalogue_name, self._catalogue_name,
                                                         article_info_json)
            article_json = self.addAnalogToJSON(article, article_json)

            # print("\tgenerateArticleJSON() -> completed")

            # fHandler.appendJSONToFile("DONALDSON", article_json, search_request)
            fHandler.appendToFileLog("\tappendToFile() -> completed")
            fHandler.appendToFileLog("saveJSON() -> completed")

            return article_json

    with sync_playwright() as p:
        def handle_response(self, response):
            if len(self._article_cross_ref_json) < 1:
                if "fetchproductcrossreflist?" in response.url:
                    try:
                        if 'crossReferenceList' in response.json():
                            self._article_cross_ref_json['crossReference'] = response.json()['crossReferenceList']
                            fHandler.appendToFileLog("\t_article_cross_ref_json -> НАЙДЕН!")
                    except:
                        logging.warning(traceback.format_exc())

            if len(self._article_info_json) < 1:
                if "fetchProductAttrAndRecentlyViewed?" in response.url:
                    article_info_characteristic = dict()
                    article_info_else = dict()
                    if 'productAttributesResponse' in response.json():
                        article_info_characteristic['productMainInfo'] = response.json()['productAttributesResponse'][
                            'dynamicAttributes']
                    if 'recentlyViewedProductResponse' in response.json():
                        article_info_else['productSecondaryInfo'] = \
                            response.json()['recentlyViewedProductResponse']['recentlyViewedProducts'][0]
                    self._article_info_json = {**article_info_characteristic, **article_info_else}
                    fHandler.appendToFileLog("\t_article_info_json -> НАЙДЕН!")

    def addAnalogToJSON(self, article, json):
        if len(article) == 4:
            return JSONHandler.appendAnalogToJSON(json, article[2], article[3])
        elif len(article) == 3:
            return JSONHandler.appendOldAnalogToJSON(json, article[2], self._catalogue_name)
        return json


def goBack(self, driver):
    executing_return = driver.execute_script("window.history.back(); return 1;")
    wait_until(int(executing_return), 2)
    return driver
