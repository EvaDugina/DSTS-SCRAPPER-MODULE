import time
from json import JSONDecodeError

from bs4 import BeautifulSoup
from selenium.common import WebDriverException, JavascriptException
from selenium.webdriver.common.by import By
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Error, sync_playwright

import Decorators
from PROVIDERS import Provider
from HANDLERS import FILEHandler as fHandler, JSONHandler as parseJSON, JSONHandler
from UTILS import strings, parse

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

    _playwright_handler = None

    def __init__(self):
        super().__init__()

    def __del__(self):
        super().__del__()

    def __exit__(self):
        super().__exit__()

    def getMainUrl(self):
        return self._main_url

    def getProductUrl(self, article_name):
        return self._article_url + article_name

    def getMaxPage(self):
        return self.max_page

    def getName(self):
        return self._catalogue_name


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
            lastButton = lastButton[0]
            try:
                max_page = int(lastButton.find_element(By.TAG_NAME, "a").get_attribute("innerHTML"))
                self.max_page = max_page
                return max_page
            except JavascriptException or IndexError:
                return -1
        return 0

    def endCondition(self, page):
        if page < self.max_page:
            return True
        return False


    def parseSearchResult(self, driver, pageNumber=None):

        div_elements = driver.find_elements(By.CLASS_NAME, "listTile")
        articles = []
        for index, div in enumerate(div_elements, start=0):
            first_div_children = div.find_element(By.TAG_NAME, "div")
            a_elem = first_div_children.find_element(By.CLASS_NAME, "donaldson-part-details")
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
                    analog_producer_name = analog_by_search.find_element(By.TAG_NAME, "span") \
                        .find_element(By.TAG_NAME, "span").get_attribute("innerHTML")
                    analog_article_name = analog_by_search.find_elements(By.TAG_NAME, "span")[2] \
                        .find_element(By.TAG_NAME, "span").get_attribute("innerHTML")
                    flag_analog = True

            try:
                span = a_elem.find_element(By.TAG_NAME, "span")
                if changedDetailArticleName != "":
                    articles.append(
                        [span.get_attribute("innerHTML"), a_elem.get_attribute("href"), changedDetailArticleName])
                else:
                    if flag_analog:
                        articles.append(
                            [span.get_attribute("innerHTML"), a_elem.get_attribute("href"), analog_article_name,
                             analog_producer_name])
                    else:
                        articles.append([span.get_attribute("innerHTML"), a_elem.get_attribute("href")])
            except JavascriptException or IndexError:
                return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
        return articles


    def loadArticlePage(self, driver, article_url, search_type=False):
        try:
            driver.get(article_url)
        except WebDriverException:
            return False
        return True


    def getArticleType(self, driver) -> str:
        html = driver.page_source.encode('utf-8')
        parsed_html = BeautifulSoup(html, "html.parser")
        body = parsed_html.body
        while body is None or body == "":
            time.sleep(0.5)
        found = body.find('div', attrs={'class': 'prodSubTitleMob'})
        return found.text

    def parseCrossReferenceResult(self, driver, pageNumber):
        pass


    def saveJSON(self, driver, article_url, article_name, type, search_request, analog_article_name,
                 analog_producer_name, playwright_browser=None):

        # Получаем Cross-Ref & Characteristics & Type
        data = {"cross_ref": {}, "info_json": {}}

        def handle_cross_ref(response_json):
            if 'crossReferenceList' in response_json:
                data['cross_ref'] = response_json['crossReferenceList']
                print(data['cross_ref'])

        def handle_info(response_json):
            article_info_characteristic = dict()
            article_info_else = dict()
            if 'productAttributesResponse' in response_json:
                article_info_characteristic['productMainInfo'] = \
                    response_json['productAttributesResponse']['dynamicAttributes']
            if 'recentlyViewedProductResponse' in response_json:
                article_info_else['productSecondaryInfo'] = \
                    response_json['recentlyViewedProductResponse']['recentlyViewedProducts'][0]
            data["info_json"] = article_info_characteristic | article_info_else
            print(data['info_json'])

        playwright_browser.newPage()
        try:
            playwright_browser.handleResponse(article_url, handle_cross_ref, "fetchproductcrossreflist?")
            playwright_browser.handleResponse(article_url, handle_info, "fetchProductAttrAndRecentlyViewed?")
        except PlaywrightTimeoutError:
            pass
        except Exception as e:
            print(f"Exception {str(e)}")

        _article_cross_ref_json = {'crossReference': data['cross_ref']}
        _article_info_json = data['info_json']

        # Проверяем, что нашли
        if len(_article_info_json) == 0:
            # print("\t_article_info_json is empty()")
            _article_info_json['articleMainInfo'] = {}
            _article_info_json['articleSecondaryInfo'] = {}
        if len(_article_cross_ref_json) == 0:
            _article_cross_ref_json['crossReference'] = []
        # print("\tJSONs получены!")

        # Приводим JSONS к нужному формату
        cross_ref_json = []
        for elem in _article_cross_ref_json['crossReference']:
            new_json = {
                "producerName": elem['manufactureName'],
                "articleNames": elem['manufacturePartNumber'],
                "type": "real"
            }
            cross_ref_json.append(new_json)
        _article_cross_ref_json['crossReference'] = cross_ref_json

        if 'productMainInfo' in _article_info_json:
            _article_info_json['articleMainInfo'] = _article_info_json['productMainInfo']
            _article_info_json.pop('productMainInfo')
        else:
            _article_info_json['articleMainInfo'] = []

        if 'productSecondaryInfo' in _article_info_json:
            _article_info_json['articleSecondaryInfo'] = {
                "articleId": _article_info_json['productSecondaryInfo']['productId'],
                "imageUrls": [_article_info_json['productSecondaryInfo']['imageUrl']]
            }
            _article_info_json.pop('productSecondaryInfo')
        else:
            _article_info_json['articleSecondaryInfo'] = {
                "articleId": -1,
                "imageUrls": []
            }

        type_json = dict([("articleDescription", type)])

        # Склеиваем информацию в один JSON
        article_info_json = {**_article_cross_ref_json, **_article_info_json}
        article_info_json = {**article_info_json, **type_json}

        # Отправляем на генерацию полного JSON
        article_json = parseJSON.generateArticleJSON(article_name, self._catalogue_name, self._catalogue_name,
                                                     article_info_json)
        article_json = self.addAnalogToJSON(analog_article_name, analog_producer_name, article_json)

        return article_json


    def addAnalogToJSON(self, analog_article_name, analog_producer_name, json):
        if analog_article_name != "" and analog_producer_name != "":
            return JSONHandler.appendAnalogToJSON(json, analog_article_name, analog_producer_name)
        elif analog_article_name != "":
            return JSONHandler.appendOldAnalogToJSON(json, analog_article_name, self._catalogue_name)
        return json

