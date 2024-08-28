#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time

import gevent
from selenium.common import WebDriverException
from selenium.webdriver.common.by import By
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Error

import Decorators
from PROVIDERS.Provider import Provider
from HANDLERS import FILEHandler as fHandler, JSONHandler, PLAYWRIGHTHandler
from UTILS import strings, parse

PLAYWRIGHT = PLAYWRIGHTHandler.PLAYWRIGHT


def wait_until(return_value, period=1):
    gevent.sleep(period)
    while return_value != 1:
        gevent.sleep(period)
    return False


class HiFi(Provider):
    _main_url = "https://catalog.hifi-filter.com/en-GB"
    _cross_referense_url = "https://catalog.hifi-filter.com/en-GB/search/global/cross-reference?q="
    _catalogue_url = "https://catalog.hifi-filter.com/en-GB/search/global/product?q="
    _article_url = "https://catalog.hifi-filter.com/en-GB/product/"
    _catalogue_name = "HIFI"
    max_page_cross_ref = 0
    max_page_search = 0
    _dbHandler = None

    _article_cross_ref_json = dict()
    _article_info_json = dict()

    _search_array = []
    _cross_reference = []

    _playwright = None

    count_responses = 0
    search_request = ""
    total_cross_ref_count = -1
    total_search_count = -1
    article_id = ""
    article_url = ""

    def __init__(self, producer_id, dbHandler):
        super().__init__(producer_id, dbHandler)
        self._playwright = PLAYWRIGHT

    def getMainUrl(self):
        return self._main_url

    def getProductUrl(self, article_name):
        return self._article_url + article_name

    def getMaxPage(self):
        return self.max_page

    def getCatalogueName(self):
        return self._catalogue_name

    @Decorators.time_decorator
    def getPageCount(self, driver, search_request):
        self.search_request = search_request

        index = 0
        limit_check = 3
        browser = self._playwright.chromium.launch(headless=False)
        page = browser.new_page()
        self.count_responses = 0
        while (self.max_page_search == 0 or self.max_page_cross_ref == 0 or
                self.total_search_count == -1 or self.total_cross_ref_count == -1) and index < limit_check:
            try:
                # page.set_default_timeout(5000)
                page.on("response", self.searchPagesHandle)
                page.goto(self._catalogue_url + search_request, wait_until="networkidle")
            except PlaywrightTimeoutError:
                fHandler.appendToFileLog("PlaywrightTimeoutError!")
            index += 1
        page.context.close()
        browser.close()

        if self.max_page_search is None:
            self.max_page_search = 0
            self.total_cross_ref_count = 0

        if self.max_page_cross_ref is None:
            self.max_page_cross_ref = 0
            self.total_cross_ref_count = 0

        if self.max_page_search + self.max_page_cross_ref == 0:
            return -1

        return max(self.max_page_search, self.max_page_cross_ref)


    def searchPagesHandle(self, response):
        if self.max_page_search != 0 and self.max_page_cross_ref != 0:
            return None

        if "search?id=" in response.url:
            self.count_responses += 1
            if self.max_page_search == 0:
                if self.count_responses == 2:
                    try:
                        while 'paging' not in response.json():
                            wait_until(1, 1)
                        # print(response.json()['paging'])
                        self.max_page_search = response.json()['paging']['lastPage']
                        self.total_search_count = response.json()['paging']['total']
                    except Error:
                        return

            if self.max_page_cross_ref == 0:
                if self.count_responses == 1:
                    try:
                        while 'paging' not in response.json():
                            wait_until(1, 1)
                        # print(response.json()['paging'])
                        self.max_page_cross_ref = response.json()['paging']['lastPage']
                        self.total_cross_ref_count = response.json()['paging']['total']
                    except Error:
                        return

    def endCondition(self, page):
        if page < self.max_page_search + self.max_page_cross_ref:
            return True
        return False

    def endCondisionSearch(self, page):
        if page < self.max_page_search:
            return True
        return False

    def endCondisionCrossRef(self, page):
        if page < self.max_page_cross_ref:
            return True
        return False

    def search(self, driver, page_number, search_request):
        return True
        # На случай, если использовать driver
        # if page_number > 0:
        #     # Переходим на др. страницу
        #     driver.get(self._catalogue_url + search_request + f'&p={page_number + 1}')
        #     return True
        # elif page_number == 0:
        #     driver.get(self._catalogue_url + search_request)
        #     # self.max_page = self.getPageCount(driver, search_request)
        #     return True
        # else:
        #     return False

    def parseSearchResult(self, driver, pageNumber):
        self._search_array = []
        self._cross_reference = []

        index = 0
        limit_check = 3
        browser = self._playwright.chromium.launch(headless=False)
        page = browser.new_page()
        self.count_responses = 0
        while (len(self._search_array) < 1 or len(self._cross_reference) < 1) and index < limit_check:
            try:
                # page.set_default_timeout(5000)
                page.on("response", self.searchMainResponseHandle)
                page.goto(self._catalogue_url + self.search_request + f"&p={pageNumber + 1}",
                          wait_until="networkidle")
            except PlaywrightTimeoutError:
                fHandler.appendToFileLog("PlaywrightTimeoutError!")
            if index == limit_check - 2:
                page.wait_for_timeout(5000)
            index += 1
        page.context.close()
        browser.close()

        articles = []
        if len(self._search_array) > 0:
            articles += self._search_array
        if len(self._cross_reference) > 0:
            articles += self._cross_reference
        return articles

    def parseCrossReferenceResult(self, driver, pageNumber):
        pass

    def searchMainResponseHandle(self, response):
        if "search?id=" in response.url:
            try:
                while 'results' not in response.json():
                    wait_until(1, 1)

                arrayElements = response.json()['results']
            except Error:
                return

            # Вытаскиваем элементы Кросс-Референса
            if len(arrayElements) > 0 and 'brand' in arrayElements[0] and len(self._cross_reference) < 1:
                for elem in arrayElements:
                    analog_article_name = parse.concatArticleName(elem['reference'])
                    analog_producer_name = elem['brand']['name']

                    flag_old = False
                    flag_changed = False
                    if analog_producer_name == "HIFI OLD NUMBER":
                        analog_producer_name = "HIFI"
                        flag_old = True
                        flag_changed = True

                    products = elem['products']
                    if len(products) > 0:
                        product = products[0]
                        article_id = parse.convertSpacesToURLSpaces(product['id'])
                        article_name = parse.concatArticleName(product['reference'])

                        article = []

                        article.append(article_name)
                        article.append(self._article_url + article_name + "/" + article_id)
                        article.append(analog_article_name)
                        if flag_old and flag_changed:
                            pass
                        else:
                            article.append(analog_producer_name)

                        self._cross_reference.append(article)

            # Вытаскиваем элементы обычного поиска
            elif len(arrayElements) > 0 and len(self._search_array) < 1 \
                    and 'brand' not in arrayElements[0] and 'catalog' not in arrayElements[0]:
                for elem in arrayElements:
                    article_id = parse.convertSpacesToURLSpaces(elem['id'])
                    article_name = parse.concatArticleName(elem['reference'])
                    article = [article_name, self._article_url + article_name + "/" + article_id]
                    self._search_array.append(article)

    def loadArticlePage(self, driver, article_url, search_type=False):
        try:
            driver.implicitly_wait(20)
            driver.get(article_url)
            self.article_url = article_url
        except WebDriverException:
            return False
        return driver



    def getArticleType(self, driver) -> str:
        b = ""
        browser = self._playwright.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            # page.set_default_timeout(5000)
            page.goto(self.article_url, wait_until="load")
            b = page.locator("#product-designation").text_content()
            b = b.replace("<!---->", "")
        except PlaywrightTimeoutError:
            fHandler.appendToFileLog("PlaywrightTimeoutError!")
        page.context.close()
        browser.close()
        return b

    def parseCrossReference(self, main_article_name, producer_name, type, cross_ref):
        main_producer_id = self._dbHandler.insertProducer(producer_name, self._catalogue_name)
        fHandler.appendToFileLog("----> PRODUCER_ID: " + str(main_producer_id))
        if type == "real":
            main_article_id = self._dbHandler.insertArticle(main_article_name, main_producer_id, self._catalogue_name,
                                                            0)
        else:
            main_article_id = self._dbHandler.insertArticle(main_article_name, main_producer_id, self._catalogue_name,
                                                            1)
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


    def saveJSON(self, driver, article_url, article_name, type, search_request, analog_article_name, analog_producer_name):

        fHandler.appendToFileLog("saveJSON():")

        article_id = article_url.split("/")[-1].split("%20")[0]

        # Получаем Cross-Reference
        _article_cross_ref_json = {}
        _article_cross_ref_json['crossReference'] = []
        analogs = driver.find_elements(By.CLASS_NAME, "compatible-application")
        if len(analogs) > 0:
            for analog in analogs:
                analog_producer_name = analog.find_element(By.TAG_NAME, "h4").get_attribute("innerHTML")
                new_json = {
                    "producerName": analog_producer_name,
                    "articleNames": [],
                    "type": "real"
                }
                articles = analog.find_element(By.TAG_NAME, "div").find_elements(By.XPATH, "./*")
                for article in articles:
                    analog_article = article.find_element(By.TAG_NAME, "a")
                    analog_article_name = analog_article.text.replace("$", "").strip()
                    new_json['articleNames'].append(analog_article_name)
                _article_cross_ref_json['crossReference'].append(new_json)

        # Получаем характеристики
        _article_info_json = {}
        _article_info_json['articleMainInfo'] = {}
        if len(driver.find_elements(By.CLASS_NAME, "attribute")) > 1:
            for div_attribute in driver.find_elements(By.CLASS_NAME, "attribute"):
                characteristic_name = div_attribute.find_element(By.TAG_NAME, "h4").get_attribute("innerHTML")
                spans_characteristic_value = div_attribute.find_elements(By.TAG_NAME, "span")
                characteristic_value = ""
                if len(spans_characteristic_value) > 1:
                    characteristic_value = spans_characteristic_value[1].get_attribute("innerHTML")
                _article_info_json['articleMainInfo'][characteristic_name] = f"{characteristic_value}"

        #  Вытаскиваем изображения
        imageURLS = []
        figures = driver.find_elements(By.TAG_NAME, "figure")
        for figure in figures:
            imageURLS.append(figure.find_element(By.TAG_NAME, "img").get_attribute("src"))

        _article_info_json['articleSecondaryInfo'] = {
            "articleId": article_id,
            "imageUrls": imageURLS
        }

        type_json = dict([("articleDescription", type)])

        # Склеиваем информацию в один JSON
        article_info_json = {**_article_cross_ref_json, **_article_info_json}
        article_info_json = {**article_info_json, **type_json}

        # Отправляем на генерацию полного JSON
        article_json = JSONHandler.generateArticleJSON(article_name, self._catalogue_name, self._catalogue_name,
                                                     article_info_json)
        article_json = self.addAnalogToJSON(analog_article_name, analog_producer_name, article_json)

        # print("\tgenerateArticleJSON() -> completed")

        # fHandler.appendJSONToFile("DONALDSON", article_json, search_request)
        fHandler.appendToFileLog("\tappendToFile() -> completed")
        fHandler.appendToFileLog("saveJSON() -> completed")

        return article_json


    # def saveJSONwithPlaywright(self, driver, article_url, article_name, type, search_request, analog_article_name, analog_producer_name):
    #
    #     fHandler.appendToFileLog("saveJSON():")
    #
    #     article_id = article_url.split("/")[-1].split("%20")[0]
    #
    #     # Получаем Cross-Ref
    #     index = 0
    #     limit_check = 3
    #     self._article_cross_ref_json = {}
    #     browser = self._playwright.chromium.launch(headless=False)
    #     page = browser.new_page()
    #     while len(self._article_cross_ref_json) == 0 and index < limit_check:
    #         try:
    #             page.set_default_timeout(10000)
    #             page.on("response", self.handle_response)
    #             page.goto(article_url, wait_until="networkidle")
    #         except PlaywrightTimeoutError:
    #             fHandler.appendToFileLog("PlaywrightTimeoutError!")
    #         index += 1
    #     page.context.close()
    #     browser.close()
    #
    #     # Получаем характеристики
    #     self._article_info_json['articleMainInfo'] = {}
    #     if len(driver.find_elements(By.CLASS_NAME, "attribute")) > 1:
    #         for div_attribute in driver.find_elements(By.CLASS_NAME, "attribute"):
    #             characteristic_name = div_attribute.find_elements(By.TAG_NAME, "h4")[0].get_attribute("innerHTML")
    #             spans_characteristic_value = div_attribute.find_elements(By.TAG_NAME, "span")
    #             characteristic_value = ""
    #             if len(spans_characteristic_value) > 1:
    #                 characteristic_value = spans_characteristic_value[1].get_attribute("innerHTML")
    #             self._article_info_json['articleMainInfo'][characteristic_name] = f"{characteristic_value}"
    #
    #     #  Вытаскиваем изображения
    #     imageURLS = []
    #     figures = driver.find_elements(By.TAG_NAME, "figure")
    #     for figure in figures:
    #         imageURLS.append(figure.find_elements(By.TAG_NAME, "img")[0].get_attribute("src"))
    #
    #     # Проверяем, что нашли
    #     if len(self._article_cross_ref_json) == 0:
    #         fHandler.appendToFileLog("\t_article_cross_ref_json is empty()")
    #         self._article_cross_ref_json['crossReference'] = []
    #     # print("\tJSONs получены!")
    #
    #     # Приводим JSONS к нужному формату
    #     cross_ref_json = []
    #     for key in self._article_cross_ref_json['crossReference']:
    #         new_json = {
    #             "producerName": key,
    #             "articleNames": [],
    #             "type": "real"
    #         }
    #         for analog in list(self._article_cross_ref_json['crossReference'][key]):
    #             new_json['articleNames'].append(analog['model']['label'])
    #         cross_ref_json.append(new_json)
    #     self._article_cross_ref_json['crossReference'] = cross_ref_json
    #
    #     self._article_info_json['articleSecondaryInfo'] = {
    #         "articleId": article_id,
    #         "imageUrls": imageURLS
    #     }
    #
    #     type_json = dict([("articleDescription", type)])
    #
    #     # Склеиваем информацию в один JSON
    #     article_info_json = {**self._article_cross_ref_json, **self._article_info_json}
    #     article_info_json = {**article_info_json, **type_json}
    #
    #     # Отправляем на генерацию полного JSON
    #     article_json = JSONHandler.generateArticleJSON(article_name, self._catalogue_name, self._catalogue_name,
    #                                                  article_info_json)
    #     article_json = self.addAnalogToJSON(analog_article_name, analog_producer_name, article_json)
    #
    #     # print("\tgenerateArticleJSON() -> completed")
    #
    #     # fHandler.appendJSONToFile("DONALDSON", article_json, search_request)
    #     fHandler.appendToFileLog("\tappendToFile() -> completed")
    #     fHandler.appendToFileLog("saveJSON() -> completed")
    #
    #     return article_json


    # def handle_response(self, response):
    #     if len(self._article_cross_ref_json) < 1:
    #         if self.article_id.split("%20")[0] in response.url:
    #             try:
    #                 if response.json() and 'id' not in response.json():
    #                     self._article_cross_ref_json['crossReference'] = response.json()
    #                     fHandler.appendToFileLog("\t_article_cross_ref_json -> FOUNDED!")
    #             except json.decoder.JSONDecodeError:
    #                 return
    #             except TypeError:
    #                 return
    #             except Error:
    #                 return
    #             except ValueError:
    #                 return

    # def addAnalogToJSON(self, article, json):
    #     if len(article) == 4:
    #         return JSONHandler.appendAnalogToJSON(json, article[2], article[3])
    #     elif len(article) == 3:
    #         return JSONHandler.appendOldAnalogToJSON(json, article[2], self._catalogue_name)
    #     return json

    def addAnalogToJSON(self, analog_article_name, analog_producer_name, json):
        if analog_article_name != "" and analog_producer_name != "":
            return JSONHandler.appendAnalogToJSON(json, analog_article_name, analog_producer_name)
        elif analog_article_name != "":
            return JSONHandler.appendOldAnalogToJSON(json, analog_article_name, self._catalogue_name)
        return json

