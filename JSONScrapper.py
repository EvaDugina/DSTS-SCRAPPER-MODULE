#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Decorators
import JSONParser
from HANDLERS import WEBHandler as wHandler
from HANDLERS import FILEHandler as fHandler, LOGHandler, STATEHandler
import init
from HANDLERS.ERRORHandler import Error

# https://techorde.com/scraping-browser-xhr-requests-using-python/
# https://scrapism.lav.io/scraping-xhr/
# https://www.zenrows.com/blog/selenium-python-web-scraping#add-real-headers
# https://www.zenrows.com/blog/web-scraping-without-getting-blocked#why-is-web-scraping-not-allowed
from PROVIDERS import Provider
from PROVIDERS.Provider import ProviderHandler

@Decorators.error_decorator
def main():
    init.init()

    search_requests = fHandler.getSearchRequests()
    if len(search_requests) < 1:
        return Error.NOTHING_TO_SEARCH

    fHandler.cleanFileOutput()
    LOGHandler.cleanProgress()

    for request in search_requests:
        searchRequest(request[0], request[1])

    exit(0)

@Decorators.time_decorator
@Decorators.log_decorator
def searchRequests(search_requests):

    init.init()

    STATEHandler.setFlagEnd(False)
    fHandler.cleanFileOutput()
    LOGHandler.cleanProgress()

    for request in search_requests:
        if request[0] == "ВСЕ":
            for provider in Provider.Providers:
                if provider["active"]:
                    searchRequest(provider["name"], request[1])
        else:
            searchRequest(request[0], request[1])

    elements = fHandler.getElementsForParse()
    JSONParser.parseElements(elements)
    # print("parseElement() -> returned")

    STATEHandler.setFlagEnd(True)
    # print(f"flag_end: {STATEHandler.getFlagEnd()}")

    # print("searchRequests() -> return")
    return 0


@Decorators.time_decorator
@Decorators.log_decorator
def searchRequest(provider_name, search_request):
    provider_code = ProviderHandler().getProviderCodeByName(provider_name)
    if provider_code is None or not ProviderHandler().isActive(provider_code):
        return

    webWorker = wHandler.WebWorker(provider_code, search_request)
    webWorker.pullCrossRefToDB()

    # fHandler.removeLINKFile(provider_name, search_request)

    return


if __name__ == "__main__":
    main()
