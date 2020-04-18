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

    SKIP_USER_NAMES = ['-', 'Администратор Пользователь', 'Администратор', 'под именем']
    
    @cherrypy.expose
    def index(self):
        data_to_show = ['Hello', 'world']
        tmpl = env.get_template('index.html')
        return tmpl.render(data=data_to_show)
        
    def parse_row(self, row):
        date, filename = row[:2]
        date = datetime.strptime(date, '%d/%m/%y, %H:%M')
        return f'{filename} {date.strftime("%d.%m.%y")}', (filename, date)

    @cherrypy.expose
    def ObrFIO(self, file, username=None, target_encoding='1251'):
        reader = csv.reader(StringIO(file.file.read().decode('utf-8')))
        reader = iter(reader)
        next(reader)
        users = sorted((row for row in map(self.parse_row, reader) if row[1][0] not in self.SKIP_USER_NAMES), key=lambda row: row[1][1])
        if username is not None and username:
            username = str(username).lower()
            users = filter(lambda row: row[1][0].lower().find(username) > -1, users)
        
        users = dict(users)

        file_out = StringIO()
        writer = csv.writer(file_out, delimiter=",")
        for name, date in users.values():
            writer.writerow((date.strftime('%d.%m.%y'), name))
        file_out.seek(0)
        filename = file.filename.replace('.csv', '')
        filenames = f"attachment; filename={filename}_UniqUsersPerDay.csv"
        cherrypy.response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        cherrypy.response.headers['Content-Disposition'] = filenames
        return file_out.read().encode(target_encoding)

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
