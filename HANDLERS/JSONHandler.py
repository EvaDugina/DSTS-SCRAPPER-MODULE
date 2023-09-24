import json
import threading
from HANDLERS import FILEHandler as fHandl


def parseCrossRefDonaldsonJSON(start_index, end_index, json_string, article_id, number_thread, dbHandler):
    fHandl.appendToFileLog(f'T{number_thread}: START PARSING!')
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

    fHandl.appendToFileLog(f'T{number_thread}: END PARSING!')


def generateArticleJSON(article_name, producer_name, catalogue_name, article_info_json):
    article_json = json.dumps({'name': article_name, 'catalogue_name': catalogue_name, 'producer_name': producer_name,
                               'info': article_info_json})
    # print(article_json)
    return article_json

def generateItemCrossRefJSON(producer_name, article_id):
    item_cross_ref = {
        "manufactureName": f"{producer_name}",
        "manufacturePartNumber": [f"{article_id}"],
        "manufactureNameSortableValue": f"{producer_name}",
        "notes": ["", ""],
        "type": "old"
    }
    return item_cross_ref

def appendOldAnalogToJSON(article_json, new_article_name, producer_name):
    article_json = json.loads(article_json)
    article_json['info']['crossReference'].append(generateItemCrossRefJSON(producer_name, new_article_name))
    article_json = json.dumps(article_json)
    return article_json

def convertSTRtoJSON(str):
    return json.dumps(str)