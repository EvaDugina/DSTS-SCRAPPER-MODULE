from HANDLERS import WEBHandler as wHandl
from HANDLERS import FILEHandler as fHandl

if __name__=="__main__":

    search_requests = fHandl.getSearchRequests()

    for request in search_requests:

        catalogue_name = request[0]
        search_request = request[1]

        print("~~~~~~~~")
        print("SEARCH REQUEST: " + request + " -> START!")
        print()
        webWorker = wHandl.WebWorker(catalogue_name, search_request)
        status_parse = webWorker.pullCrossRefToDB()
        print("SEARCH REQUEST: " + request + " -> END!")
        print("~~~~~~~~")
        print()
