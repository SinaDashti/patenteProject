from tabulate import tabulate
import pandas as pd
from bs4 import BeautifulSoup
import os
import sys
import requests
import mysql.connector
import time

start_time = time.time()
mydb = mysql.connector.connect(
                                host = "localhost",
                                user = "root",
                                passwd = "mysqlmysql",

                                # The below line must be a comment if
                                # the database already exists.

                                database = "patentedb"
                                )

# initializing the cursor of the dtabase

mycursor = mydb.cursor()
main_url = "https://www.patentati.it"
# creating database (just first time, the comment it)
# mycursor.execute("CREATE DATABASE patentedb")

################################################################################
# At this stage, first all the 25 sections required information, name and links,
# have extracted and stored in the section_dic. Then this information is stored
# in capitolo_list table.
# Before storing the information the capitolo_list table must be created.
################################################################################
r = requests.get('https://www.patentati.it/quiz-patente-b/lista-domande.php')
section_dic = dict()
domande = BeautifulSoup(r.text, 'lxml')
for lista_domande in domande.find_all('a', class_='box')[1:]:
    section_dic[
        lista_domande.text.strip()] = main_url + lista_domande.get('href')
Q = "CREATE TABLE capitolo_list \
    (capitolo VARCHAR (255), url_capitolo VARCHAR (255), \
    capitolo_id INTEGER AUTO_INCREMENT PRIMARY KEY)"
mycursor.execute(Q)
print('Creating tables')
print("--- %s seconds ---" % (time.time() - start_time))
# inserting array of values inside tables
#
sqlformula = "INSERT INTO capitolo_list (capitolo, url_capitolo) VALUES (%s, %s)"
capitoloValues = []
for cap,url_cap in section_dic.items():
    capitoloValues.append((cap,url_cap))
mycursor.executemany(sqlformula, capitoloValues)
print('Inserting in capitoplo')
print("--- %s seconds ---" % (time.time() - start_time))
# Pay attention without committing we do not see the changes.

mydb.commit()
################################################################################
# At this stage, by using the first table in the patentedb, the required
# information is queried from table. Then by looping through the chapter's url,
# one table has created, in which all topic and their specific page url,
# is mapped and stored.
################################################################################
Q = "SELECT capitolo, url_capitolo FROM capitolo_list"
mycursor.execute(Q)
myresult = mycursor.fetchall()

# Looping at each chapter

for (topic, section) in myresult:
    r = requests.get(section)
    domande = BeautifulSoup(r.text, 'lxml')
    list_argomenta = domande.find_all('a',
            class_='cardBox uk-flex uk-flex-center uk-flex-middle')

    # In the topic name the are a lot of replace method, because some charecters
    # make problem for table name in SQL, and also it is sliced at the end.

    table_name = topic.replace(',', '').replace(' ', '_').replace('\'',
            '_').replace('(', '').replace(')', '').replace(':', '')[:50]
#
#     # createsqltable = "DROP TABLE IF EXISTS " + table_name
#
    createsqltable = """CREATE TABLE """ + str(table_name) + ' (' \
        + 'topic_name VARCHAR (255), url_topic VARCHAR (255), ' \
        + 'topic_id INTEGER AUTO_INCREMENT PRIMARY KEY' \
        + ')'
    mycursor.execute(createsqltable)
    mydb.commit()

    sqlformula = """INSERT INTO """ + table_name \
        + """ (topic_name, url_topic) VALUES (%s, %s)"""

    # Loop inside each chapter

    tableValues = []
    for row in list_argomenta:
        tableValues.append((row.text.strip(), main_url + row['href']))
    mycursor.executemany(sqlformula, tableValues)
    mydb.commit()

print('Creating all question tables and inserting in them')
print("--- %s seconds ---" % (time.time() - start_time))
################################################################################
# At this stage, by using each table in the previous part, the question name and
# link are queried from tables. Then by looping through the chapter's url,
# one table has created, in which all topic and their specific page url,
# is mapped and stored. MUST BE EDITED
################################################################################

Q = "SELECT topic_name, url_topic from Segnali_di_pericolo"
query_all_table_name = "SHOW TABLES"
mycursor.execute(query_all_table_name)
list_of_topics_table = mycursor.fetchall()

c1 = 'Figura'
c2 = 'Domanda'
c3 = 'Risposta'


for topicTable in list_of_topics_table[1:]:
    query_topics_in_table = "SELECT topic_name, url_topic from " + topicTable[0]
    mycursor.execute(query_topics_in_table)
    list_of_topics_questions = mycursor.fetchall()

    for rows in list_of_topics_questions:
        ###
        r = requests.get(rows[1])
        source = BeautifulSoup(r.text, "lxml")
        table = source.find('table')
        table_row =table.find_all('tr')[1:]
        ###
        figura = []#
        # domanda = []
        # risposta = []
        tableValues = []#
        ###
        for tr in table_row:
            table_name = rows[0].replace(',', '').replace(' ', '_').replace('\'',
                        '_').replace('(', '').replace(')', '').replace(':', '').replace('km/h','km')[:50]
            question = tr.find_all('td', class_ = 'domanda')#
            answer = tr.find_all('td', class_ = 'risp')#
            # domanda.append(question[0].text)
            # risposta.append(answer[0].text.strip())
            headers = source.find('thead').find_all('td')#

            if len(headers) == 3:
                if tr.img:
                    figura.append(main_url + tr.img['src'])
                    tableValues.append((main_url + tr.img['src'], question[0].text, answer[0].text.strip()))
                elif len(figura) > 0:
                    figura.append(figura[len(figura)-1])
                    tableValues.append((figura[len(figura)-1], question[0].text, answer[0].text.strip()))
                else:
                    # figura.append(None)
                    tableValues.append((None, question[0].text, answer[0].text.strip()))
            elif len(headers) == 2:
                tableValues.append((question[0].text, answer[0].text.strip()))

        if len(headers) == 3:
            # df = pd.DataFrame({c1:figura, c2:domanda, c3:risposta})
            try:
                createsqltable = """CREATE TABLE """ + str(table_name) + ' (' \
                    + 'Figura VARCHAR (255), Domanda VARCHAR (500), Risposta CHAR,' \
                    + 'Domanda_id INTEGER AUTO_INCREMENT PRIMARY KEY' \
                    + ')'
                # createsqltable = """DROP TABLE """ + str(table_name)
                mycursor.execute(createsqltable)
                mydb.commit()
                # print(tabulate(df, headers = 'keys', tablefmt = 'psql', showindex = False))

                sqlformula = """INSERT INTO """ + table_name \
                    + """ (Figura, Domanda, Risposta) VALUES (%s, %s, %s)"""

                ##Loop inside each chapter

                mycursor.executemany(sqlformula, tableValues)
                mydb.commit()
            except Exception as e:
                 print(table_name)


        elif len(headers) == 2:
            try:
                # df = pd.DataFrame({c2:domanda, c3:risposta})
                createsqltable = """CREATE TABLE """ + str(table_name) + ' (' \
                    + 'Domanda VARCHAR (500), Risposta CHAR,' \
                    + 'Domanda_id INTEGER AUTO_INCREMENT PRIMARY KEY' \
                    + ')'

                # createsqltable = """DROP TABLE """ + str(table_name)
                mycursor.execute(createsqltable)
                mydb.commit()
                # print(tabulate(df, headers = 'keys', tablefmt = 'psql', showindex = False))

                sqlformula = """INSERT INTO """ + table_name \
                    + """ (Domanda, Risposta) VALUES (%s, %s)"""

                ## Loop inside each chapter

                mycursor.executemany(sqlformula, tableValues)
                mydb.commit()

            except Exception as e:
                print(table_name)

print('creating all question tables and inserting question')
print("--- %s seconds ---" % (time.time() - start_time))
