#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://peps.python.org/pep-0263/
from loguru import logger

import Decorators
import JSONParser
from HANDLERS import WEBHandler as wHandler
from HANDLERS import FILEHandler as fHandler
import init
from HANDLERS.ERRORHandler import Error

# https://techorde.com/scraping-browser-xhr-requests-using-python/
# https://scrapism.lav.io/scraping-xhr/
# https://www.zenrows.com/blog/selenium-python-web-scraping#add-real-headers
# https://www.zenrows.com/blog/web-scraping-without-getting-blocked#why-is-web-scraping-not-allowed
from PROVIDERS.Provider import ProviderHandler


@Decorators.error_decorator
def main():
    init.init()

    logger.debug("JSONScrapper.py")

    search_requests = fHandler.getSearchRequests()
    if len(search_requests) < 1:
        return Error.NOTHING_TO_SEARCH

    fHandler.cleanFileOutput()

    for request in search_requests:
        searchRequest(request[0], request[1])

    exit(0)

@Decorators.time_decorator
def searchRequests(search_requests):
    init.init()

    logger.debug(f"searchRequests({search_requests})")
    logger.debug(search_requests)

    fHandler.cleanFileOutput()

    for request in search_requests:
        searchRequest(request[0], request[1])

    elements = fHandler.getElementsForParse()
    JSONParser.parseElements(elements)

    exit(0)


def searchRequest(provider_name, search_request):

    provider_code = ProviderHandler().getProviderCodeByName(provider_name)
    if provider_code is None or not ProviderHandler().isActive(provider_code):
        return

    logger.debug(">>>> SEARCH REQUEST: " + search_request)

    webWorker = wHandler.WebWorker(provider_code, search_request)
    webWorker.pullCrossRefToDB()

    fHandler.moveLINKToCompleted(provider_name, search_request)

    logger.debug("<<<< SEARCH REQUEST: " + search_request)

    return

def getSearchResults():
    return fHandler.getOutputText()


if __name__ == "__main__":
    main()
