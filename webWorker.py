from selenium import webdriver
import DBHandler as db
import requests
import strings

import Donaldson as dl
# import Fleetguard as fl
import FilFilter as ff


def webWork(search_request, producer_name):
    producer_id = db.insertProducer(producer_name)
    provider = None
    if producer_name == "DONALDSON":
        provider = dl.Donaldson(producer_id)
    # elif producer_name == "FLEETGUARD":
    #     provider = fl.Fleetguard(producer_id)
    elif producer_name == "FIL-FILTER":
        provider = ff.FilFilter(producer_id)
    else:
        return strings.UNDEFIND_PRODUCER + ": " + str(producer_name)

    try:
        requests.head(provider.getMainUrl(), timeout=1)
    except requests.ConnectionError:
        return strings.INTERNET_ERROR

    driver = webdriver.Edge()

    count_successed_articles = 0
    count_unsuccessed_articles = 0

    page = 0
    while provider.endCondision(page):

        driver = provider.search(driver, page, search_request)

        articles = provider.parseSearchResult(driver)

        # for article in articles:
        #     article_id = db.insertArticle(article[0], producer_id)
        #     driver = provider.loadArticlePage(driver, article)
        #     provider.parseCrossReference(driver, article_id)
        #     count_successed_articles += 1
        article_id = db.insertArticle(articles[0][0], producer_id)
        driver = provider.loadArticlePage(driver, articles[0])
        flag = doWhileNoSuccess(0, "parseCrossRef", provider.parseCrossReference, driver, article_id)

        if flag:
            count_successed_articles += 1
        else:
            count_unsuccessed_articles += 1

        page += 1

    if count_successed_articles > 0 and count_unsuccessed_articles == 0:
        return "SUCCESS"
    elif count_successed_articles != 0 and count_unsuccessed_articles > 0:
        return "НЕКОТОРЫЕ ЭЛЕМЕНТЫ НЕ БЫЛИ ОБРАБОТАНЫ!"
    else:
        return "Ни один элемент не был обработан"


def doWhileNoSuccess(try_count, type_function, function, driver, article):
    if try_count > 4:
        return False
    else:
        flag = False
        if type_function == "parseCrossRef":
            if try_count > 0:
                flag = function(driver, article, try_count*2)
            else:
                flag = function(driver, article, 1)

        elif type_function == "loadArticlePage":
            flag = function(driver, article)

        if flag:
            return True
        else:
            return doWhileNoSuccess(try_count + 1, type_function, function, driver, article)