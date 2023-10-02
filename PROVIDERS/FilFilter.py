import json
import logging
import time
import traceback

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error
from selenium.common import WebDriverException, JavascriptException
from selenium.webdriver.common.by import By

from PROVIDERS import Provider
from HANDLERS import FILEHandler as fHandler, JSONHandler as parseJSON, JSONHandler
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
    _article_url = "https://catalog.filfilter.com.tr/ru/product/"
    _catalogue_name = "FILFILTER"
    _max_page = 1
    _dbHandler = None

    def __init__(self, producer_id, dbHandler):
        self._producer_id = producer_id
        self._dbHandler = dbHandler
        self._producer_name = dbHandler.getProducerById(self._producer_id)

    def getMainUrl(self):
        return self._main_url

    def getCatalogueName(self):
        return self._catalogue_name

    # def getArticleFromURL(self, url):
    #     url_attr = url.split("/")
    #     if len(url_attr) < 4:
    #         return False
    #     return [url_attr[5], url]

    def getProducerId(self, article):
        return self._dbHandler.insertProducer(article[3])

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

        # executing_return = driver.execute_script("let pageButton = document.getElementById(\"select_6\");"
        #                                          "if (pageButton) {"
        #                                          "pageButton.click();"
        #                                          "let select_arrayCountByPage = document.getElementById(pageButton.getAttribute(\"aria-owns\"));"
        #                                          "let aa = select_arrayCountByPage.firstChild.firstChild;"
        #                                          "let button_countByPage = aa.children[aa.children.length-1];"
        #                                          "document.getElementById(button_countByPage.getAttribute(\"id\")).click();"
        #                                          "document.getElementById(\"select_3\").click();"
        #                                          "return 1;"
        #                                          "} else return 0;")
        # wait_until(int(executing_return))

        # try:
        #     buttonPages = driver.find_elements(By.ID, "select_3")
        #     if buttonPages:
        #         selectElement = driver.find_elements(By.ID, buttonPages[0].get_attribute("aria-owns"))
        #         lastchildren = selectElement[0].find_elements(By.CSS_SELECTOR, "*")[
        #             0].find_elements(By.CSS_SELECTOR, "*")[0].find_elements(By.TAG_NAME, "md-option")
        #         count = len(lastchildren)
        #         self._max_page = int(lastchildren[count - 1].get_attribute("value"))
        #         return self._max_page
        # except JavascriptException or IndexError:
        #     return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
        # return -1

    def endCondision(self, page):
        if page < self._max_page:
            return True
        return False

    # Поиск
    def search(self, driver, page_number, search_request):
        driver.get(self._catalog_url + search_request)
        return driver



    # Парсинг одну страницу поиска
    def parseSearchResult(self, driver, pageNumber):
        # print("parseSearchResult")
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

    # Загрузка страницы товара
    def loadArticlePage(self, driver, article_url, search_type=False):

        try:
            driver.get(article_url)
        except WebDriverException:
            return False

        return driver

    def getArticleType(self, driver) -> str:
        return ""

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

    # def getAnalogs(self, article_url, article_id):
    #     pass

    def setInfo(self, article_name, producer_name, info_json):
        pass

    def saveJSON(self, driver, article_url, article_name, description, search_request, analog_article_name, analog_producer_name):

        fHandler.appendToFileLog("saveJSON():")

        with sync_playwright() as p:

            # Получаем Cross-Ref & Type
            index = 0
            limit_check = 4
            self._article_info_json = {}
            self._article_cross_ref_json = {}
            browser = p.chromium.launch()
            page = browser.new_page()
            while len(self._article_cross_ref_json) == 0 and index < limit_check:
                try:
                    page.set_default_timeout(5000)
                    page.on("response", self.handle_response)
                    page.goto(article_url, wait_until="networkidle")
                except PlaywrightTimeoutError:
                    fHandler.appendToFileLog("PlaywrightTimeoutError!")
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
                status = driver.find_elements(By.CLASS_NAME, "product-link")[0]\
                    .find_element(By.XPATH, '..')\
                    .find_element(By.XPATH, "preceding-sibling::*[1]")\
                    .find_elements(By.TAG_NAME, "b")[0]\
                    .get_attribute("innerHTML")
                status = status.split(" ")[0].upper()
                if status == "ЗАМЕНЕНО":
                    flag_replace = True
                    replace_article_names.append(driver.find_elements(By.CLASS_NAME, "product-link")[0].get_attribute(
                        "innerHTML"))
                    article_type = "real"
                elif status == "ЗАМЕНА":
                    flag_replaced = True
                    replaced_article_names.append(driver.find_elements(By.CLASS_NAME, "product-link")[0].get_attribute(
                        "innerHTML"))
                    article_type = "old"

            elif driver.find_elements(By.CLASS_NAME, "flex-40")[
                len(driver.find_elements(By.CLASS_NAME, "flex-40")) - 1] \
                    .get_attribute("innerHTML") == "не поставляется":
                article_type = "old"


            # Получаем характеристики
            self._article_info_json['articleMainInfo'] = {}
            if len(driver.find_elements(By.CLASS_NAME, "vehicle-details")) > 1:
                md_list_item_characteristics = driver.find_elements(By.CLASS_NAME, "vehicle-details")[1]
                md_list_item_characteristics = md_list_item_characteristics.find_elements(By.CLASS_NAME, "md-no-proxy")
                md_list_item_characteristics.pop(0)
                index = 0
                for md_item_characteristic in md_list_item_characteristics:
                    characteristic_name = md_item_characteristic.find_elements(By.CLASS_NAME, "flex-60")[0] \
                        .find_elements(By.TAG_NAME, "b")[0].get_attribute("innerHTML")
                    if index == 0:
                        characteristic_name = characteristic_name.split(":")[0].strip()
                    characteristic_value = md_item_characteristic.find_elements(By.CLASS_NAME, "flex-40")[0] \
                        .get_attribute("innerHTML")
                    if characteristic_name == "Товарная группа":
                        description = characteristic_value
                    self._article_info_json['articleMainInfo'][characteristic_name] = f"{characteristic_value}"
                    index += 1
            # Получаем изображение
            imageURLS = []
            if len(driver.find_elements(By.CLASS_NAME, "md-card-image")) > 0:
                imageURLS.append(driver.find_elements(By.CLASS_NAME, "md-card-image")[0].get_attribute("src"))

            # Проверяем, что нашли
            if len(self._article_cross_ref_json) == 0:
                fHandler.appendToFileLog("\t_article_cross_ref_json is empty()")
                self._article_cross_ref_json['crossReference'] = []
                # print("\tJSONs получены!")

            # Приводим Cross Ref JSON к нужному формату
            cross_ref_json = []
            previous_producer_name = ""
            new_json = {}
            id = 0
            self._article_cross_ref_json['crossReference'] = sorted(self._article_cross_ref_json['crossReference'],
                                                                    key=lambda elem: elem['manufacturer_name'])
            for elem in self._article_cross_ref_json['crossReference']:
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
                id += 1
            if new_json != {}:
                cross_ref_json.append(new_json)

            self._article_cross_ref_json['crossReference'] = cross_ref_json

            self._article_info_json['articleSecondaryInfo'] = {
                "articleId": article_url.split("/")[len(article_url.split("/")) - 1],
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

            # print("\tgenerateArticleJSON() -> completed")

            # fHandler.appendJSONToFile("DONALDSON", article_json, search_request)
            fHandler.appendToFileLog("\tappendToFile() -> completed")
            fHandler.appendToFileLog("saveJSON() -> completed")

            return article_json

    with sync_playwright() as p:
        def handle_response(self, response):
            if len(self._article_cross_ref_json) > 0:
                return None

            # print(response.url)
            if "get_product_oe_references" in response.url:
                # print("НАШЁЛ!")
                try:
                    # print(response.json())
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
