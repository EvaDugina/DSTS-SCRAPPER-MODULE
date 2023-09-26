import json

import psycopg2

from HANDLERS import FILEHandler as fHandl

from UTILS import parse


class DBWorker:
    CONNECTION = None

    def __init__(self, port):
        self.CONNECTION = psycopg2.connect(dbname='dsts', user='dsts', port=port,
                        password='123456', host='localhost')


    def getArticleById(self, article_id) -> list:
        query = querySelectArticle(article_id)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        if not bool(cursor.rowcount):
            return []

        return cursor.fetchone()


    def getArticleByName(self, article_name, producer_id) -> list:
        query = querySelectArticleByNameAndProducerId(article_name, producer_id)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        if not bool(cursor.rowcount):
            return []

        return cursor.fetchone()


    def getArticleAnalogs(self, article_id) -> list[int]:
        group_id = self.getGroupArticleAnalogs(article_id)
        query = querySelectArticleAnalogsByGroup(group_id)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        analogs = []
        for analog in cursor.fetchall():
            analogs.append(analog[0])

        if not bool(cursor.rowcount):
            return []

        return analogs


    def getGroupArticleAnalogs(self, article_id) -> int:
        query = querySelectGroupArticleAnalogs(article_id)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        if not bool(cursor.rowcount):
            return -1

        return cursor.fetchone()[0]


    def getProducerById(self, producer_id) -> list:
        query = querySelectProducerById(producer_id)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        if not bool(cursor.rowcount):
            return []

        return cursor.fetchone()

    def getProducerIdByNameAndCatalogueName(self, producer_name, catalogue_name) -> int:
        producer_name = parse.splitProducerNameBySpaces(producer_name)
        producer = self.getProducerByName(producer_name)
        if producer == []:
            producer = self.getProducerByNameAndCatalogueName(producer_name, catalogue_name)
            if producer == []:
                return -1
            else:
                producer_id = producer[0]
        else:
            producer_id = producer[0]

        return producer_id


    def getProducerByName(self, producer_name) -> list:
        query = querySelectProducerByName(producer_name)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        if not bool(cursor.rowcount):
            return []

        return cursor.fetchone()


    def getProducerByNameAndCatalogueName(self, producer_name, catalogue_name) -> list:
        query = querySelectProducerNameVariation(producer_name, catalogue_name)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        if not bool(cursor.rowcount):
            return []

        return cursor.fetchone()


    def getProducerNameVariations(self, producer_id) -> list:
        query = querySelectProducerNameVariations(producer_id)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        if not bool(cursor.rowcount):
            return []

        return cursor.fetchall()


    def getArticleInfo(self, article_id, catalogue_name) -> list:
        query = querySelectArticleInfo(article_id, catalogue_name)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        if not bool(cursor.rowcount):
            return []

        return cursor.fetchone()


    def getMaxGroupId(self) -> int:
        query = querySelectMaxGroupNumber()

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        if not cursor.rowcount:
            return 0

        # return cursor.fetchall()
        return cursor.rowcount

    #####################################################################
    # INSERTS TO DB
    #####################################################################

    def insertArticle(self, article_line, producer_id, catalogue_name, type=None) -> int:
        article_line.upper().strip()

        article_name = parse.concatArticleName(article_line)

        if not self.isArticleExist(article_name, producer_id):
            if type is None:
                query = queryInsertArticle(article_name, producer_id)
            else:
                query = queryInsertArticleWithType(article_name, producer_id, type)

            cursor = self.CONNECTION.cursor()
            cursor.execute(query)
            self.CONNECTION.commit()
            article_id = cursor.fetchone()[0]

            fHandl.appendToFileLog(f"\t\t\tINSERTED ARTICLE: {article_id} - {article_name} {producer_id}")
        else:
            article = self.getArticleByName(article_name, producer_id)
            article_id = article[0]

        # Добавляем себя в producers_name_variations
        self.insertArticleNameVariation(article_id, article_line, catalogue_name)
        self.insertArticleNameVariation(article_id, article_name, catalogue_name)

        # Добавляем себя в articles_comparison
        # self.insertArticleAnalog(article_id, article_id, catalogue_name)

        return article_id



    def insertProducer(self, producer_line, catalogue_name) -> int:
        producer_line = producer_line.upper()
        producer_name = producer_line

        # Вытаскиваем оригинальные и аналогичные имена производителей из строк по типу: JD(JohnDeere)
        variation_symbol = parse.hasNameVariations(producer_line)
        if bool(variation_symbol):
            producer_name = producer_line.split(variation_symbol)[0]
        producer_name = producer_name.strip()

        # Склеиваем имя производителя без прбелов и спец. символов
        producer_name_with_spaces = parse.splitProducerNameBySpaces(producer_name)

        # Добавляем в БД producers
        producer_id = -1
        if not self.isProducerExist(producer_name_with_spaces):
            query = queryInsertProducer(producer_name_with_spaces)

            cursor = self.CONNECTION.cursor()
            cursor.execute(query)
            self.CONNECTION.commit()

            producer_id = cursor.fetchone()[0]

            fHandl.appendToFileLog(f"\t\tINSERTED PRODUCER: {producer_id} - {producer_name_with_spaces}")
        else:
            producer = self.getProducerByName(producer_name_with_spaces)
            producer_id = producer[0]

        # Добавляем себя в БД producers_name_variations
        self.insertProducerNameVariation(producer_id, producer_line, catalogue_name)

        # Добавляем аналогичное имя из линии без конкатенаций
        if bool(variation_symbol):
            self.insertProducerNameVariation(producer_id, producer_name, catalogue_name)
            producer_name = producer_line.split(variation_symbol)[1]
            if variation_symbol == '(':
                producer_name = producer_name[:-1]
            self.insertProducerNameVariation(producer_id, producer_name, catalogue_name)

        return producer_id

    def insertArticleAnalog(self, article_id, analog_article_id, catalogue_name) -> int:

        group_id = self.getGroupArticleAnalogs(article_id)

        # Добавляем себя в качестве аналога
        if group_id == -1:
            group_id = self.getMaxGroupId()
            if group_id:
                group_id += 1
            else:
                group_id = 1

        query = queryInsertArticlesComparison(group_id, analog_article_id, catalogue_name)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        fHandl.appendToFileLog(f"\t\t\tINSERTED ANALOG g{group_id}: {article_id}")

        return group_id

    def insertArticleAnalogs(self, article_id, analog_article_ids, catalogue_name):

        group_id = self.getGroupArticleAnalogs(article_id)

        # Добавляем себя в качестве аналога
        if group_id == -1:
            group_id = self.insertArticleAnalog(article_id, article_id, catalogue_name)

        query = ""
        for analog_article_id in analog_article_ids:
            # if not self.isAnalogInComparisonTable(article_id, analog_article_id, catalogue_name):
            query += queryInsertArticlesComparison(group_id, analog_article_id, catalogue_name)
            fHandl.appendToFileLog(f"\t\t\tINSERTED ANALOGS: {article_id} {analog_article_id}")

        if query != "":
            cursor = self.CONNECTION.cursor()
            cursor.execute(query)
            self.CONNECTION.commit()

        # Убираем повторяющиеся строки
        query = queryDeleteSimmilarArticlesComparison(group_id)
        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()


    def insertProducerNameVariation(self, producer_id, name_variation, catalogue_name):
        name_variation = name_variation.upper()

        if not self.hasProducerNameVariation(producer_id, name_variation, catalogue_name):
            query = queryInsertProducerNameVariation(producer_id, name_variation, catalogue_name)

            cursor = self.CONNECTION.cursor()
            cursor.execute(query)
            self.CONNECTION.commit()

            fHandl.appendToFileLog(f"\t\tINSERTED PRODUCER_NAME_VARIATION: {producer_id} - {name_variation} - {catalogue_name}")


    def insertArticleNameVariation(self, article_id, name_variation, catalogue_name):
        name_variation = name_variation.upper()

        if not self.hasArticleNameVariation(article_id, name_variation, catalogue_name):
            query = queryInsertArticleNameVariation(article_id, name_variation, catalogue_name)

            cursor = self.CONNECTION.cursor()
            cursor.execute(query)
            self.CONNECTION.commit()

            fHandl.appendToFileLog(f"\t\tINSERTED ARTICLE_NAME_VARIATION: {article_id} - {name_variation} - {catalogue_name}")


    def insertArticleInfo(self, article_id, catalogue_name, url, type, output_json):

        if self.getArticleInfo(article_id, catalogue_name) == []:
            query = queryInsertArticleInfo(article_id, catalogue_name, url, type, json.dumps(output_json))

            cursor = self.CONNECTION.cursor()
            cursor.execute(query)
            self.CONNECTION.commit()

            fHandl.appendToFileLog(f"\t\tINSERTED ARTICLE INFO: {article_id} - {catalogue_name}")


    def insertCharacteristics(self, charachterictics_json):
        # print(charachterictics_json)
        for charachterictic in charachterictics_json:
            self.insertUniqueCharacteristic(charachterictic)

    def insertUniqueCharacteristic(self, charachterictic_name):
        query = queryInsertCharacteristic(charachterictic_name)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()


    #####################################################################
    # CHECK-FUNCTIONS
    #####################################################################


    def isArticleExist(self, article_name, producer_id) -> bool:
        query = querySelectArticleByNameAndProducerId(article_name, producer_id)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        return bool(cursor.rowcount)

    def isProducerExist(self, producer_name) -> bool:
        query = querySelectProducerByName(producer_name)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        return bool(cursor.rowcount)


    def isAnalogInComparisonTable(self, article_id, analog_article_id, catalogue_name) -> bool:
        group_id = self.getGroupArticleAnalogs(article_id)
        query = queryCheckArticleAnalog(group_id, analog_article_id, catalogue_name)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        return bool(cursor.rowcount)


    def hasArticleNameVariation(self, article_id, name_variation, catalogue_name) -> bool:
        query = queryCheckArticleNameVariation(article_id, name_variation, catalogue_name)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        return bool(cursor.rowcount)

    def hasProducerNameVariation(self, producer_id, name_variation, catalogue_name) -> bool:
        query = queryCheckProducerNameVariation(producer_id, name_variation, catalogue_name)

        cursor = self.CONNECTION.cursor()
        cursor.execute(query)
        self.CONNECTION.commit()

        return bool(cursor.rowcount)




def querySelectProducerById(producer_id):
    return "SELECT * FROM producers " \
           f'WHERE id = {producer_id};'

def querySelectProducerNameVariations(producer_id):
    return "SELECT * FROM producers_name_variations " \
           f'WHERE producer_id = {producer_id};'

def querySelectArticle(article_id):
    return "SELECT * FROM articles " \
           f'WHERE id = {article_id};'

def querySelectArticleByNameAndProducerId(article_name, producer_id):
    return "SELECT DISTINCT articles.*, articles_name_variations.article_name AS article_name_variation FROM articles " \
           "INNER JOIN articles_name_variations ON articles_name_variations.article_id = articles.id " \
           f"WHERE articles_name_variations.article_name = '{article_name}' AND articles.producer_id = {producer_id};"

def querySelectProducerByName(producer_name):
    return "SELECT DISTINCT producers.*, producers_name_variations.producer_name AS producer_name_variation FROM producers " \
           "INNER JOIN producers_name_variations ON producers_name_variations.producer_id = producers.id " \
           f"WHERE producers_name_variations.producer_name = '{producer_name}';"

def querySelectProducerNameVariation(producer_name, catalogue_name):
    return "SELECT * FROM producers_name_variations " \
           f"WHERE producer_name = '{producer_name}' AND catalogue_name = '{catalogue_name}';"

def queryCheckProducerNameVariation(producer_id, producer_name, catalogue_name):
    return "SELECT * FROM producers_name_variations " \
           f"WHERE producer_id = {producer_id} AND producer_name = '{producer_name}' AND catalogue_name = '{catalogue_name}';"

def queryCheckArticleNameVariation(article_id, article_name, catalogue_name):
    return "SELECT * FROM articles_name_variations " \
           f"WHERE article_id = {article_id} AND article_name = '{article_name}' AND catalogue_name = '{catalogue_name}';"

def querySelectProducerNameVarations(producer_id):
    return "SELECT * FROM producers_name_variations " \
           f"WHERE producer_id = {producer_id};"

def querySelectGroupArticleAnalogs(article_id):
    return "SELECT group_id FROM articles_comparison " \
           f'WHERE article_id = {article_id};'

def querySelectArticleAnalogsByGroup(group_id):
    return "SELECT article_id FROM articles_comparison " \
           f'WHERE group_id = {group_id};'

def queryCheckArticleAnalog(group_id, analog_article_id, catalogue_name):
    return "SELECT * FROM articles_comparison " \
           f"WHERE group_id = {group_id} AND article_id = {analog_article_id} AND catalogue_name = '{catalogue_name}';"

def querySelectArticleInfo(article_id, catalogue_name):
    return "SELECT * FROM articles_details " \
           f"WHERE article_id = {article_id} AND catalogue_name = '{catalogue_name}';"

def querySelectMaxGroupNumber():
    return "SELECT DISTINCT(group_id) AS max_group_id FROM articles_comparison ORDER BY group_id DESC;"



def queryInsertArticle(article_name, producer_id):
    return "INSERT INTO public.articles(article_name, producer_id, type) " \
           + f"VALUES ('{article_name}', {producer_id}, 0) " \
             f"RETURNING id;"

def queryInsertArticleWithType(article_name, producer_id, type):
    return "INSERT INTO public.articles(article_name, producer_id, type) " \
           + f"VALUES ('{article_name}', {producer_id}, {type}) " \
             f"RETURNING id;"

def queryInsertProducer(producer_name):
    return "INSERT INTO public.producers(producer_name) " \
           + f"VALUES ('{producer_name}') " \
             "RETURNING id;"

def queryInsertProducerNameVariation(producer_id, producer_name, catalogue_name):
    return "INSERT INTO public.producers_name_variations(producer_id, producer_name, catalogue_name) " \
           + f"VALUES ({producer_id}, '{producer_name}', '{catalogue_name}') " \
             "RETURNING id;"

def queryInsertArticleNameVariation(article_id, article_name, catalogue_name):
    return "INSERT INTO public.articles_name_variations(article_id, article_name, catalogue_name) " \
           + f"VALUES ({article_id}, '{article_name}', '{catalogue_name}') " \
             "RETURNING id;"

def queryInsertArticlesComparison(group_id, article_id, catalogue_name):
    return "INSERT INTO public.articles_comparison(group_id, article_id, catalogue_name) " \
           + f"VALUES ({group_id}, {article_id}, '{catalogue_name}');"

def queryInsertArticleInfo(article_id, catalogue_name, url, type, json):
    return "INSERT INTO public.articles_details(article_id, catalogue_name, url, type, json) " \
           + f"VALUES ({article_id}, '{catalogue_name}', '{url}', '{type}', $antihype1${json}$antihype1$);"

def queryInsertCharacteristic(characteristic):
    return "INSERT INTO characteristics_comparison(characteristic_original, characteristic_alt) " \
           + f"VALUES ('{characteristic}', '{characteristic}') ON CONFLICT (characteristic_original) DO NOTHING;"




def queryDeleteSimmilarArticlesComparison(group_id):
    return "DELETE FROM articles_comparison AS a " \
           "USING articles_comparison as b " \
           f"WHERE a.id > b.id AND a.group_id = {group_id}" \
           "AND a.group_id = b.group_id AND a.article_id = b.article_id AND a.catalogue_name = b.catalogue_name;"