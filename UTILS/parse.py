
def hasNameVariations(str):
    if str.find('/') != -1:
        return '/'
    if str.find('(') != -1:
        return '('
    return ''


def splitProducerNameBySpaces(producer_name):
    producer_name = producer_name.upper()
    flag_special_symb = hasSpecialSymbolProducer(producer_name)
    while flag_special_symb != "":
        if flag_special_symb == ".":
            producer_name = producer_name.replace(flag_special_symb, "")
        else:
            producer_name = producer_name.replace(flag_special_symb, " ")
        flag_special_symb = hasSpecialSymbolProducer(producer_name)
    return producer_name.strip()

def concatArticleName(article_name):
    article_name = article_name.upper()
    flag_special_symb = hasSpecialSymbolArticle(article_name)
    while flag_special_symb != "":
        article_name = article_name.replace(flag_special_symb, "")
        flag_special_symb = hasSpecialSymbolArticle(article_name)
    return article_name.strip()

def hasSpecialSymbolProducer(str):
    if str.find('-') != -1:
        return '-'
    if str.find('.') != -1:
        return '.'
    if str.find(',') != -1:
        return ','
    if str.find('/') != -1:
        return '/'
    return ''

def hasSpecialSymbolArticle(str):
    if str.find('-') != -1:
        return '-'
    if str.find('.') != -1:
        return '.'
    if str.find(',') != -1:
        return ','
    if str.find('/') != -1:
        return '/'
    if str.find(' ') != -1:
        return ' '
    return ''

def convertSpacesToURLSpaces(str):
    return str.replace(" ", "%20")

def hasDigits(str):
    return any(chr.isdigit() for chr in str)

def parseOutputFile(output_file_lines):
    output = []
    catalogue_name = ""
    for line in output_file_lines:
        if len(line) < 1:
            continue

        if line[0] == "!":
            line_elems = line.replace("! ", "").split(" | ")
            catalogue_name = line_elems[0]
            main_article_array = {
                "type": "main_article",
                "catalogue_name": line_elems[0],
                "article_id": line_elems[1],
                "article_name": line_elems[2],
                "producer_name": line_elems[3]
            }
            output.append(main_article_array)
        elif line[0] == ">":
            line_elems = line.replace("> ", "").split(" | ")
            analog = {
                "type": "analog_article",
                "article_id": line_elems[0],
                "article_name": line_elems[1],
                "catalogue_name": catalogue_name,
                "producer_name": line_elems[2]
            }
            output.append(analog)
        else:
            output.append({
                "type": "text",
                "text": line
            })

    return output

