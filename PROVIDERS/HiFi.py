#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time

import gevent
from loguru import logger
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
                pass
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
                        self.max_page_search = response.json()['paging']['lastPage']
                        self.total_search_count = response.json()['paging']['total']
                    except Error:
                        return

            if self.max_page_cross_ref == 0:
                if self.count_responses == 1:
                    try:
                        while 'paging' not in response.json():
                            wait_until(1, 1)
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
                page.on("response", self.searchMainResponseHandle)
                page.goto(self._catalogue_url + self.search_request + f"&p={pageNumber + 1}",
                          wait_until="networkidle")
            except PlaywrightTimeoutError:
                pass
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
            pass
        page.context.close()
        browser.close()
        return b

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


        return article_json


    def addAnalogToJSON(self, analog_article_name, analog_producer_name, json):
        if analog_article_name != "" and analog_producer_name != "":
            return JSONHandler.appendAnalogToJSON(json, analog_article_name, analog_producer_name)
        elif analog_article_name != "":
            return JSONHandler.appendOldAnalogToJSON(json, analog_article_name, self._catalogue_name)
        return json

