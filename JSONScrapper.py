#!/usr/bin/env python
# -*- coding: utf-8 -*-
# https://peps.python.org/pep-0263/
import Decorators
from HANDLERS import WEBHandler as wHandler
from HANDLERS import FILEHandler as fHandler
import init
from Error import Error, ErrorHandler

# https://techorde.com/scraping-browser-xhr-requests-using-python/
# https://scrapism.lav.io/scraping-xhr/
# https://www.zenrows.com/blog/selenium-python-web-scraping#add-real-headers
# https://www.zenrows.com/blog/web-scraping-without-getting-blocked#why-is-web-scraping-not-allowed
from PROVIDERS.Provider import ProviderHandler


def appendSearchRequestStartToFileLog(search_request):
    fHandler.appendToFileLog("~~~~~~~~")
    fHandler.appendToFileLog("SEARCH REQUEST: " + search_request + " -> START!")
    fHandler.appendToFileLog("\n")

def appendSearchRequestEndToFileLog(search_request):
    fHandler.appendToFileLog("SEARCH REQUEST: " + search_request + " -> END!")
    fHandler.appendToFileLog("~~~~~~~~")
    fHandler.appendToFileLog("\n")

if __name__=="__main__":

    init.init()
    errorHandler = ErrorHandler()

    search_requests = fHandler.getSearchRequests()
    if len(search_requests) < 1:
        errorHandler.printError(Error.NOTHING_TO_SEARCH)
        exit()

    # ?????????? ?? ???????? ? ???????????? ??
    for request in search_requests:

        provider_name = request[0]
        search_request = request[1]

        # ???????? ???????????? ?????????? ????? ????????????? ? ?? ??? ???????????????
        provider_code = ProviderHandler().getProviderCodeByName(provider_name)
        if provider_code is None or not ProviderHandler().isActive(provider_code):
            continue

        # appendSearchRequestStartToFileLog(search_request)

        # ??????????? ?????-????????
        webWorker = wHandler.WebWorker(provider_code, search_request)
        status_code = webWorker.pullCrossRefToDB()
        if status_code is not Error.SUCCESS:
            errorHandler.printError(status_code)

        # appendSearchRequestEndToFileLog(search_request)

    exit(0)
