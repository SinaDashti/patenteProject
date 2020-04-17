import tabulate
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import time
from collections import defaultdict
import random
import urllib.request
import mysql.connector
from PIL import ImageTk, Image
from tkinter import *
# from tkinter import Tk, Button, Canvas, Label
from PIL import Image, ImageFont
import tkinter as tk
import textwrap

mydb = mysql.connector.connect(
                                host = "localhost",
                                user = "root",
                                passwd = "mysqlmysql",
                                database = "patentedb"
                                )
mycursor = mydb.cursor()
# because the spaces in capitolo column in capolo_list makes problem
# we should change also this column on the patenteSQL script
def name_correct(name):
    return name.replace(',','').replace(' ','_').replace('\'','_').\
    replace('(','').replace(')','').replace(':','').replace('km/h','km')[:50]


def replace_func(topic):
    temp = str(topic.find('span')).split('-1')[0].split('\r\n')
    if len(temp) > 1:
        temp = temp[1].strip().split('<')[0].strip()
        return name_correct(temp)
    else:
        return False

################################################################################
# First we go to a specific link, in which we can find the wiegth of each exam
# section. Then, we store each section and its weight in a dictionary. I used
# defaultdict, because based on different wigth, one section can have 1 or 2
# question in the exam. Finally, we loop through sections, and based on their
# wigth we map 1 or 2 random numbers, which are between 1 and the maximum number
# of each section argument. SO, until now we choosed random argument of each
# section.
################################################################################

r = requests.get('https://www.patentati.it/quiz-patente-b/argomento.php')
logic = BeautifulSoup(r.text, 'lxml')
separator = logic.find_all('div', class_='uk-grid uk-child-width-1-2@m pat-font uk-grid-match uk-margin-bottom')
argoment_exam_q_num = dict()


i=0
while i < 2:
    for row in separator[i]:
        if replace_func(row):
            if i == 0:
                argoment_exam_q_num[replace_func(row)] = 2
            else:
                argoment_exam_q_num[replace_func(row)] = 1
    i+=1

# matching the name of sections and their wieght
topic_rand = defaultdict(list)
mycursor.execute("SELECT * FROM capitolo_list")
section = mycursor.fetchall()
for row in section:
    arument_counter = """SELECT count(*) FROM """ + str(row[0])
    mycursor.execute(arument_counter)
    for arg_cnt in mycursor:
        for _ in range(0, argoment_exam_q_num[str(row[0])]):
            topic_rand[str(row[0])].append(random.randrange(1, arg_cnt[0] + 1))
            # print(str(row[0]), topic_rand[str(row[0])])

################################################################################
# At each section, based on its weight we perform a loop. I call it loop_1. In
# this loop, we select 1 or 2 random argument based on topic_id. Then, at each
# argument, we need to find its row length. Then, based on this row length, we
# choose a random row, inclucing figure's link, question and answer. In short,
# we find one of the 40 random question for the exam. Because, some question,
# does not have figure, we add None to some of our raw data. At the end, we have
# our data frame with 40 questions. Until now I did not decide to store this
# information in a seperate SQL table.
################################################################################

figura = []
domanda = []
risposta = []
for row in section:
    # loop_1
    for i in range(0, len(topic_rand[str(row[0])])):
        topic_select_for_exam = """SELECT topic_name FROM """ + str(row[0]) + \
        """ WHERE topic_id = """ + str(topic_rand[str(row[0])][i])
        mycursor.execute(topic_select_for_exam)
        exam_topic = mycursor.fetchone()
        topic_question_counter = """SELECT count(*) FROM """ + str(exam_topic[0])
        mycursor.execute(topic_question_counter)
        # loop_2
        for max_row_in_topic in mycursor:

            one_exam_record = """SELECT * FROM """ + str(exam_topic[0]) + \
            """ WHERE Domanda_id = """ + \
            str(random.randrange(1, max_row_in_topic[0] + 1))

            mycursor.execute(one_exam_record)
            # pay attention, I cannot use fetchone()
            final = mycursor.fetchall()
            if len(final[0]) == 4:
                figura.append(final[0][0])
                domanda.append(final[0][1])
                risposta.append(final[0][2])
            else:
                figura.append('None')
                domanda.append(final[0][0])
                risposta.append(final[0][1])

df = pd.DataFrame({'Figura':figura, 'Domanda':domanda, 'Risposta':risposta})
# print(df)

################################################################################
# We need to save the figures to give them to the GUI. Pay attention, the files
# save in ExamLogic branch local folder.
################################################################################
my_window = Tk()
my_window.geometry("1150x520+0+0")
my_window.resizable(width=False, height=False)
my_window.title("Patente")

class ImgFrame(Frame):
    def __init__(self, the_windows):
        super().__init__()
        self['height'] = 300
        self['width'] = 400
        self['bg'] = "white"

class SqrFrame(Frame):
    def __init__(self, the_windows):
        super().__init__()
        self['height'] = 300
        self['width'] = 300
        self['bg'] = "white"

class RectFrame(Frame):
    def __init__(self, the_windows):
        super().__init__()
        self['height'] = 300
        self['width'] = 1000
        self['bg'] = "white"

index_label = df.loc[df['Figura'] != 'None'].index.tolist()
image_list = []

for idx in range(len(df['Figura'])):
    if df.iloc[idx,0] != 'None':
        try:
            urllib.request.urlretrieve(df.iloc[idx,0], str(idx) + '.png')
            with Image.open(str(idx) + '.png') as temp_image:
                exam_img = temp_image.resize((300,292) ,Image.LANCZOS)
                exam_img.save(str(idx) + '.png', exam_img.format)
                image_list.append(ImageTk.PhotoImage(Image.open(str(idx) + '.png')))
        except Exception as e:
            pass
    elif df.iloc[idx,0] == 'None':
        image_list.append('None')

def image_var():

    global current_index
    global image_list

    if image_list[current_index] != 'None':

        return image_list[current_index]
    else:
        return ImageTk.PhotoImage(Image.open('temp.png'))

def question_wraper(question, width):

    temp = textwrap.wrap(question.strip(), width = width)
    question = ''
    for text in temp:
        question += text + '\n'

    return question

def dissable_button():
    global current_index
    if current_index == 0:
        button6['state'] = DISABLED
    elif current_index == 39:
        button9['state'] = DISABLED
    else:
        button6['state'] = ACTIVE
        button9['state'] = ACTIVE

current_index = 0
answers = ['' for _ in range(0, 40)]

def next_question(event):
    global current_index
    if current_index < 39:
        current_index += 1

        question_box.config(text = question_wraper(str(current_index+1)+'.'+df.loc[current_index]['Domanda'], 50))
        Label(img_fr).grid_forget()
        Label(img_fr, image = image_var()).grid(row = 0, column = 0)
        dissable_button()


def previous_question(event):
    global current_index
    if current_index > 0:
        current_index -= 1
        if current_index > -1:

            question_box.config(text = question_wraper(str(current_index+1)+'.'+df.loc[current_index]['Domanda'],50))
            Label(img_fr).grid_forget()
            Label(img_fr, image = image_var()).grid(row = 0, column = 0)
            dissable_button()


def true_answer():
    global remained
    global current_index
    global answers
    qlink[str(current_index)]['fg'] = 'green'
    answers[current_index] = 'V'
    remained = answers.count('')
    info_set(remained, info_var)
    next_question(current_index)

def false_answer():
    global remained
    global current_index
    global answers
    qlink[str(current_index)]['fg'] = 'red'
    answers[current_index] = 'F'
    remained = answers.count('')
    info_set(remained, info_var)
    next_question(current_index)


def timer_func(stop, label):
    global answers
    if stop > 0:
        m, s = divmod(stop, 60)
        time_left = str(m).zfill(2) + ':' + str(s).zfill(2) + '\r'
        stop -= 1
        label.set(time_left)
        frame_c.after(1000, lambda: timer_func(stop, label))
    else:
        answer_df = pd.DataFrame({'answers':answers})
        frame_c.destroy()
        correct_sum = sum(np.where(df.Risposta == answer_df.answers,
                            'True',
                            'False') == 'True'
                            )
        result = ''
        for var in range(0, 40):

            result += '{}{}{}{:2}'.format(
                                        str(var + 1).zfill(2),
                                        '.' ,
                                        df.iloc[var, 2],
                                        '')

        if correct_sum >= 36:
            question_box.config(text = "PASS with " +
                                        str(40 - correct_sum) +
                                        " False answers\n\n" +
                                        "Correct answers:\n\n" +
                                        question_wraper(result,30)
                                        )

        else:
            question_box.config(text = "FAIL with " +
                                        str(40 - correct_sum) +
                                        " False answers\n\n" +
                                        "Correct answers:\n\n" +
                                        question_wraper(result,30)
                                        )




counter = 2400
button_label = StringVar()
button_label.set(counter)
info_var = StringVar()
info_var.set('')
remained = 40

def info_set(remained_num, var_str):

    information = '{}{:2d}{}{}{:2d}{}'.format("Answered: " ,
                    abs(remained - 40),
                    '\n',
                    'Remained: ',
                    remained,
                    '\n')

    var_str.set(information)



def start_test():
    question_box.config(text = question_wraper(str(current_index+1)+'.'+str(df.loc[0]['Domanda']),50))
    info_set(40, info_var)
    timer_box = Label(frame_c, textvariable = button_label, font = "Courier 40")
    timer_box.grid(row = 0, column = 1, sticky = "ne")
    timer_func(counter, button_label)
    button4['state'] = DISABLED
    button6['state'] = ACTIVE
    button7['state'] = ACTIVE
    button8['state'] = ACTIVE
    button9['state'] = ACTIVE

def finish_test():
    global my_img
    timer_func(0, button_label)

    Label(img_fr).grid_forget()
    Label(img_fr, image = my_img).grid(row = 0, column = 0)
    button4['state'] = DISABLED
    button5['state'] = DISABLED
    button6['state'] = DISABLED
    button7['state'] = DISABLED
    button8['state'] = DISABLED
    button9['state'] = DISABLED


with Image.open('pat.png') as im:
    im1 = im.resize((300,292),Image.LANCZOS)
    im1.save('temp.png', im1.format)

my_img = ImageTk.PhotoImage(Image.open('temp.png'))

img_fr = ImgFrame(my_window)
img_holder = Label(img_fr, image = my_img).grid(row = 0, column = 0)


frame_a = SqrFrame(my_window)
frame_b = RectFrame(my_window)
frame_c = SqrFrame(my_window)
frame_d = SqrFrame(my_window)
frame_e = RectFrame(my_window)
frame_f = SqrFrame(my_window)

img_fr.grid(row = 0, column = 0)
frame_b.grid(row = 0, column = 1,sticky="wn")
frame_c.grid(row = 0, column = 2, sticky="ne")
frame_d.grid(row = 1, column = 0,sticky="wn")
frame_e.grid(row = 1, column = 1,sticky="wn")
frame_f.grid(row = 1, column = 2,sticky="n")


var_1 = ''

question_box = Label(frame_b, text = var_1, justify=LEFT, font = "Courier 18")
question_box.grid(sticky="wn")

button4 = Button(frame_d, padx=52, pady=11, text = 'START ', fg = 'blue',font = "Courier 60", command = start_test)
button5 = Button(frame_d, padx=52, pady=11, text = 'FINISH', fg = 'red', font = "Courier 60", command = finish_test)

button4.grid(row = 0, column = 0)
button5.grid(row = 1, column = 0)

button6 = Button(frame_e, state = DISABLED, padx =6, width = 4, height = 3, text='<',fg='gray', font = "Courier 55", command = lambda:previous_question(current_index))
button7 = Button(frame_e, state = DISABLED, padx =5 ,width = 4, height = 3, text='F',fg='red', font = "Courier 55", command = false_answer)

button6.pack(side=LEFT)
button7.pack(side=LEFT)

button8 = Button(frame_e, state = DISABLED, padx =5 ,width = 4, height = 3, text='V',fg='green', font = "Courier 55", command = true_answer)
button9 = Button(frame_e, state = DISABLED, padx =6 ,width = 4, height = 3, text='>',fg='gray', font = "Courier 55", command = lambda:next_question(current_index))
button8.pack(side=LEFT)
button9.pack(side=LEFT)

info_box = Label(frame_f, textvariable = info_var, justify=LEFT, font = "Courier 30")
info_box.grid(sticky="e")
# goto_frame = Frame(my_window)
# label_goTo = Label(my_window, text = "Go to:", fg = 'blue')
link_frame = Frame(my_window)
# label_goTo.grid(row=2, column=0,sticky="n")
link_frame.grid(row=2, column=1, sticky="n")
qlink = dict()
r = 3
c = 0
for i in range(0, 40):
    qlink[str(i)] = Label(link_frame,
                           text = str(i+1),
                           width=2,
                           height=1,
                           fg='blue',
                           anchor="w",
                           font = "Courier 16"
                           )

    qlink[str(i)].grid(row = r, column = c)
    c +=1
    if i > 0:
        if (i + 1) % 20 == 0:
            r += 1
            c = 0


my_window.mainloop()
