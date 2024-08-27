#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gevent import monkey
monkey.patch_all()

import json
import time
import logging

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import WebDriverException, JavascriptException
from selenium.webdriver.common.by import By
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error

from PROVIDERS import Provider
from HANDLERS import FILEHandler as fHandler, JSONHandler as parseJSON, JSONHandler


logging.getLogger().setLevel(logging.INFO)
PLAYWRIGHT = sync_playwright().start()


def wait_until(return_value, period=1):
    time.sleep(period)
    while return_value != 1:
        time.sleep(period)
    return False


class Mann(Provider.Provider):
    _main_url = "https://www.mann-filter.com/ru-ru/catalog"
    _catalogue_url = ["https://www.mann-filter.com/ru-ru/catalog/search-results.html?mode=smart&smart=", "&smartSearchTerm="]
    _article_url = ["https://www.mann-filter.com/ru-ru/catalog/search-results/product.html/", "_mann-filter.html"]
    _catalogue_name = "MANN"
    _dbHandler = None

    max_page_cross_ref = 0
    max_page_search = 0
    total_cross_ref_count = -1
    total_search_count = -1
    max_page = -1

    def __init__(self, producer_id, dbHandler):
        super().__init__(producer_id, dbHandler)
        self._playwright = PLAYWRIGHT

    def getMainUrl(self):
        return self._main_url

    def getProductUrl(self, article_name):
        return f"{self._article_url[0]}{article_name}{self._article_url[1]}"

    def getSearchUrl(self, article_name):
        return f"{self._catalogue_url[0]}{article_name}{self._catalogue_url[1]}{article_name}"

    def getCatalogueName(self):
        return self._catalogue_name

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
                page.on("response", self.searchPagesHandle)
                page.goto(self.getSearchUrl(search_request), wait_until="networkidle")
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

        self.max_page = max(self.max_page_search, self.max_page_cross_ref)

        return self.max_page

    def searchPagesHandle(self, response):
        if self.max_page_search != 0 and self.max_page_cross_ref != 0:
            return None

        if "catalog-prod?query=" in response.url:
            try:
                while 'data' not in response.json():
                    wait_until(1, 1)
                crossReference = response.json()['data']['catalogSearch']['crossReference']
                self.max_page_cross_ref = crossReference['pageInfo']['totalPages']
                self.total_cross_ref_count = crossReference['totalCount']

                products = response.json()['data']['catalogSearch']['products']
                self.max_page_search = products['pageInfo']['totalPages']
                self.total_search_count = products['totalCount']

            except Error:
                return

    def endCondition(self, page):
        if page < self.max_page:
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

    def choseProducts(self, driver):
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'cmp-tabs__tablist')))
        li_products = driver.find_element(By.CLASS_NAME, "cmp-tabs__tablist")\
            .find_element(By.CSS_SELECTOR, "[data-filter-code='Products']")
        try:
            li_products.click()
        except WebDriverException:
            pass

    def choseCrossRef(self, driver):
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'cmp-tabs__tablist')))
        li_crossRef = driver.find_element(By.CLASS_NAME, "cmp-tabs__tablist") \
            .find_element(By.CSS_SELECTOR, "[data-filter-code='CrossReference']")
        try:
            li_crossRef.click()
        except WebDriverException:
            pass


    # Поиск
    def search(self, driver, page_number, search_request):
        driver.get(self.getSearchUrl(self.search_request))

        if page_number > 0:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'cmp-pagination')))
            selector = driver.find_element(By.CLASS_NAME, "cmp-pagination").find_element(By.CLASS_NAME, "cmp-form-options__field--drop-down")
            selector.click()
            selector.find_elements(By.TAG_NAME, "option")[page_number].click()
        return True

    def searchProducts(self, driver, page_number, search_request):
        driver.get(self.getSearchUrl(self.search_request))

        self.choseProducts(driver)

        if page_number > 0:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'cmp-pagination')))
            selector = driver.find_element(By.CLASS_NAME, "cmp-pagination").find_element(By.CLASS_NAME, "cmp-form-options__field--drop-down")
            selector.click()
            selector.find_elements(By.TAG_NAME, "option")[page_number].click()
        return True

    def searchCrossRef(self, driver, page_number, search_request):
        driver.get(self.getSearchUrl(self.search_request))

        self.choseCrossRef(driver)

        if page_number > 0:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'cmp-pagination')))
            selector = driver.find_element(By.CLASS_NAME, "cmp-pagination").find_element(By.CLASS_NAME,
                                                                                         "cmp-form-options__field--drop-down")
            selector.click()
            selector.find_elements(By.TAG_NAME, "option")[page_number].click()
        return True

    # Парсинг одну страницу поиска
    def parseSearchResult(self, driver, pageNumber):
        self._search_array = []
        self._cross_reference = []
        self.pageNumber = pageNumber

        articles = []
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'cmp-catalog__results-result-item-description')))
        div_elements = driver.find_elements(By.CLASS_NAME, "cmp-catalog__results-result-item-description")
        for row in div_elements:
            block = row.find_element(By.CLASS_NAME, "cmp-catalog__results-result-item-product-key-block-title")
            article_name = block.find_element(By.CLASS_NAME, "cmp-text__paragraph").text.replace(" ", "").upper()
            articles.append([article_name, self.getProductUrl(article_name.lower())])

        return articles

    def parseCrossReferenceResult(self, driver, pageNumber):
        self._search_array = []
        self._cross_reference = []
        self.pageNumber = pageNumber

        articles = []
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'cmp-table-data__row')))
        div_elements = driver.find_elements(By.CLASS_NAME, "cmp-table-data__row")
        for row in div_elements:
            cells = row.find_elements(By.CLASS_NAME, "cmp-table-data__cell")
            analog_article_name = cells[0].find_element(By.CLASS_NAME, "cmp-text__paragraph").text.replace(" ", "").upper()
            analog_producer_name = cells[1].find_element(By.CLASS_NAME, "cmp-text__paragraph").text.replace(" ", "").upper()
            article_name = cells[2].find_element(By.CLASS_NAME, "cmp-text__paragraph").text.replace(" ", "").upper()
            if article_name == "нет аналога".replace(" ", "").upper():
                continue
            articles.append(
                [article_name, self.getProductUrl(article_name.lower()), analog_article_name, analog_producer_name])

        return articles

    # Загрузка страницы товара
    def loadArticlePage(self, driver, article_url, search_type=False):

        try:
            driver.get(article_url)
        except WebDriverException:
            return False

        return driver

    def getArticleType(self, driver) -> str:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'cmp-product__title-family')))
        return driver.find_element(By.CLASS_NAME, "cmp-product__title-family").text

    def parseCrossReference(self, main_article_name, producer_name, type, cross_ref):
        main_producer_id = self._dbHandler.insertProducer(producer_name, self._catalogue_name)
        fHandler.appendToFileLog("----> PRODUCER_ID: " + str(main_producer_id))

        if type == "real":
            main_article_id = self._dbHandler.insertArticle(main_article_name, main_producer_id, self._catalogue_name, 0)
        else:
            main_article_id = self._dbHandler.insertArticle(main_article_name, main_producer_id, self._catalogue_name, 1)

        last_producer_name = ""
        producer_id = -1
        analog_article_ids = []
        index = 0
        for elem in cross_ref:
            producer_name = elem['producerName']
            if last_producer_name == producer_name:
                article_name = elem['articleNames'][0]
                if elem['type'] == "old":
                    analog_article_id = self._dbHandler.insertArticle(article_name, producer_id, self._catalogue_name,
                                                                      1)
                else:
                    analog_article_id = self._dbHandler.insertArticle(article_name, producer_id, self._catalogue_name)
                analog_article_ids.append(analog_article_id)

            else:
                if index != 0:
                    self._dbHandler.insertArticleAnalogs(main_article_id, analog_article_ids, self._catalogue_name)

                last_producer_name = producer_name

                fHandler.appendToFileLog("\t--> PRODUCER_NAME: " + str(producer_name))
                producer_id = self._dbHandler.insertProducer(producer_name, self._catalogue_name)
                analog_article_ids = []

                article_name = elem['articleNames'][0]
                if elem['type'] == "old":
                    analog_article_id = self._dbHandler.insertArticle(article_name, producer_id, self._catalogue_name,
                                                                      1)
                else:
                    analog_article_id = self._dbHandler.insertArticle(article_name, producer_id, self._catalogue_name)
                analog_article_ids.append(analog_article_id)

            if index == len(cross_ref)-1:
                self._dbHandler.insertArticleAnalogs(main_article_id, analog_article_ids, self._catalogue_name)

            index += 1


    def setInfo(self, article_name, producer_name, info_json):
        pass

    def saveJSON(self, driver, article_url, article_name, description, search_request, analog_article_name, analog_producer_name):

        fHandler.appendToFileLog("saveJSON():")

        flag_replaced = False
        flag_replace = False
        replaced_article_names = []
        replace_article_names = []
        article_type = "real"

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'cmp-product-status__status-text')))
        p_status = driver.find_element(By.CLASS_NAME, "cmp-product-status__status-text").find_element(By.TAG_NAME, "p")
        change_el = driver.find_elements(By.CLASS_NAME, "cmp-tag")
        if len(change_el) > 0:
            flag_replaced = True
            replaced_article_names.append(change_el[0].find_element(By.TAG_NAME, "a").text)
            article_type = "old"

        elif "Производство остановлено" in p_status.text:
            article_type = "old"

        elif "Временно недоступен" in p_status.text:
            pass

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'oeNumbers')))
        rows_analogs = driver.find_element(By.ID, "oeNumbers").find_elements(By.CLASS_NAME, "cmp-accordion__item")
        cross_reference = []
        for row in rows_analogs:
            analog_producer_name1 = row.find_element(By.CLASS_NAME, "cmp-accordion__header")\
                .find_element(By.CLASS_NAME, "cmp-accordion__title").get_attribute("innerHTML").strip()
            analog_article_names = []
            lis_article_names = row.find_element(By.TAG_NAME, "ul").find_elements(By.TAG_NAME, "li")
            for li in lis_article_names:
                analog_article_names.append(li.get_attribute("innerHTML").replace(" ", ""))
            analogs = {
                "producerName": analog_producer_name1,
                "articleNames": analog_article_names,
                "type": "real"
            }
            cross_reference.append(analogs)


        # Получаем характеристики
        self._article_info_json['articleMainInfo'] = {}
        div_characteristics = driver.find_elements(By.CLASS_NAME, "cmp-product__summary")
        if len(div_characteristics) > 0:
            lis = div_characteristics[0].find_elements(By.TAG_NAME, "li")
            for li in lis:
                text = li.get_attribute("innerHTML")
                if ";" in text:
                    characteristcs = text.split(";")
                    for characteristic in characteristcs:
                        name, value = characteristic.split(" = ")
                        self._article_info_json['articleMainInfo'][name] = f"{value}"
                elif " : " in text:
                    name, value = text.split(" : ")
                    self._article_info_json['articleMainInfo'][name] = f"{value}"
                else:
                    self._article_info_json['articleMainInfo']["Дополнительно"] = f"{text}"

        # Получаем изображение
        imageURLS = []
        images = driver.find_element(By.CLASS_NAME, "cmp-product__gallery-container--dynamic")\
            .find_elements(By.TAG_NAME, "img")
        if len(images) > 0:
            for image in images:
                if image.get_attribute("alt") == "":
                    break
                imageURLS.append(image.get_attribute("src"))

        self._article_cross_ref_json['crossReference'] = cross_reference

        self._article_info_json['articleSecondaryInfo'] = {
            "articleId": article_name,
            "imageUrls": imageURLS
        }

        type_json = dict([("articleDescription", description)])

        # Склеиваем информацию в один JSON
        article_info_json = {**self._article_cross_ref_json, **self._article_info_json}
        article_info_json = {**article_info_json, **type_json}

        # Отправляем на генерацию полного JSON
        article_json = parseJSON.generateArticleJSON(article_name, self._catalogue_name, self._catalogue_name,
                                                        article_info_json, article_type)
        article_json = self.addAnalogToJSON(analog_article_name, analog_producer_name, article_json)

        if flag_replaced:
            article_json = JSONHandler.appendAnalogsToJSON(article_json, replaced_article_names, self._catalogue_name)
        if flag_replace:
            article_json = JSONHandler.appendOldAnalogsToJSON(article_json, replace_article_names, self._catalogue_name)

        # fHandler.appendJSONToFile("DONALDSON", article_json, search_request)
        fHandler.appendToFileLog("\tappendToFile() -> completed")
        fHandler.appendToFileLog("saveJSON() -> completed")

        return article_json

    def handle_response(self, response):
        if len(self._article_cross_ref_json) > 0:
            return None

        if "get_product_oe_references" in response.url:
            try:
                if 'retval' in response.json():
                    retval = response.json()['retval']
                    if retval:
                        self._article_cross_ref_json['crossReference'] = retval['references']
                    fHandler.appendToFileLog("\t_article_cross_ref_json -> НАЙДЕН!")
                else:
                    return None
            except PlaywrightTimeoutError:
                fHandler.appendToFileLog("PlaywrightTimeoutError!")
            except Error:
                pass

    def addAnalogToJSON(self, analog_article_name, analog_producer_name, json):
        if analog_article_name != "" and analog_producer_name != "":
            return JSONHandler.appendAnalogToJSON(json, analog_article_name, analog_producer_name)
        elif analog_article_name != "":
            return JSONHandler.appendOldAnalogToJSON(json, analog_article_name, self._catalogue_name)
        return json

    def goBack(self, driver):
        executing_return = driver.execute_script("window.history.back(); return 1;")
        wait_until(int(executing_return), 2)
        return driver
