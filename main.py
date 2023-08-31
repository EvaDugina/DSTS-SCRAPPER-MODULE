from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Combobox

from HANDLERS import WEBHandler as web


_width = 800
_height = 600

window = Tk()
window.title("ПОИСК ПО КАТАЛОГУ DONALDSON")
window.geometry(f'{_width}x{_height}')
window.resizable = False


def clickedPullCrossRef():
    search_request = input_article_name.get()
    catalogue_name = combo_producer_name.get()
    print(search_request + " " + catalogue_name)
    if checkFiledsEmpty(search_request, catalogue_name):

        webWorker = web.WebWorker(catalogue_name, search_request)
        status_parse = webWorker.pullCrossRefToDB()

        if status_parse == "SUCCESS":
            messagebox.showinfo('РЕЗУЛЬТАТ ВЫПОЛНЕНИЯ', 'ДАННЫЕ УСПЕШНО ПОЛУЧЕНЫ!')
        else:
            messagebox.showinfo('РЕЗУЛЬТАТ ВЫПОЛНЕНИЯ', status_parse)
    else:
        messagebox.showinfo('Ошибка', 'Заполните все поля!')

def checkFiledsEmpty(search_request, producer_name):
    if search_request != "" and producer_name != "":
        return True
    return False



frame = Frame(
   window,
   padx=10,
   pady=10
)
frame.pack(expand=True)

text_article_name = Label(
    frame,
    text="АРТУКУЛ ДЛЯ ПОИСКА ПО КАТАЛОГУ  "
)
text_article_name.grid(row=1, column=1)

input_article_name = Entry(
    frame, width=25
)
input_article_name.grid(row=1, column=2)

text_name_producer = Label(
    frame,
    text="НАЗВАНИЕ ПРОИЗВОДИТЕЛЯ  ",
)
text_name_producer.grid(row=2, column=1)

combo_producer_name = Combobox(frame, width=25)
combo_producer_name['values'] = ("DONALDSON")
combo_producer_name.current(0)
combo_producer_name.grid(row=2, column=2)

btn = Button(frame, text="СКОПИРОВАТЬ ДАННЫЕ ПО КРОСС-РЕФЕРЕНСУ", command=clickedPullCrossRef)
btn.grid(row=3, column=2)

window.mainloop()
