import logging
from flask import current_app
from gcloud import pubsub #, storage
import psq
# import requests
from . import model_cloudsql as model
# from . import storage
from .util.content import Content
from .util import utils
from . import memcache_config

def get_books_queue():
	ps_client = pubsub.Client(project=current_app.config['PROJECT_ID'])
	# ds_client = storage.Client(project=current_app.config['PROJECT_ID'])
	# return psq.Queue(ps_client,storage=psq.DatastoreStorage(ds_client),extra_context=current_app.app_context)
	return psq.Queue(ps_client, extra_context = current_app.app_context)

def process_book(filetext, session_server_key, session_client_key):
	book_key = session_server_key + session_client_key
	logging.info('Processing book content')
	content = Content(filetext, basedir = current_app.config['BASE_DIR'])
	book = {}
	book['id'] = session_client_key
	book['sentences'] = [s for s in content.sentences]
	book['sentiments'] = [s for s in content.sentiment]
	book['characters'] = [{'title': content.entities[i], 'names': [content.entities[i]]} for i in range(len(content.entities))]
	book['occurrences'] = {}
	for char in book['characters']:
		book['occurrences'][char['title']] = utils.get_occurrences(char, book['sentences'])
	book['title'] = 'Click to edit title'
	book['nodes']=[{"name": char['title'], "occurrences": book['occurrences'][char['title']]} for char in book['characters']]
	book['links'] = utils.get_links(book['occurrences'], characters=book["characters"], n=2, extent=[0,None])
	memcache_client = memcache_config.get_memcache_client()
	logging.info('Setting book in cache under client key %s' % session_client_key)
	memcache_client.set(book_key, book)
	logging.info('Commiting book to the database')
	model.commit_book(book, select = 0)
	return session_client_key

def process_json(data, session_server_key, session_client_key):
	if not set(['sentences', 'sentiments', 'characters', 'occurrences', 'title']).issubset(set(data.keys())):
		logging.error("Data format is incorrect")
		return None
	else:
		book_key = session_server_key + session_client_key
		book = data
		book['id'] = session_client_key
		book['nodes']=[{"name": char['title'], "occurrences": book['occurrences'][char['title']]} for char in book['characters']]
		book['links'] = utils.get_links(book['occurrences'], characters=book["characters"], n=2, extent=[0,None])
		memcache_client = memcache_config.get_memcache_client()
		memcache_client.set(book_key, book)
		# model.commit_book(book, select = 0)
	return session_client_key

def update_characters(characters, occurrences, session_server_key, session_client_key):
	book_key = session_server_key + session_client_key
	memcache_client = memcache_config.get_memcache_client()
	book = memcache_client.get(book_key)
	logging.info('Trying to get book')
	if book:
		logging.info('Got book, updating characterss')
		book['characters'] = characters
		book['occurrences'] = occurrences
		memcache_client.set(book_key, book)
		logging.info('Updating book')
	# model.update_chars(session_client_key, characters = characters, occurrences = occurrences)
	return session_client_key

def save_to_db(book, session_server_key, session_client_key):
	logging.info('Saving book to database')
	book_id = model.save_book(session_client_key, book)
	logging.info('Got book id from db. It is %d' % book_id)
	memcache_client = memcache_config.get_memcache_client()
	memcache_client.set(session_server_key[:10]+session_client_key, book_id)
	return session_client_key