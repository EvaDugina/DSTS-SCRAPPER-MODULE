import json

from playwright.sync_api import sync_playwright


class PlaywrightHandler:
    __playwright = None

    def __init__(self):
        self.__playwright = sync_playwright().start()

    def getPlaywright(self):
        return self.__playwright


PLAYWRIGHT_HANDLER = PlaywrightHandler()


class PlaywrightBrowser:
    __playwright = None
    __browser = None
    __context = None
    __page = None

    def __init__(self, playwright):
        self._playwright = playwright
        self.__browser = self._playwright.chromium.launch()
        self.__context = self.__browser.new_context()

    def __enter__(self):
        self.__browser = self._playwright.chromium.launch()
        self.__context = self.__browser.new_context()
        print(f"PlaywrightBrowser --enter(): {self.__browser}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"PlaywrightBrowser --exit(): {self.__browser}")
        self.closeContext()
        self.__browser.close()

    def __del__(self):
        print(f"PlaywrightBrowser --del(): {self.__browser}")
        self.closeContext()
        self.__browser.close()

    def newPage(self):
        self.__page = self.__context.new_page()
        # return self.__page

    def closePage(self):
        if self.__page:
            self.__page.close()

    def closeContext(self):
        if self.__context:
            self.__context.close()

    def setPageTimeout(self, timeout_ms):
        self.__page.set_default_timeout(timeout_ms)

    # def handleResponse(self, func_handle_response):
    #     try:
    #         self.__page.on("response", func_handle_response)
    #     except Exception as e:
    #         print(f"Exception {str(e)}")

    # def removeResponseHandler(self):
    #     self.__page.remove_listener('response', self.__func_handle_response)
    #     self.__func_handle_response = None
    #     self.closePage()

    def open(self, url):
        try:
            self.__page.goto(url, wait_until="domcontentloaded")
        except Exception as e:
            print(f"Exception {str(e)}")

    def handleResponses(self, url, handler1, handler2, match1=None, match2=None):
        responses_jsons = self.expectResponsesJsons(url, match1, match2)
        handler1(responses_jsons[0])
        handler2(responses_jsons[1])

    def handleResponse(self, url, func_handl, match):
        response_json = self.expectResponseJson(url, match)
        func_handl(response_json)

    def expectResponsesJsons(self, url, match1, match2):
        response_json1 = self.expectResponseJson(url, match1)
        response_json2 = self.expectResponseJson(url, match2)
        return [response_json1, response_json2]

    def expectResponseJson(self, url, match):
        with self.__page.expect_response(lambda response: match is not None and match in response.url
                                                          and response.status == 200) as response_info:
            self.open(url)
            response = response_info.value
        return response.json()

