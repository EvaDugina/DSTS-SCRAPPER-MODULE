from selenium.webdriver.common.by import By
import DBHandler as db
import Provider as provider
import time


def wait_until(return_value, period=0.5):
    time.sleep(period)
    while return_value != 1:
        time.sleep(period)
    return False


class FilFilter(provider.Provider):

    _main_url = "https://catalog.filfilter.com.tr/ru"
    _catalog_url = "https://catalog.filfilter.com.tr/ru/search/"
    _max_page = 1

    def __init__(self, producer_id):
        self._producer_id = producer_id
        self._producer_name = db.getProducerById(self._producer_id)

    def getMainUrl(self):
        return self._main_url

    def search(self, driver, page_number, search_request):
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
        else:
            driver.get(self._catalog_url + search_request)

            # try:
            # Отображаем максимальное количество элементов на странице
            executing_return = driver.execute_script("let pageButton = document.getElementById(\"select_6\");"
                                                     "pageButton.click();"
                                                     "let select_arrayCountByPage = document.getElementById(pageButton.getAttribute(\"aria-owns\"));"
                                                     "let aa = select_arrayCountByPage.firstChild.firstChild;"
                                                     "let button_countByPage = aa.children[aa.children.length-1];"
                                                     "document.getElementById(button_countByPage.getAttribute(\"id\")).click();"
                                                     "document.getElementById(\"select_3\").click();"
                                                     "return 1;")

            wait_until(int(executing_return))

            # except:
            #     print("Ошибка 'driver.execute_script'")

            # Получаем максимальное количество страниц в поиске
            buttonPages = driver.find_elements(By.ID, "select_3")
            if buttonPages:
                selectElement = driver.find_elements(By.ID, buttonPages[0].get_attribute("aria-owns"))
                lastchildren = selectElement[0].find_elements(By.CSS_SELECTOR, "*")[
                    0].find_elements(By.CSS_SELECTOR, "*")[0].find_elements(By.TAG_NAME, "md-option")
                count = len(lastchildren)
                self._max_page = int(lastchildren[count - 1].get_attribute("value"))

        return driver

    def endCondision(self, page):
        if page < self._max_page:
            return True
        return False

    def parseSearchResult(self, driver):
        # print("parseSearchResult")
        trs = driver.find_elements(By.TAG_NAME, "tr")
        trs.pop(0)
        articles = []
        for index, elem in enumerate(trs, start=0):
            tds = elem.find_elements(By.TAG_NAME, "td")
            articles.append([tds[0].get_attribute("innerHTML"), tds[2].get_attribute("innerHTML"), index])
        return articles

    def loadArticlePage(self, driver, article):
        executing_return = \
            driver.execute_script("let trs = document.getElementsByTagName(\"tr\");"
                                  f"let tr = trs[{str(article[2]+1)}];"
                                  f"tr.children[tr.children.length-1].children[0].classList.add(\"button-link-{str(article[2])}\");"
                                  "document.getElementsByClassName(\"button-link-"+str(article[2])+"\")[0].click();"
                                  "return 1;")
        wait_until(int(executing_return), 1)
        return driver

    def parseCrossReference(self, driver, article_id, timeout=1):
        # print("parseCrossReference")
        executing_return = \
            driver.execute_script("let buttons = document.getElementsByClassName(\"md-center-tabs\")[1];"
                                  f"buttons.children[1].classList.add(\"IAmFromRussia\");"
                                  "document.getElementsByClassName(\"IAmFromRussia\")[0].click();"
                                  f"return 1;")
        wait_until(int(executing_return), timeout*2)


        text_maxPages = driver.find_elements(By.CLASS_NAME, "buttons")[0].find_elements(By.TAG_NAME, "div")[0].get_attribute("innerHTML")
        max_page = int(text_maxPages.split(" ")[2])

        count_cross_reference_elements = int(text_maxPages.split(" ")[4])
        print("НАЙДЕНО ЭЛЕМЕНТОВ КРОСС-РЕФЕРЕНСА:" + str(count_cross_reference_elements))

        count_pages = 1
        count_analogs = 0

        while count_pages <= max_page:

            div = driver.find_elements(By.CLASS_NAME, "md-body")[0]
            elements = div.find_elements(By.TAG_NAME, "tr")

            analog_producer_name = ""
            analog_producer_id = -1
            analogs = []

            for index, elem in enumerate(elements, start=0):

                now_analog_producer_name = elem.find_elements(By.TAG_NAME, "td")[0].get_attribute("innerHTML")
                now_analog_article_name = elem.find_elements(By.TAG_NAME, "td")[1].get_attribute("innerHTML")
                if now_analog_producer_name != analog_producer_name:
                    analog_producer_id = db.insertProducer(now_analog_producer_name)
                    if len(analogs) > 0:
                        db.insertArticleAnalogs(article_id, analogs)
                        count_analogs += len(analogs)
                        analogs = []
                    analog_producer_name = now_analog_producer_name
                else:
                    analog_article_id = db.insertArticle(now_analog_article_name, analog_producer_id)
                    analogs.append(analog_article_id)

            executing_return = \
                driver.execute_script("let buttons = document.getElementsByClassName(\"buttons\")[0];"
                                      f"buttons.children[2].classList.add(\"IAmFromRussia2\");"
                                      "document.getElementsByClassName(\"IAmFromRussia2\")[0].click();"
                                      f"return 1;")
            wait_until(int(executing_return), timeout)

            count_pages += 1

        if count_analogs > 0 and count_cross_reference_elements > 0:
            return True

        return False
