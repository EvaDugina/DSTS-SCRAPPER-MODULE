
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
        "active": False
    },
    {
        "name": "FLEETGUARD",
        "code": 3,
        "active": False
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
            return lambda producer_id, dbHandler: Donaldson(producer_id, dbHandler)
        elif provider_name == "HIFI":
            from PROVIDERS.HiFi import HiFi
            return lambda producer_id, dbHandler: HiFi(producer_id, dbHandler)
        # elif provider_name == "MANN":
        #     from PROVIDERS.Mann import Mann
        #     return lambda producer_id, dbHandler: Mann(producer_id, dbHandler)
        # elif provider_name == "FLEETGUARD":
        #     from PROVIDERS.Fleetguard import Fleetguard
        #     return lambda producer_id, dbHandler: Fleetguard(producer_id, dbHandler)
        # elif provider_name == "SF":
        #     from PROVIDERS.SF import SF
        #     return lambda producer_id, dbHandler: SF(producer_id, dbHandler)
        # elif provider_name == "BALDWIN":
        #     from PROVIDERS.Baldwin import Baldwin
        #     return lambda producer_id, dbHandler: Baldwin(producer_id, dbHandler)
        elif provider_name == "FILFILTER":
            from PROVIDERS.FilFilter import FilFilter
            return lambda producer_id, dbHandler: FilFilter(producer_id, dbHandler)

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

    def getArticleBaseURLbyProviderName(self, provider_name):
        provider = self.getProviderByProviderName(provider_name)(None, None)
        return provider.getProductUrl()


class Provider:

    max_page = 1
    _dbHandler = None

    _article_cross_ref_json = dict()
    _article_info_json = dict()

    def __init__(self, producer_id=None, dbHandler=None):
        if producer_id is not None and dbHandler is not None:
            self._producer_id = producer_id
            self._dbHandler = dbHandler
            self._producer_name = dbHandler.getProducerById(self._producer_id)

    def getMainUrl(self):
        pass

    def getProductUrl(self):
        pass

    def getCatalogueName(self):
        pass

    # def getArticleFromURL(self, url):
    #     pass

    def getProducerId(self, article):
        pass

    def getPageCount(self, driver, search_request):
        pass

    def endCondition(self, page):
        pass



    def search(self, driver, page_number, search_request):
        pass

    def parseSearchResult(self, driver, pageNumber):
        pass

    def loadArticlePage(self, driver, article_url, search_type):
        pass

    def getArticleType(self, driver) -> str:
        pass

    def parseCrossReference(self, main_article_name, producer_name, type, cross_ref):
        pass



    def saveJSON(self, driver, article_url, article_name, type, search_request, analog_article_name, analog_producer_name):
        pass

    def addAnalogToJSON(self, analog_article_name, analog_producer_name, json):
       pass

    # def getAnalogs(self, article_url, article_id):
    #     pass

    def setInfo(self, article_name, producer_name, info_json):
        pass

    def goBack(self, driver):
        pass
