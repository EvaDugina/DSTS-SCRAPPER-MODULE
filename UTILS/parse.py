
def hasNameVariations(str):
    if str.find('/') != -1:
        return '/'
    if str.find('(') != -1:
        return '('
    return ''


def splitProducerNameBySpaces(producer_name):
    producer_name = producer_name.upper()
    flag_special_symb = hasSpecialSymbol(producer_name)
    while flag_special_symb != "":
        if flag_special_symb == ".":
            producer_name = producer_name.replace(flag_special_symb, "")
        else:
            producer_name = producer_name.replace(flag_special_symb, " ")
        flag_special_symb = hasSpecialSymbol(producer_name)
    return producer_name.strip()

def splitArticleNameBySpaces(article_name):
    article_name = article_name.upper()
    flag_special_symb = hasSpecialSymbol(article_name)
    while flag_special_symb != "":
        article_name = article_name.replace(flag_special_symb, " ")
        flag_special_symb = hasSpecialSymbol(article_name)
    return article_name.strip()



def hasSpecialSymbol(str):
    if str.find('-') != -1:
        return '-'
    if str.find('.') != -1:
        return '.'
    if str.find(',') != -1:
        return ','
    if str.find('/') != -1:
        return '/'
    return ''
