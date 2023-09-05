#!/usr/bin/env python

from HANDLERS import WEBHandler as wHandl
from HANDLERS import FILEHandler as fHandl


if __name__=="__main__":

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
