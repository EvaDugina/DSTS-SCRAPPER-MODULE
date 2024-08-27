import json
import threading
from HANDLERS import FILEHandler as fHandl


def parseCrossRefDonaldsonJSON(start_index, end_index, json_string, article_id, number_thread, dbHandler):
    fHandl.appendToFileLog(f'T{number_thread}: START PARSING!')
    for i in range (start_index, end_index+1):
        cross_ref_el = json_string['crossReferenceList'][i]

        producer_name = cross_ref_el['producerName']
        producer_id = dbHandler.insertProducer(producer_name)
        # print(producer_name)
        analogs = []
        for article_name in cross_ref_el['articleNames']:
            analog_article_id = dbHandler.insertArticle(article_name, producer_id)
            analogs.append(analog_article_id)

        dbHandler.insertArticleAnalogs(article_id, analogs)

    fHandl.appendToFileLog(f'T{number_thread}: END PARSING!')


def generateArticleJSON(article_name, catalogue_name, producer_name, article_info_json, type="real"):
    article_json = json.dumps({'name': article_name, 'catalogue_name': catalogue_name, 'producer_name': producer_name,
                               'type': type, 'info': article_info_json})
    # print(article_json)
    return article_json

def generateItemCrossRefJSON(producer_name, article_ids, type):
    item_cross_ref = {
        "producerName": f"{producer_name}",
        "articleNames": [],
        "type": type
    }
    for article_id in article_ids:
        item_cross_ref["articleNames"].append(article_id)
    return item_cross_ref

def appendOldAnalogToJSON(article_json, article_name, producer_name):
    article_json = json.loads(article_json)
    article_json['info']['crossReference'].append(generateItemCrossRefJSON(producer_name, [article_name], "old"))
    article_json = json.dumps(article_json)
    return article_json

def appendOldAnalogsToJSON(article_json, article_names, producer_name):
    article_json = json.loads(article_json)
    article_json['info']['crossReference'].append(generateItemCrossRefJSON(producer_name, article_names, "old"))
    article_json = json.dumps(article_json)
    return article_json

def appendAnalogToJSON(article_json, article_name, producer_name):
    article_json = json.loads(article_json)
    article_json['info']['crossReference'].append(generateItemCrossRefJSON(producer_name, [article_name], "real"))
    article_json = json.dumps(article_json)
    return article_json

def appendAnalogsToJSON(article_json, article_names, producer_name):
    article_json = json.loads(article_json)
    article_json['info']['crossReference'].append(generateItemCrossRefJSON(producer_name, article_names, "real"))
    article_json = json.dumps(article_json)
    return article_json

def convertSTRtoJSON(str):
    return json.dumps(str)