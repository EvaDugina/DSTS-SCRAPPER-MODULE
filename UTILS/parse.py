
def hasNameVariations(str):
    if str.find('/') != -1:
        return '/'
    if str.find('(') != -1:
        return '('
    return ''



def convertToStandartProducerName(producer_name):
    producer_name.upper()
    flag_special_symb = hasSpecialSymbol(producer_name)
    if flag_special_symb == "":
        return producer_name.strip()
    else:
        if flag_special_symb == ".":
            producer_name = producer_name.replace(flag_special_symb, "")
        else :
            producer_name = producer_name.replace(flag_special_symb, " ")
        producer_name = convertToStandartProducerName(producer_name)
    return producer_name.strip()



def hasSpecialSymbol(str):
    if str.find('-') != -1:
        return '-'
    if str.find('.') != -1:
        return '.'
    if str.find(',') != -1:
        return ','
    return ''
