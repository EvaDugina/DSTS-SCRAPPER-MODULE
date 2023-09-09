#!/usr/bin/env python

import requests

from HANDLERS import WEBHandler as wHandl
from HANDLERS import FILEHandler as fHandl


# https://techorde.com/scraping-browser-xhr-requests-using-python/
# https://scrapism.lav.io/scraping-xhr/
# https://www.zenrows.com/blog/selenium-python-web-scraping#add-real-headers
# https://www.zenrows.com/blog/web-scraping-without-getting-blocked#why-is-web-scraping-not-allowed


if __name__=="__main__":

    # import requests
    # https: // www.youtube.com / watch?v = DqtlR0y0suo
    # url = "https://shop.donaldson.com/store/rest/fetchProductAttrAndRecentlyViewed"
    # querystring = {"id": "39794", "fpp": "P551424-316-541", "globalSearchFlag": "false", "_": "1694255986560"}
    # payload = ""
    # headers = {
    #     "cookie": "_ym_uid=1631135930373897084; velaro_firstvisit=^%^222021-09-08T21^%^3A19^%^3A53.213Z^%^22; velaro_visitorId=^%^22iVd6vCxQNEeputrfsVRsxA^%^22; _hjid=3ca22462-cbda-4de9-8c6e-890b1cd656a6; _hjSessionUser_64165=eyJpZCI6IjFhMGI4NzZlLTNiZDctNTZlMS05ODZiLTQ1Y2ZhODRiNjVkOSIsImNyZWF0ZWQiOjE2NzEwNDM0NTA4NTAsImV4aXN0aW5nIjp0cnVlfQ==; s_fid=6C0861A1CFD388C0-0A0E17E41816E781; s_vi=^[CS^]v1^|323E30732645E194-60001CD6C08918EB^[CE^]; _ga=GA1.3.325279740.1685872849; OptanonAlertBoxClosed=2023-06-04T10:01:13.407Z; _ym_d=1686815878; _fbp=fb.1.1692791546349.21032163; _gcl_au=1.1.1515802377.1693681082; _gid=GA1.2.771378523.1694085460; ln_or=eyIxOTkzOSI6ImQifQ^%^3D^%^3D; _ym_isad=2; _gid=GA1.3.771378523.1694085460; _fileDownloaded=false; at_check=true; s_cc=true; CartCount=1-9; s_sq=^%^5B^%^5BB^%^5D^%^5D; velaro_endOfDay=^%^222023-09-09T23^%^3A59^%^3A59.999Z^%^22; JSESSIONID=^\^hY3XIHfqcKO2sbo3-Bv_HCpmuKJKo6JkjQQGPnHG.gdcplecatg02:store-server-2^^; BIGipServerGDC_DMZ_dciorigin-shop=400649122.64288.0000; TS0159dbaf=01cef8c7d883b0a342294071a3f43faf8c60b4dfc94d0bea00c72c144bb2963ae7cf1c2b90abea7c21834a59e68417a710faf534d38aeaf29c9de1c0865a62c56148c50c8214dd5de070dd9f2191872fd21a2a0e3586e56f62b24b3c6dd87f7704e4593bc0; _hjSession_64165=eyJpZCI6ImU2MWIxMjBkLWIyZDYtNGIyNS05ZDNjLTMyODI0YzRhOWMyMyIsImNyZWF0ZWQiOjE2OTQyNTU2OTYwOTEsImluU2FtcGxlIjpmYWxzZX0=; _hjAbsoluteSessionInProgress=0; OptanonConsent=isGpcEnabled=0&datestamp=Sat+Sep+09+2023+13^%^3A34^%^3A56+GMT^%^2B0300+(^%^D0^%^9C^%^D0^%^BE^%^D1^%^81^%^D0^%^BA^%^D0^%^B2^%^D0^%^B0^%^2C+^%^D1^%^81^%^D1^%^82^%^D0^%^B0^%^D0^%^BD^%^D0^%^B4^%^D0^%^B0^%^D1^%^80^%^D1^%^82^%^D0^%^BD^%^D0^%^BE^%^D0^%^B5+^%^D0^%^B2^%^D1^%^80^%^D0^%^B5^%^D0^%^BC^%^D1^%^8F)&version=6.35.0&isIABGlobal=false&hosts=&consentId=4b50e940-fb46-468f-9592-b0e3d2ee37a1&interactionCount=3&landingPath=NotLandingPage&groups=C0001^%^3A1^%^2CC0003^%^3A1^%^2CC0002^%^3A1^%^2CC0004^%^3A1&AwaitingReconsent=false&geolocation=RU^%^3BMOW; mbox=PC^#111691350128204-676247.37_0^#1757500497^|session^#bbe3fa931d764a4b99a46ccff4ae3ed0^#1694257557; _uetsid=261dbaa04d7011ee8f50fb17959d466d; _uetvid=4cb96a007bdf11edb2bcbf04ba8acb36; gpv_p3=shop^%^3A^%^2Fstore^%^2Fru-ru^%^2Fproduct^%^2Fp551424^%^2F39794; _ga=GA1.2.325279740.1685872849; sessionExpiry=7200; AMCVS_211631365C190F8B0A495CFC^%^40AdobeOrg=1; AMCV_211631365C190F8B0A495CFC^%^40AdobeOrg=-1124106680^%^7CMCMID^%^7C69639804510096596081994692082918066722^%^7CMCAAMLH-1694860784^%^7C6^%^7CMCAAMB-1694860784^%^7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y^%^7CMCOPTOUT-1694263184s^%^7CNONE^%^7CMCSYNCSOP^%^7C411-19616^%^7CvVersion^%^7C5.2.0; ADRUM=s=1694255985568&r=https^%^3A^%^2F^%^2Fshop.donaldson.com^%^2Fstore^%^2Fru-ru^%^2Fproduct^%^2FP551424^%^2F39794^%^3F0; AKA_A2=A; _ga_9WYYFBQLF0=GS1.1.1694255695.72.0.1694255985.47.0.0; s_plt=^%^5B^%^5BB^%^5D^%^5D; s_pltp=^%^5B^%^5BB^%^5D^%^5D",
    #     "accept-language": "ru;q=0.9",
    #     "service_token": "3TuSgTm3MyS9ZL0adPDjYg==",
    #     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 YaBrowser/23.7.4.971 Yowser/2.5 Safari/537.36"
    # }
    # response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    # print(response.text.encode("utf-8"))

    fHandl.createLOGSDir()

    search_requests = fHandl.getSearchRequests()

    for request in search_requests:

        catalogue_name = request[0]
        search_request = request[1]

        fHandl.appendToFileLog("~~~~~~~~")
        fHandl.appendToFileLog("SEARCH REQUEST: " + search_request + " -> START!")
        fHandl.appendToFileLog("\n")
        webWorker = wHandl.WebWorker(catalogue_name, search_request)
        status_parse = webWorker.pullCrossRefToDB()
        fHandl.appendToFileLog("SEARCH REQUEST: " + search_request + " -> END!")
        fHandl.appendToFileLog("~~~~~~~~")
        fHandl.appendToFileLog("\n")

        fHandl.moveLINKToCompleated(catalogue_name, search_request)
