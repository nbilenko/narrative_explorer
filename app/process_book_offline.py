import sys
import os
import json
from flask import Flask
from util.content import Content
from util import utils
import model_cloudsql

basedir = os.path.abspath(os.path.dirname(__file__)) 
app = Flask(__name__)
app.config.from_pyfile(basedir+'/../config.py')

model = model_cloudsql
model.app = app
model.init_app(app)

def process_book(filename):
	extension = filename.rsplit('.', 1)[1]
	if extension == 'txt':
		with open(filename, 'r') as f:
			filetext = f.read()
			content = Content(filetext, basedir = basedir+'/../')
			book = {}
			book['id'] = '0'
			book['sentences'] = [s for s in content.sentences]
			book['sentiments'] = [s for s in content.sentiment]
			book['characters'] = [{'title': content.entities[i], 'names': [content.entities[i]]} for i in range(len(content.entities))]
			book['occurrences'] = {}
			for char in book['characters']:
				book['occurrences'][char['title']] = utils.get_occurrences(char, book['sentences'])
			book['title'] = 'Click to edit title'
			with app.app_context():
				model.commit_book(book, select = 0)
	elif extension == 'json' or extension == 'JSON':
		with open(filename, 'r') as f:
			data = json.loads(f.read())
			book = data
			book['id'] = 0
			with app.app_context():
				model.commit_book(book, select = 0)


if __name__ == '__main__':
	process_book(sys.argv[1])