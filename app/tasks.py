import logging
from flask import current_app
from gcloud import pubsub
import psq
from . import model_cloudsql as model
from .util.content import Content
from .util import utils
from . import memcache_config

def get_books_queue():
	ps_client = pubsub.Client(project=current_app.config['PROJECT_ID'])
	return psq.Queue(ps_client, extra_context = current_app.app_context)

def cache_book(book, session_server_key, session_client_key):
	memcache_client = memcache_config.get_memcache_client()
	logging.info('Setting book in cache under client key %s' % session_client_key)
	memcache_client.set_multi(utils.add_cache_keys(book, session_server_key, session_client_key))

def process_book(filetext, session_server_key, session_client_key):
	logging.info('Processing book content')
	content = Content(filetext, basedir = current_app.config['BASE_DIR'])
	book = {}
	book['title'] = 'Click to edit title'
	book['sentences'] = [s for s in content.sentences]
	book['sentiments'] = [s for s in content.sentiment]
	book['characters'] = [{'title': content.entities[i], 'names': [content.entities[i]]} for i in range(len(content.entities))]
	book['occurrences'] = {}
	for char in book['characters']:
		book['occurrences'][char['title']] = utils.get_occurrences(char, book['sentences'])
	cache_book(book, session_server_key, session_client_key)

def process_json(data, session_server_key, session_client_key):
	if not utils.get_book_keys().issubset(set(data.keys())):
		logging.error("Data format is incorrect")
		return None
	else:
		cache_book(data, session_server_key, session_client_key)

def save_to_db(session_server_key, session_client_key):
	memcache_client = memcache_config.get_memcache_client()
	book = utils.strip_cache_keys(memcache_client.get_multi([session_server_key+session_client_key+'_'+k for k in utils.get_book_keys()]))
	logging.info('Saving book to database')
	book['id'] = session_client_key
	book_id = model.commit_book(book, select = 1)
	logging.info('Got book id from db. It is %d' % book_id)
	memcache_client.set(session_server_key+session_client_key+'_bookid', book_id)

def clean_db():
	model.delete_unselected()