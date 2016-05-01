import logging
from flask import current_app
from gcloud import pubsub, storage
import psq
import requests
from . import model_cloudsql as model
# from . import storage
from .util.content import Content
from .util import utils

def get_books_queue():
	ps_client = pubsub.Client(project=current_app.config['PROJECT_ID'])
	ds_client = storage.Client(project=current_app.config['PROJECT_ID'])
	print ds_client

	return psq.Queue(
		ps_client,
		storage=psq.DatastoreStorage(ds_client),
		extra_context=current_app.app_context)

def process_book(filetext):
	content = Content(filetext, basedir = current_app.config['BASE_DIR'])
	book = {}
	book['sentences'] = [s for s in content.sentences]
	book['sentiments'] = [s for s in content.sentiment]
	book['characters'] = [{'title': content.entities[i], 'names': [content.entities[i]]} for i in range(len(content.entities))]
	book['occurrences'] = {}
	for char in book['characters']:
		book['occurrences'][char['title']] = utils.get_occurrences(char, book['sentences'])
	book['title'] = 'Click to edit title'
	book['nodes']=[{"name": char['title'], "occurrences": book['occurrences'][char['title']]} for char in book['characters']]
	book['links'] = utils.get_links(book['occurrences'], characters=book["characters"], n=2, extent=[0,None])
	return book

def process_json(data):
	if not set(['sentences', 'sentiments', 'characters', 'occurrences', 'title']).issubset(set(data.keys())):
		logging.error("Data format is incorrect")
		return None
	else:
		book = data
		book['nodes']=[{"name": char['title'], "occurrences": book['occurrences'][char['title']]} for char in book['characters']]
		book['links'] = utils.get_links(book['occurrences'], characters=book["characters"], n=2, extent=[0,None])
		return book