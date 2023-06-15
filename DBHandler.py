import psycopg2
import parse

conn = psycopg2.connect(dbname='dsts', user='postgres', port='5432',
                        password='postgres', host='localhost')
cursor = conn.cursor()


def getAllArticles():
    query = querySelectAllArticles()
    cursor.execute(query)
    return cursor.fetchall()

def getArticle(article_id):
    query = querySelectArticle(article_id)
    cursor.execute(query)
    return cursor.fetchone()

def getArticleByName(article_name, producer_id):
    query = querySelectArticleByName(article_name, producer_id)
    cursor.execute(query)
    return cursor.fetchone()

def getArticleAnalogs(article_id):
    analogs = []

    query = querySelectFirstArticleAnalogs(article_id)
    cursor.execute(query)
    for line in cursor.fetchall():
        analogs.append(getArticle(line[0]))

    query = querySelectSecondArticleAnalogs(article_id)
    cursor.execute(query)
    for line in cursor.fetchall():
        analogs.append(getArticle(line[0]))

    return analogs

def getProducerById(producer_id):
    query = querySelectProducerById(producer_id)
    cursor.execute(query)
    return cursor.fetchone()

def getProducerByName(producer_name):
    query = querySelectProducerByName(producer_name)
    cursor.execute(query)
    return cursor.fetchone()

def getProducerNameVariations(producer_id):
    name_variations = []

    query = querySelectProducerById(producer_id)
    cursor.execute(query)
    name_variations.append(cursor.fetchone()[1])

    query = querySelectProducerNameVarations(producer_id)
    cursor.execute(query)
    for line in cursor.fetchall():
        name_variations.append(line[2])

    return name_variations




def insertArticle(article_name, producer_id):
    article_name.upper().strip()
    if not isArticleExist(article_name, producer_id):
        query = queryInsertArticle(article_name, producer_id)
        cursor.execute(query)
        article_id = cursor.fetchone()[0]
        conn.commit()

        # print(f"INSERTED ARTICLE: {article_id} - {article_name} {producer_id}")
        return article_id
    else:
        return getArticleByName(article_name, producer_id)[0]

def insertArticles(articles):
    query = ""
    for article in articles:
        article_name = article['article_name'].upper().strip()
        producer_id = article['producer_id']

        query += queryInsertArticle(article_name, producer_id)

    cursor.execute(query)
    conn.commit()

    # print(f"INSERTED ARTICLES")


def insertProducer(producer_line):
    producer_line = producer_line.upper()

    original_producer_name = ""
    variation_symbol = parse.hasNameVariations(producer_line)
    if bool(variation_symbol):
        original_producer_name = producer_line.split(variation_symbol)[0].strip()
    else:
        original_producer_name = producer_line.strip()

    special_symb = parse.hasSpecialSymbol(original_producer_name)
    producer_name = parse.convertToStandartProducerName(original_producer_name)

    producer_id = -1
    if not isProducerExist(producer_name):
        query = queryInsertProducer(producer_name)
        cursor.execute(query)
        conn.commit()
        producer_id = cursor.fetchone()[0]

        print(f"INSERTED PRODUCER: {producer_id} - {producer_name}")

    else:
        producer = getProducerByName(producer_name)
        if producer:
            producer_id = producer[0]
        else:
            producer = getProducerByName(producer_name.replace(" ", ""))
            producer_id = producer[0]


    if bool(special_symb):
        insertProducerNameVariation(producer_id, original_producer_name)

    if bool(variation_symbol):
        producer_name = producer_line.split(variation_symbol)[1]
        if variation_symbol == '(':
            producer_name = producer_name[:-1]
        producer_name = producer_name.strip()
        insertProducer(producer_name)

    return producer_id


def insertArticleAnalogs(article_id, articles_comparison):
    query = ""
    for article_cmp_id in articles_comparison:
        if not isInComparisonTable(article_id, article_cmp_id):
            query += queryInsertArticlesComparison(article_id, article_cmp_id)
            # print(f"INSERTED ANALOGS: {article_id} {article_cmp_id}")
    if query != "":
        cursor.execute(query)
        conn.commit()

def insertProducerNameVariation(producer_id, name_variation):
    name_variation.upper()
    if not hasProducerNameVariation(producer_id, name_variation):
        query = queryInsertProducerNameVariation(producer_id, name_variation)
        cursor.execute(query)
        conn.commit()
        print(f"INSERTED PRODUCER_NAME_VARIATION: {producer_id} - {name_variation}")



def isArticleExist(article_name, producer_id):
    query = querySelectArticleByName(article_name, producer_id)
    cursor.execute(query)
    return bool(cursor.rowcount)
def isProducerExist(producer_name):
    query = querySelectProducerByName(producer_name)
    cursor.execute(query)
    flag1 = bool(cursor.rowcount)

    producer_name = producer_name.replace(" ", "")
    query = querySelectProducerByName(producer_name)
    cursor.execute(query)
    flag2 = bool(cursor.rowcount)
    return flag1 or flag2
def isInComparisonTable(main_article_id, comparison_article_id):
    analogs = getArticleAnalogs(main_article_id)
    for analog in analogs:
        if analog[0] == comparison_article_id:
            return True
    return False


def hasProducerNameVariation(producer_id, name_variation):
    for name in getProducerNameVariations(producer_id):
        if name == name_variation:
            return True
    return False




def querySelectProducerById(producer_id):
    return "SELECT * FROM producers " \
           f'WHERE id = {producer_id};'

def querySelectAllArticles():
    return "SELECT * FROM articles;"

def querySelectArticle(article_id):
    return "SELECT * FROM articles " \
           f'WHERE id = {article_id};'

def querySelectArticleByName(article_name, producer_id):
    return "SELECT * FROM articles " \
           f"WHERE article_name = '{article_name}' AND producer_id = {producer_id};"

def querySelectProducerByName(producer_name):
    return "SELECT * FROM producers " \
           f"WHERE producer_name = '{producer_name}';"

def querySelectProducerNameVarations(producer_id):
    return "SELECT * FROM producer_name_variations " \
           f"WHERE producer_id = {producer_id};"


def querySelectFirstArticleAnalogs(article_id):
    return "SELECT first_article_id as article_id FROM articles_comparison " \
           f'WHERE second_article_id = {article_id};'


def querySelectSecondArticleAnalogs(article_id):
    return "SELECT second_article_id as article_id FROM articles_comparison " \
           f'WHERE first_article_id = {article_id};'




def queryInsertArticle(article_name, producer_id):
    return "INSERT INTO public.articles(article_name, producer_id) " \
           + f"VALUES ('{article_name}', {producer_id}) " \
             f"RETURNING id;"

def queryInsertProducer(producer_name):
    return "INSERT INTO public.producers(producer_name) " \
           + f"VALUES ('{producer_name}') " \
             "ON CONFLICT (producer_name) DO NOTHING " \
             "RETURNING id;"

def queryInsertProducerNameVariation(producer_id, producer_name):
    return "INSERT INTO public.producer_name_variations(producer_id, producer_name) " \
           + f"VALUES ('{producer_id}', '{producer_name}') " \
             "RETURNING id;"

def queryInsertArticlesComparison(first_srticle_id, second_article_id):
    return "INSERT INTO public.articles_comparison(first_article_id, second_article_id) " \
           + f'VALUES ({first_srticle_id}, {second_article_id});'
