import cherrypy
import os
from jinja2 import Environment, FileSystemLoader
import csv
import re
from itertools import groupby
from collections import defaultdict
import string
import codecs, io
from io import StringIO, BytesIO
from datetime import datetime
from cherrypy import tools

env = Environment(loader=FileSystemLoader('html'))

class HelloWorld(object):
    @cherrypy.expose
    def index(self):
        data_to_show = ['Hello', 'world']
        tmpl = env.get_template('index.html')
        return tmpl.render(data=data_to_show)

    @cherrypy.expose
    def Obr(self, filename):
        reader = csv.reader(StringIO(filename.file.read().decode('utf-8')))

        UsersList = []  # Изначальный список
        newlist = []  # Список без дубликатов
        frequency = {}

        # Исключения имён
        for row in reader:
            Date = re.sub(r'[^0-9./]+', r'', row[0][0:8])
            User = row[1]
            if User != '-' and User != 'Администратор Пользователь' and User != 'Администратор \u3000' and ("под именем" in User) == False:
                List = Date + ' ' + User
            UsersList.append(List)
        UsersList = [el for el, _ in groupby(UsersList)]

        # Избавление от дупликатов
        for i in UsersList:
            if i not in newlist:
                newlist.append(i)

        # Разбитие на "слова"
        newlist = ",".join(newlist)
        newlist = re.sub(r'[^0-9/,]+', r'', newlist)
        newlist = newlist.replace("/", ".")
        newlist = newlist.split(",")

        # Подсчёт
        for word in newlist:
            count = frequency.get(word, 0)
            frequency[word] = count + 1
        frequency_list = frequency.keys()

        file_out = StringIO()
        writer = csv.writer(file_out, delimiter=",")
        for i in frequency_list:
            ITOG = [i, frequency[i]]
            writer.writerow(ITOG)
        file_out.seek(0)
        filename.filename = filename.filename.replace('.csv', '')
        filenames = "attachment; filename=" + filename.filename + "UniqUsersPerDay.csv"
        cherrypy.response.headers['Content-Type'] = 'text/csv'
        cherrypy.response.headers['Content-Disposition'] = filenames
        return file_out
        
    @cherrypy.expose
    @tools.decode(encoding='1251')
    def ObrFIO(self, filename, username):
        def parse_row(row):
            date, filename = row[:2]
            date = datetime.strptime(date, '%d/%m/%y, %H:%M')
            return f'{filename} {date.strftime("%d.%m.%y")}', (filename, date)

        SKIP_USER_NAMES = ['-', 'Администратор Пользователь', 'Администратор', 'под именем']

        reader = csv.reader(StringIO(filename.file.read().decode('utf-8')))
        reader = iter(reader)
        next(reader)
        users = sorted((row for row in map(parse_row, reader) if row[1][0] not in SKIP_USER_NAMES), key=lambda row: row[1][1])
        if username is not None:
            username = str(username).lower()
            users = filter(lambda row: row[1][0].lower().find(username) > -1, users)
        
        users = dict(users)

        file_out = StringIO()
        writer = csv.writer(file_out, delimiter=",")
        for name, date in users.values():
            writer.writerow((date.strftime('%d.%m.%y'), name))
        file_out.seek(0)
        filename.filename = filename.filename.replace('.csv', '')
        filenames = "attachment; filename=" + filename.filename + "UniqUsersPerDay.csv"
        cherrypy.response.headers['Content-Type'] = 'text/csv'
        cherrypy.response.headers['Content-Disposition'] = filenames
        return file_out

config = {
    'global': {
        'server.socket_host': '0.0.0.0',
        'server.socket_port': int(os.environ.get('PORT', 5000)),
    },
    '/assets': {
        'tools.staticdir.root': os.path.dirname(os.path.abspath(__file__)),
        'tools.staticdir.on': True,
        'tools.staticdir.dir': 'assets',
    }
}

cherrypy.quickstart(HelloWorld(), '/', config=config)
