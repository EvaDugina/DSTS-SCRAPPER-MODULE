import json
import logging
import time
import traceback

from playwright.sync_api import sync_playwright
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

        # Старая версия с прокликиваниями
        # trs = driver.find_elements(By.TAG_NAME, "tr")
        # trs.pop(0)
        # articles = []
        # for index, elem in enumerate(trs, start=0):
        #     try:
        #         tds = elem.find_elements(By.TAG_NAME, "td")
        #         articles.append([tds[0].get_attribute("innerHTML"), tds[2].get_attribute("innerHTML"),
        #                          index, tds[1].get_attribute("innerHTML")])
        #     except JavascriptException or IndexError:
        #         return strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE
        return articles

    # Загрузка страницы товара
    def loadArticlePage(self, driver, article_url, search_type=False):
        # Старое с прокликиванием
        # if search_type:
        #     try:
        #         driver.get(article[1])
        #     except WebDriverException:
        #         return False
        #     return driver
        #
        # executing_return = \
        #     driver.execute_script("let trs = document.getElementsByTagName(\"tr\");"
        #                           f"let tr = trs[{str(article[2]+1)}];"
        #                           f"tr.children[tr.children.length-1].children[0].classList.add(\"button-link-{str(article[2])}\");"
        #                           "document.getElementsByClassName(\"button-link-"+str(article[2])+"\")[0].click();"
        #                           "return 1;")
        # wait_until(int(executing_return), 2)

        try:
            driver.get(article_url)
        except WebDriverException:
            return False

        return driver

    def getArticleType(self, driver) -> str:
        return ""

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

        # main_producer_id = self._dbHandler.insertProducer(producer_name, self._catalogue_name)
        # fHandler.appendToFileLog("----> PRODUCER_ID: " + str(main_producer_id))
        # main_article_id = self._dbHandler.insertArticle(main_article_name, main_producer_id, self._catalogue_name)
        # for elem in cross_ref:
        #     producer_name = elem['producerName']
        #     fHandler.appendToFileLog("\t--> PRODUCER_NAME: " + str(producer_name))
        #     producer_id = self._dbHandler.insertProducer(producer_name, self._catalogue_name)
        #     analog_article_names = elem['articleNames']
        #     analog_article_ids = []
        #     for article_name in analog_article_names:
        #         analog_article_id = self._dbHandler.insertArticle(article_name, producer_id, self._catalogue_name)
        #         analog_article_ids.append(analog_article_id)
        #     self._dbHandler.insertArticleAnalogs(main_article_id, analog_article_ids, self._catalogue_name)

    def getAnalogs(self, article_url, article_id):
        pass

    def setInfo(self, article_name, producer_name, info_json):
        pass

    def saveJSON(self, driver, article_url, article_name, type, search_request, article):

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
                page.on("response", self.handle_response)
                page.goto(article_url, wait_until="load")
                if index == limit_check - 2:
                    page.wait_for_timeout(2000)
                index += 1
            page.context.close()
            browser.close()

            flag_changed = False
            type = "real"
            if len(self._article_cross_ref_json) == 0:
                if len(driver.find_elements(By.CLASS_NAME, "product-link")) > 0:
                    changed_article_name = driver.find_elements(By.CLASS_NAME, "product-link")[0].get_attribute(
                        "innerHTML")
                    flag_changed = True
                    type = "old"
                elif driver.find_elements(By.CLASS_NAME, "flex-40")[
                    len(driver.find_elements(By.CLASS_NAME, "flex-40")) - 1] \
                        .get_attribute("innerHTML") == "не поставляется":
                    type = "old"

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
                        characteristic_name = characteristic_name.split(":")[0]
                    characteristic_value = md_item_characteristic.find_elements(By.CLASS_NAME, "flex-40")[0] \
                        .get_attribute("innerHTML")
                    self._article_info_json['articleMainInfo'][characteristic_name] = f"{characteristic_value}"
                    index += 1

            # Получаем изображение
            imageURL = ""
            if len(driver.find_elements(By.CLASS_NAME, "md-card-image")) > 0:
                imageURL = driver.find_elements(By.CLASS_NAME, "md-card-image")[0].get_attribute("src")

            # Проверяем, что нашли
            if len(self._article_cross_ref_json) == 0:
                logging.info("\t_article_cross_ref_json is empty()")
                self._article_cross_ref_json['crossReference'] = []
                # print("\tJSONs получены!")

            # Приводим Cross Ref JSON к нужному формату
            cross_ref_json = []
            for elem in self._article_cross_ref_json['crossReference']:
                new_json = {
                    "producerName": elem['manufacturer_name'],
                    "articleNames": [
                        elem['RefNo']
                    ],
                    "type": "real"
                }
                cross_ref_json.append(new_json)
            self._article_cross_ref_json['crossReference'] = cross_ref_json
            self._article_cross_ref_json['crossReference'] = sorted(self._article_cross_ref_json['crossReference'],
                                                                    key=lambda elem: elem['producerName'])

            self._article_info_json['articleSecondaryInfo'] = {
                "articleId": article_url.split("/")[len(article_url.split("/")) - 1],
                "imageUrl": imageURL,
                "fullId": ""
            }

            type_json = dict([("articleDescription", type)])

            # Склеиваем информацию в один JSON
            article_info_json = {**self._article_cross_ref_json, **self._article_info_json}
            article_info_json = {**article_info_json, **type_json}

            # Отправляем на генерацию полного JSON
            article_json = parseJSON.generateArticleJSON(article_name, self._catalogue_name, self._catalogue_name,
                                                            article_info_json, type)
            article_json = self.addAnalogToJSON(article, article_json)

            if flag_changed:
                article_json = JSONHandler.appendAnalogToJSON(article_json, changed_article_name, self._catalogue_name)

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
                except:
                    logging.warning(traceback.format_exc())

    def addAnalogToJSON(self, article, json):
        if len(article) == 4:
            return JSONHandler.appendAnalogToJSON(json, article[2], article[3])
        # elif len(article) == 3:
        #     return JSONHandler.appendOldAnalogToJSON(json, article[2], self._catalogue_name)
        return json

    def goBack(self, driver):
        executing_return = driver.execute_script("window.history.back(); return 1;")
        wait_until(int(executing_return), 2)
        return driver
