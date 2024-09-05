#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://stackoverflow.com/questions/63564559/greenlet-error-cannot-switch-to-a-different-thread
# from gevent import monkey

import Decorators

# monkey.patch_all()

import logging


logging.getLogger().setLevel(logging.INFO)

Providers = [
    {
        "name": "DONALDSON",
        "code": 0,
        "active": True
    },
    {
        "name": "HIFI",
        "code": 1,
        "active": True
    },
    {
        "name": "MANN",
        "code": 2,
        "active": True
    },
    {
        "name": "FLEETGUARD",
        "code": 3,
        "active": True
    },
    {
        "name": "SF",
        "code": 4,
        "active": False
    },
    {
        "name": "BALDWIN",
        "code": 5,
        "active": False
    },
    {
        "name": "FILFILTER",
        "code": 6,
        "active": True
    }
]

class ProviderHandler:

    def isActive(self, provider_code):
        if provider_code < len(Providers):
            return Providers[provider_code]["active"]
        raise Exception("isActive() index out of range")

    def getProviderByProviderCode(self, provider_code):
        if not provider_code < len(Providers):
            raise Exception("getProviderNameByCode() index out of range")

        provider_name = self.getProviderNameByCode(provider_code)
        return self.getProviderByProviderName(provider_name)

    def getProviderByProviderName(self, provider_name):
        if provider_name == "DONALDSON":
            from PROVIDERS.Donaldson import Donaldson
            return Donaldson
        elif provider_name == "HIFI":
            from PROVIDERS.HiFi import HiFi
            return HiFi()
        elif provider_name == "MANN":
            from PROVIDERS.Mann import Mann
            return Mann
        elif provider_name == "FLEETGUARD":
            from PROVIDERS.Fleetguard import Fleetguard
            return Fleetguard
        # elif provider_name == "SF":
        #     from PROVIDERS.SF import SF
        #     return lambda producer_id, dbHandler: SF(producer_id, dbHandler)
        # elif provider_name == "BALDWIN":
        #     from PROVIDERS.Baldwin import Baldwin
        #     return lambda producer_id, dbHandler: Baldwin(producer_id, dbHandler)
        elif provider_name == "FILFILTER":
            from PROVIDERS.FilFilter import FilFilter
            return FilFilter

        raise Exception("getProviderByProviderName() incorrect provider name")

    def getProviderNameByCode(self, provider_code):
        if not provider_code < len(Providers):
            raise Exception("getProviderNameByCode() index out of range")
        return Providers[provider_code]["name"]

    def getProviderCodeByName(self, provider_name):
        for provider in Providers:
            if provider["name"] == provider_name:
                return provider["code"]
        return None

    def getArticleBaseURLbyProviderName(self, provider_name, article_name):
        provider = self.getProviderByProviderName(provider_name)()
        return provider.getProductUrl(article_name)


class Provider:

    max_page = 1

    def __init__(self):
        pass

    def getMainUrl(self):
        pass

    def getProductUrl(self, article_name):
        pass

    def getName(self):
        pass

    @Decorators.log_decorator
    def getPageCount(self, driver, search_request):
        pass

    def endCondition(self, page):
        pass


    @Decorators.log_decorator
    def search(self, driver, page_number, search_request):
        pass

    @Decorators.log_decorator
    def parseSearchResult(self, driver, pageNumber):
        pass

    @Decorators.log_decorator
    def parseCrossReferenceResult(self, driver, pageNumber):
        pass

    @Decorators.log_decorator
    def loadArticlePage(self, driver, article_url, search_type):
        pass

    @Decorators.log_decorator
    def getArticleType(self, driver) -> str:
        pass

    @Decorators.log_decorator
    def saveJSON(self, driver, article_url, article_name, type, search_request, analog_article_name, analog_producer_name):
        pass

    def addAnalogToJSON(self, analog_article_name, analog_producer_name, json):
       pass
