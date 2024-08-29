import time

import gevent
from loguru import logger
from selenium.common import WebDriverException
from selenium.webdriver.common.by import By
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Error
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from PROVIDERS import Provider
from HANDLERS import FILEHandler as fHandler, JSONHandler as parseJSON, JSONHandler, PLAYWRIGHTHandler
from UTILS import strings, parse

PLAYWRIGHT = PLAYWRIGHTHandler.PLAYWRIGHT


class Fleetguard(Provider.Provider):
    _main_url = "https://www.fleetguard.com/s/?language=en_US"
    _catalogue_url = "https://www.fleetguard.com/s/searchResults?propertyVal="
    _article_url = "https://www.fleetguard.com/s/productDetails?language=en_US&propertyVal="
    _catalogue_name = "FLEETGUARD"

    _articles = []

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

    def getSearchUrl(self, article_name):
        return f"{self._catalogue_url}{article_name}"


    def getPageCount(self, driver, search_request):

        driver.get(self.getSearchUrl(search_request))

        # Прогружаем всю страницу со всеми товарами
        # https://www.selenium.dev/documentation/webdriver/actions_api/wheel/
        # https://scrapfly.io/blog/how-to-scroll-to-the-bottom-with-selenium/
        prev_height = -1
        scroll_count = 0
        max_scrolls = 5
        while scroll_count < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            new_height = driver.execute_script("return document.body.scrollHeight")
            gevent.sleep(scroll_count*2)
            if new_height == prev_height:
                break
            prev_height = new_height
            scroll_count += 1

        #  Ищём товары
        # https://ru.stackoverflow.com/questions/1331382/selenium-%D0%BD%D0%B5-%D1%83%D0%B4%D0%B0%D0%B5%D1%82%D1%81%D1%8F-%D0%BD%D0%B0%D0%B9%D1%82%D0%B8-%D1%8D%D0%BB%D0%B5%D0%BC%D0%B5%D0%BD%D1%82-python
        # https://qna.habr.com/q/1248740
        # https://habr.com/ru/companies/simbirsoft/articles/598407/
        # https://qna.habr.com/q/706681
        # https://automated-testing.info/t/selenium-ne-nahodit-element-po-xpath-a-on-est-na-stranicze/28205/3
        # https://www.selenium.dev/selenium/docs/api/py/webdriver_support/selenium.webdriver.support.expected_conditions.html#selenium.webdriver.support.expected_conditions.presence_of_all_elements_located
        shadow_host = driver.find_elements(By.TAG_NAME, "c-product-listing-page")[0]
        shadow_root = shadow_host.shadow_root
        div_leftPadd = shadow_root.find_elements(By.CLASS_NAME, "Left-Padd")
        if len(div_leftPadd) < 1:
            return -1
        else:
            div_leftPadd = div_leftPadd[0]

        # Собираем всё, что нашли
        elements = WebDriverWait(div_leftPadd, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "container_Changed")))

        for element in elements:
            a = element.find_element(By.CLASS_NAME, "productCode1")
            article_name = a.text.strip()
            cross_ref = element.find_elements(By.CLASS_NAME, "crossRef-content")
            if len(cross_ref) > 0:
                cross_ref = cross_ref[0]
                analog_article = cross_ref.find_element(By.CLASS_NAME, "crossRefName").text.strip().split(" ")
                analog_article_producer_name = ""
                for i in range(0, len(analog_article) - 1):
                    analog_article_producer_name += analog_article[i]
                analog_article_producer_name = analog_article_producer_name.upper()
                analog_article_name = analog_article[len(analog_article)-1]
                self._articles.append([article_name, self.getProductUrl(article_name), analog_article_name, analog_article_producer_name])
            else:
                self._articles.append([article_name, self.getProductUrl(article_name)])

        return len(elements)

    def endCondition(self, page):
        if page < self.max_page:
            return True
        return False

    def search(self, driver, page_number, search_request):
        return True

    def parseSearchResult(self, driver, pageNumber=None):
        return self._articles

    def loadArticlePage(self, driver, article_url, search_type=False):
        try:
            driver.get(article_url)
        except WebDriverException:
            return False
        return driver

    def getArticleType(self, driver) -> str:
        shadow_root = driver.find_element(By.TAG_NAME, "c-product-detail-page").shadow_root
        type = shadow_root.find_element(By.CLASS_NAME, "productDetails").find_elements(By.TAG_NAME, "h2")[0].text
        return type

    def parseCrossReferenceResult(self, driver, pageNumber):
        pass

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

    def saveJSON(self, driver, article_url, article_name, description, search_request, analog_article_name, analog_producer_name):

        flag_replaced = False
        flag_replace = False
        replaced_article_names = []
        replace_article_names = []
        article_type = "real"

        shadow_root = driver.find_element(By.TAG_NAME, "c-product-detail-page").shadow_root
        obsolente = shadow_root.find_elements(By.CLASS_NAME, "ObsoleteClass")
        if len(obsolente) > 0:
            flag_replaced = True
            article_type = "old"
            els = shadow_root.find_elements(By.CLASS_NAME, "parts")
            replaced_by = None
            for el in els:
                if el.text == "Replaced By":
                    replaced_by = el
            if replaced_by is not None:
                next_sibling_js = driver.execute_script("return arguments[0].nextElementSibling;", replaced_by)
                replaced_by_articles = next_sibling_js.find_elements(By.CLASS_NAME, "relatedItem")
                for article in replaced_by_articles:
                    replaced_article_names.append(article.text)
        else:
            els = shadow_root.find_elements(By.CLASS_NAME, "parts")
            replaces = None
            for el in els:
                if el.text == "Replaces":
                    replaces = el
            if replaces is not None:
                flag_replace = True
                next_sibling_js = driver.execute_script("return arguments[0].nextElementSibling;", replaces)
                replaces_articles = next_sibling_js.find_elements(By.CLASS_NAME, "relatedItem")
                for article in replaces_articles:
                    replace_article_names.append(article.text)

        cross_reference = []
        buttons = shadow_root.find_elements(By.CLASS_NAME, "tablinks")
        for button in buttons:
            if button.text == "OEM Cross Reference":
                button.click()
                gevent.sleep(1)
                tab = shadow_root.find_element(By.CLASS_NAME, "tabcontent")
                rows_analogs = tab.find_elements(By.CLASS_NAME, "Related_Parts_Class")
                for row in rows_analogs:
                    analog_producer_name1 = row.find_element(By.CLASS_NAME, "parts").get_attribute("innerHTML").strip()
                    analog_article_names = []
                    div_article_names = row.find_element(By.CLASS_NAME, "three_Part_Grid")\
                        .find_elements(By.CLASS_NAME, "parts")
                    for div in div_article_names:
                        analog_article_names.append(div.get_attribute("data-item").replace(" ", ""))
                    analogs = {
                        "producerName": analog_producer_name1,
                        "articleNames": analog_article_names,
                        "type": "real"
                    }
                    cross_reference.append(analogs)

        _article_cross_ref_json = {}
        _article_cross_ref_json['crossReference'] = cross_reference

        # Получаем характеристики
        _article_info_json = {}
        _article_info_json['articleMainInfo'] = {}
        div_characteristics = shadow_root.find_elements(By.CLASS_NAME, "tableCls")
        if len(div_characteristics) > 0:
            tables = div_characteristics[0].find_elements(By.TAG_NAME, "table")
            for table in tables:
                trs = table.find_elements(By.TAG_NAME, "tr")
                for tr in trs:
                    tds = tr.find_elements(By.TAG_NAME, "td")
                    name = tds[0].text
                    value = tds[1].text
                    _article_info_json['articleMainInfo'][name] = f"{value}"

        # Получаем изображение
        imageURLS = []
        image = shadow_root.find_element(By.CLASS_NAME, "imgfluid")
        imageURLS.append(image.get_attribute("src"))

        _article_info_json['articleSecondaryInfo'] = {
            "articleId": article_name,
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
            article_json = JSONHandler.appendAnalogsToJSON(article_json, replaced_article_names, self._catalogue_name)
        if flag_replace:
            article_json = JSONHandler.appendOldAnalogsToJSON(article_json, replace_article_names, self._catalogue_name)

        return article_json

    def addAnalogToJSON(self, analog_article_name, analog_producer_name, json):
        if analog_article_name != "" and analog_producer_name != "":
            return JSONHandler.appendAnalogToJSON(json, analog_article_name, analog_producer_name)
        elif analog_article_name != "":
            return JSONHandler.appendOldAnalogToJSON(json, analog_article_name, self._catalogue_name)
        return json
