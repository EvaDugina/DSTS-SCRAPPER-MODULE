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

    def open(self, url):
        try:
            self.__page.goto(url, wait_until="domcontentloaded")
        except Exception as e:
            print(f"Exception {str(e)}")

    def handleResponse(self, url, func_handl, match):
        try:
            response_json = self.expectResponseJson(url, match)
            if response_json != "":
                print(f"response_json: {json.dumps(response_json)}")
                func_handl(response_json)
        except Exception as e:
            print(f"Exception handleResponse(): {str(e)}")

    def expectResponseJson(self, url, match):
        try:
            with self.__page.expect_response(lambda response: match is not None and match in response.url
                                                              and response.status == 200) as response_info:
                self.open(url)
                response_json = response_info.value.json()
        except Exception as e:
            # print(f"Exception expectResponseJson(): {str(e)}")
            return ""
        return response_json

