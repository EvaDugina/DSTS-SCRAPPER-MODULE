import gevent
from gevent import monkey
monkey.patch_all()

import json
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Error
from selenium.common import WebDriverException
from selenium.webdriver.common.by import By

from PROVIDERS import Provider
from HANDLERS import FILEHandler as fHandler, JSONHandler as parseJSON, JSONHandler, PLAYWRIGHTHandler

PLAYWRIGHT = PLAYWRIGHTHandler.PLAYWRIGHT

def wait_until(return_value, period=0.5):
    gevent.sleep(period)
    while return_value != 1:
        gevent.sleep(period)
    return False


class FilFilter(Provider.Provider):
    _main_url = "https://catalog.filfilter.com.tr/ru"
    _catalog_url = "https://catalog.filfilter.com.tr/ru/search/"
    _article_url = "https://catalog.filfilter.com.tr/ru/product/"
    _catalogue_name = "FILFILTER"
    _max_page = 1

    _playwright = None

    def __init__(self):
        super().__init__()
        self._playwright = PLAYWRIGHT

    def getMainUrl(self):
        return self._main_url

    def getProductUrl(self, article_name):
        return self._article_url + article_name

    def getName(self):
        return self._catalogue_name

    def getPageCount(self, driver, search_request):

        driver.get(self._catalog_url + search_request)

        tbody_search_result = driver.find_elements(By.CLASS_NAME, "md-body")
        if len(tbody_search_result) > 0:
            ng_init_search_result = tbody_search_result[0].get_attribute("ng-init")
            if ng_init_search_result is not None:
                search_result_json = json.loads(ng_init_search_result.split(" = ")[1])
                return len(search_result_json) // 15
            else:
                return -1
        else:
            return -1

    def endCondition(self, page):
        if page < self._max_page:
            return True
        return False

    # Поиск
    def search(self, driver, page_number, search_request):

        driver.get(self._catalog_url + search_request)
        return driver

    # Парсинг одну страницу поиска
    def parseSearchResult(self, driver, pageNumber):

        tbody_search_result = driver.find_elements(By.CLASS_NAME, "md-body")[0]
        ng_init_search_result = tbody_search_result.get_attribute("ng-init")
        search_result_json = json.loads(ng_init_search_result.split(" = ")[1])

        articles = []
        for index, elem in enumerate(search_result_json):
            if index % self._max_page == pageNumber:
                link = f"{self._article_url}{elem['product']['SearchArtNo']}/{elem['product']['ArtId']}"
                if elem['manufacturer'] != "FIL FILTER":
                    articles.append([elem['product']['SearchArtNo'], link, elem['RefNo'], elem['manufacturer']])
                else:
                    articles.append([elem['product']['SearchArtNo'], link])

        return articles

    def parseCrossReferenceResult(self, driver, pageNumber):
        pass

    # Загрузка страницы товара
    def loadArticlePage(self, driver, article_url, search_type=False):

        try:
            driver.get(article_url)
        except WebDriverException:
            return False

        return driver

    def getArticleType(self, driver) -> str:

        return ""

    def saveJSON(self, driver, article_url, article_name, description, search_request, analog_article_name,
                 analog_producer_name):

        # Получаем Cross-Ref & Type
        index = 0
        limit_check = 4
        _article_info_json = {}
        _article_cross_ref_json = {}

        def handle_response(response):
            if len(_article_cross_ref_json) > 0:
                return None

            if "get_product_oe_references" in response.url:
                try:
                    if 'retval' in response.json():
                        retval = response.json()['retval']
                        if retval:
                            _article_cross_ref_json['crossReference'] = retval['references']
                    else:
                        return None
                except PlaywrightTimeoutError:
                    pass
                except Error:
                    pass

        browser = self._playwright.chromium.launch()
        page = browser.new_page()
        while len(_article_cross_ref_json) == 0 and index < limit_check:
            try:
                # page.set_default_timeout(5000)
                page.on("response", handle_response)
                page.goto(article_url, wait_until="networkidle")
            except PlaywrightTimeoutError:
                pass
            if index == limit_check - 2:
                page.wait_for_timeout(2000)
            index += 1
        page.context.close()
        browser.close()

        flag_replaced = False
        flag_replace = False
        replaced_article_names = []
        replace_article_names = []
        article_type = "real"
        if len(driver.find_elements(By.CLASS_NAME, "product-link")) > 0:
            status = driver.find_element(By.CLASS_NAME, "product-link") \
                .find_element(By.XPATH, '..') \
                .find_element(By.XPATH, "preceding-sibling::*[1]") \
                .find_element(By.TAG_NAME, "b") \
                .get_attribute("innerHTML")
            status = status.split(" ")[0].upper()
            if status == "ЗАМЕНЕНО":
                flag_replace = True
                replace_article_names.append(driver.find_element(By.CLASS_NAME, "product-link").get_attribute(
                    "innerHTML"))
                article_type = "real"
            elif status == "ЗАМЕНА":
                flag_replaced = True
                replaced_article_names.append(driver.find_element(By.CLASS_NAME, "product-link").get_attribute(
                    "innerHTML"))
                article_type = "old"

        elif driver.find_elements(By.CLASS_NAME, "flex-40")[
            len(driver.find_elements(By.CLASS_NAME, "flex-40")) - 1] \
                .get_attribute("innerHTML") == "не поставляется":
            article_type = "old"

        # Получаем характеристики
        _article_info_json['articleMainInfo'] = {}
        if len(driver.find_elements(By.CLASS_NAME, "vehicle-details")) > 1:
            md_list_item_characteristics = driver.find_elements(By.CLASS_NAME, "vehicle-details")[1]
            md_list_item_characteristics = md_list_item_characteristics.find_elements(By.CLASS_NAME, "md-no-proxy")
            md_list_item_characteristics.pop(0)
            index = 0
            for md_item_characteristic in md_list_item_characteristics:
                characteristic_name = md_item_characteristic.find_element(By.CLASS_NAME, "flex-60") \
                    .find_element(By.TAG_NAME, "b").get_attribute("innerHTML")
                if index == 0:
                    characteristic_name = characteristic_name.split(":")[0].strip()
                characteristic_value = md_item_characteristic.find_element(By.CLASS_NAME, "flex-40") \
                    .get_attribute("innerHTML")
                if characteristic_name == "Товарная группа":
                    description = characteristic_value
                _article_info_json['articleMainInfo'][characteristic_name] = f"{characteristic_value}"
                index += 1
        # Получаем изображение
        imageURLS = []
        if len(driver.find_elements(By.CLASS_NAME, "md-card-image")) > 0:
            imageURLS.append(driver.find_element(By.CLASS_NAME, "md-card-image").get_attribute("src"))

        # Проверяем, что нашли
        if len(_article_cross_ref_json) == 0:
            _article_cross_ref_json['crossReference'] = []
        else:
            _article_cross_ref_json['crossReference'] = sorted(_article_cross_ref_json['crossReference'],
                                                               key=lambda elem: elem['manufacturer_name'])

        # Приводим Cross Ref JSON к нужному формату
        cross_ref_json = []
        previous_producer_name = ""
        new_json = {}
        id = 0
        for elem in _article_cross_ref_json['crossReference']:
            try:
                if elem['manufacturer_name'] != previous_producer_name:
                    if id != 0:
                        cross_ref_json.append(new_json)

                    new_json = {
                        "producerName": elem['manufacturer_name'],
                        "articleNames": [
                            elem['RefNo']
                        ],
                        "type": "real"
                    }
                    previous_producer_name = elem['manufacturer_name']
                else:
                    new_json['articleNames'].append(elem['RefNo'])
            except KeyError:
                # print("ELEM:", elem)
                pass
            id += 1
        if new_json != {}:
            cross_ref_json.append(new_json)

        _article_cross_ref_json['crossReference'] = cross_ref_json

        _article_info_json['articleSecondaryInfo'] = {
            "articleId": article_url.split("/")[len(article_url.split("/")) - 1],
            "imageUrls": imageURLS
        }

        type_json = dict([("articleDescription", description)])

        # Склеиваем информацию в один JSON
        article_info_json = {**_article_cross_ref_json, **_article_info_json}
        article_info_json = {**article_info_json, **type_json}

        # Отправляем на генерацию полного JSON
        article_json = parseJSON.generateArticleJSON(article_name, self._catalogue_name, self._catalogue_name,
                                                     article_info_json, article_type)
        article_json = self.addAnalogToJSON(analog_article_name, analog_producer_name, article_json)

        if flag_replaced:
            article_json = JSONHandler.appendAnalogsToJSON(article_json, replaced_article_names,
                                                           self._catalogue_name)
        if flag_replace:
            article_json = JSONHandler.appendOldAnalogsToJSON(article_json, replace_article_names,
                                                              self._catalogue_name)


        return article_json


    def addAnalogToJSON(self, analog_article_name, analog_producer_name, json):
        if analog_article_name != "" and analog_producer_name != "":
            return JSONHandler.appendAnalogToJSON(json, analog_article_name, analog_producer_name)
        elif analog_article_name != "":
            return JSONHandler.appendOldAnalogToJSON(json, analog_article_name, self._catalogue_name)
        return json
