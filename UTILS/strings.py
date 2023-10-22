INTERNET_ERROR = "ОТСУТСВУЕТ ПОДКЛЮЧЕНИЕ К ИНТРНЕТУ!"
UNDEFIND_PRODUCER = "НЕИЗВЕСТНЫЙ ПРОИЗВОДИТЕЛЬ!"
UNDEFIND_BROWSER = "БРАУЗЕР НЕ НАЙДЕН!"
INCORRECT_LINK = "НЕКОРРЕКТНАЯ ССЫЛКА!"
INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE = "НЕКОРРЕКТНАЯ ССЫЛКА или ИЗМЕНИЛАСЬ СТРУКТУРА САЙТА!"
SUCCESS = "SUCCESS"

def getConnectionErrorMessage(catalogue_name):
    return f"Плохое интернет-соединение или сайт {catalogue_name} временно недоступен."
