import json
import threading


def parseCrossRefDonaldsonJSON(start_index, end_index, json_string, article_id, number_thread, dbHandler):
    print(f'T{number_thread}: START PARSING!')
    for i in range (start_index, end_index+1):
        cross_ref_el = json_string['crossReferenceList'][i]

        producer_name = cross_ref_el['manufactureName']
        producer_id = dbHandler.insertProducer(producer_name)
        # print(producer_name)
        analogs = []
        for article_name in cross_ref_el['manufacturePartNumber']:
            analog_article_id = dbHandler.insertArticle(article_name, producer_id)
            analogs.append(analog_article_id)

        dbHandler.insertArticleAnalogs(article_id, analogs)

    print(f'T{number_thread}: END PARSING!')


def parseCrossRef(json_string, article_id, dbHandler):

    # init events
    e1 = threading.Event()
    e2 = threading.Event()
    e3 = threading.Event()
    e4 = threading.Event()

    start_index_e2 = len(json_string['crossReferenceList']) // 4
    start_index_e3 = len(json_string['crossReferenceList']) // 2
    start_index_e4 = len(json_string['crossReferenceList']) // 4 * 3

    # init threads
    t1 = threading.Thread(target=parseCrossRefDonaldsonJSON,
                          args=(0, start_index_e3, json_string, article_id, 1, dbHandler))
    t2 = threading.Thread(target=parseCrossRefDonaldsonJSON,
                          args=(start_index_e3, len(json_string['crossReferenceList'])-1, json_string, article_id, 2, dbHandler))

    # t2 = threading.Thread(target=parseCrossRefDonaldsonJSON, args=(start_index_e2, start_index_e3, json_string, article_id, 2))
    # t3 = threading.Thread(target=parseCrossRefDonaldsonJSON, args=(start_index_e3, start_index_e4, json_string, article_id, 3))
    # t4 = threading.Thread(target=parseCrossRefDonaldsonJSON, args=(start_index_e4, len(json_string['crossReferenceList']) - 1, json_string, article_id, 4))

    # start threads
    t1.start()
    t2.start()
    # t3.start()
    # t4.start()

    # e1.set()  # initiate the first event

    # join threads to the main thread
    t1.join()
    t2.join()
    # t3.join()
    # t4.join()

def generateArticleJSON(article_name, producer_name, catalogue_name, article_info_json):
    article_json = json.dumps({'name': article_name, 'catalogue_name': catalogue_name, 'producer_name': producer_name,
                               'info': article_info_json})
    # print(article_json)
    return article_json


def convertSTRtoJSON(str):
    return json.dumps(str)



