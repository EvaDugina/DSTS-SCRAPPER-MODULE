from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Combobox
import webWorker as web

_width = 800
_height = 600

window = Tk()
window.title("ПОИСК ПО КАТАЛОГУ DONALDSON")
window.geometry(f'{_width}x{_height}')
window.resizable = False


def clicked():
    search_request = txt_search_request.get()
    producer_name = combo_producer_name.get()
    print(search_request + " " + producer_name)
    if checkFiledsEmpty(search_request, producer_name):
        status_parse = web.webWork(search_request, producer_name)
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


lbl = Label(window, text="ВВЕДИТЕ АРТУКУЛ ДЛЯ ПОИСКА ПО КАТАЛОГУ DONALDSON: ")
lbl.grid(column=0, row=0)

txt_search_request = Entry(window)
txt_search_request.grid(column=1, row=0)


lbl = Label(window, text="ВЫБЕРИТЕ НАЗВАНИЕ ПРОИЗВОДИТЕЛЯ: ")
lbl.grid(column=0, row=1)

combo_producer_name = Combobox(window)
combo_producer_name['values'] = ("DONALDSON", "FIL-FILTER")
combo_producer_name.current(0)
combo_producer_name.grid(column=1, row=1)

btn = Button(window, text="ПОИСК", command=clicked)
btn.grid(column=1, row=2)

window.mainloop()
