from selenium.webdriver.common.by import By
import DBHandler as db
import Provider


class Fleetguard(Provider):

    _catalog_url = "https://shop.donaldson.com/store/ru-ru/search?Ntt="
    _max_page = 1

    def __init__(self, producer_id):
        self._producer_id = producer_id
        self._producer_name = db.getProducerById(self._producer_id)

    def search(self, driver, page_number, search_request):
        # if page_number > 0:
        #     driver.get(self._catalog_url + search_request + f"No={20*page_number}&")
        # else:
        #     driver.get(self._catalog_url + search_request)
        #     lastButton = driver.find_elements(By.CLASS_NAME, "lastButton")
        #     if len(lastButton) > 0:
        #         self._max_page = int(lastButton[0].find_elements(By.TAG_NAME, "a")[0]
        #                              .get_attribute("innerHTML"))
        return driver

    def endCondision(self, page):
        # if page < self._max_page:
            return True
        return False


    def parseSearchResult(self, driver):
        # elements = driver.find_elements(By.CLASS_NAME, "donaldson-part-details")
        # articles = []
        # for index, elem in enumerate(elements, start=0):
        #     if index % 2 == 0:
        #         spans = elem.find_elements(By.TAG_NAME, "span")
        #         articles.append([spans[0].get_attribute("innerHTML"), elem.get_attribute("href")])
        return articles

    def parseCrossReference(self, driver, article_id):
        # driver.execute_script("document.getElementById(\"showAllCrossReferenceListButton\").click();" +
        #                       "let blocks = document.getElementsByClassName(\"searchCrossRef\");" +
        #                       "for(let i = 0; i < blocks.length; i++){" +
        #                       "blocks[i].style.display = \"unset\";" +
        #                       "blocks[i].parentElement.className = \"\";" +
        #                       "let tag_i = blocks[i].getElementsByTagName(\"i\");" +
        #                       "if(tag_i.length > 0)" +
        #                       "tag_i[0].click();" +
        #                       "}")
        #
        # elements = driver.find_elements(By.CLASS_NAME, "searchCrossRef")
        # analog_producer_name = ""
        # analog_producer_id = -1
        # analogs = []
        # for index, elem in enumerate(elements, start=0):
        #     if index % 3 == 0:
        #         if elem.text != analog_producer_name:
        #             analog_producer_id = db.insertProducer(analog_producer_name)
        #             if len(analogs) > 0:
        #                 db.insertArticleAnalogs(article_id, analogs)
        #                 analogs = []
        #             analog_producer_name = elem.text
        #     elif index % 3 == 1:
        #         analog_article_name = elem.text
        #         analog_article_id = db.insertArticle(analog_article_name, analog_producer_id)
        #         analogs.append(analog_article_id)
