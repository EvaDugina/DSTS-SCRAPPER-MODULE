class Provider:

    def getMainUrl(self):
        pass

    def search(self, driver, page_number, search_request):
        pass

    def endCondision(self, page):
        pass

    def parseSearchResult(self, driver):
        pass

    def loadArticlePage(self, driver, article):
        pass

    def parseCrossReference(self, driver, article_id, timeout):
        pass
