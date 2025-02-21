import json
from HANDLERS import FILEHandler as fHandl


def generateArticleJSON(article_name, catalogue_name, producer_name, article_info_json, type="real"):
    article_json = json.dumps({'name': article_name, 'catalogue_name': catalogue_name, 'producer_name': producer_name,
                               'type': type, 'info': article_info_json})
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