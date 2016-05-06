from __future__ import absolute_import
import numpy as np
from flask import Flask, request, redirect, url_for, render_template, jsonify
import logging
from werkzeug.utils import secure_filename
import os
import json
import uuid
from .util import utils
from . import model_cloudsql
from . import tasks
from . import memcache_config

def create_app(config, debug=False, testing=False, config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(config)

    app.debug = debug
    app.testing = testing

    if config_overrides:
        app.config.update(config_overrides)

    # Configure logging
    if not app.testing:
        logging.basicConfig(level=logging.INFO)

    # Setup the data model.
    with app.app_context():
        model = model_cloudsql
        model.init_app(app)

    session_server_key = app.config['SESSION_KEY']
    memcache_client = memcache_config.get_memcache_client()

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

    def allowed_import(filename):
        return '.' in filename and filename.rsplit('.', 1)[1] in ['JSON', 'json']

    @app.route('/')
    def index():
        books = model.load_selected()
        return render_template('index.html', books = books)

    @app.route('/select_book/<book_id>', methods=['POST'])
    def slct_book(book_id):
        session_client_key = str(uuid.uuid4())
        book = model.load_book(book_id)
        memcache_client.set_multi(utils.add_cache_keys(book, session_server_key, session_client_key))
        book["nodes"], book["links"] = utils.get_nodes_links(characters=book['characters'], occurrences = book['occurrences'], n=2, extent=[0,None])
        book["id"] = session_client_key
        return jsonify(book)

    @app.route('/uploadajax', methods=['POST'])
    def upldfile():
        if request.method == 'POST':
            session_client_key = str(uuid.uuid4())
            file = request.files['file']
            q = tasks.get_books_queue()
            if file and allowed_file(file.filename):
                filetext = file.read().decode('utf-8')
                q.enqueue(tasks.process_book, filetext, session_server_key, session_client_key)
            elif file and allowed_import(file.filename):
                data = json.loads(file.read())
                q.enqueue(tasks.process_json, data, session_server_key, session_client_key)
            else:
                return redirect('/bad_extension')
            return jsonify(session_key = session_client_key)

    @app.route('/update', methods=['POST'])
    def upd_viz():
        if request.method == 'POST':
            session_client_key = request.json['client_key']
            logging.info('Received client key: %s' % session_client_key)
            book = utils.strip_cache_keys(memcache_client.get_multi([session_server_key+session_client_key+'_'+k for k in utils.get_book_keys()]))
            if book:
                logging.info('Got book from memcache')
                book["nodes"], book["links"] = utils.get_nodes_links(characters = book["characters"], occurrences = book["occurrences"], n=2, extent=[0, None])
                return jsonify(book)
            else:
                return jsonify(status = 1)

    @app.route('/charedit', methods=['POST'])
    def char2viz():
        if request.method == 'POST':
            data = request.json
            session_client_key = data['client_key']
            hierarchy = data['hierarchy']
            charwindow = int(data['charwindow'])/2
            extent = data['extent']
            logging.info("Attempting to load sentences from cache")
            book = utils.strip_cache_keys(memcache_client.get_multi([session_server_key+session_client_key+'_'+k for k in ['sentences']]))
            if book:
                logging.info("Loaded book from cache")
                characters = utils.parse_characters(hierarchy)
                occurrences = {}
                for char in characters:
                    occurrences[char['title']] = utils.get_occurrences(char, book['sentences'])
                memcache_client.set_multi(utils.add_cache_keys({'characters': characters, 'occurrences': occurrences}, session_server_key, session_client_key))
                nodes, links = utils.get_nodes_links(characters=characters, occurrences=occurrences, n=charwindow, extent=extent)
                return jsonify(nodes=nodes, links=links)
            else:
                return jsonify(status = 1)

    @app.route('/charlinks', methods=['POST'])
    def charextent():
        if request.method == 'POST':
            data = request.json
            extent = data['extent']
            charwindow = int(data['charwindow'])/2
            session_client_key = data['client_key']
            logging.info("Attempting to load book from cache")
            book = utils.strip_cache_keys(memcache_client.get_multi([session_server_key+session_client_key+'_'+k for k in ['characters', 'occurrences']]))
            if book:
                logging.info("Loaded book from cache")
                nodes, links = utils.get_nodes_links(characters = book["characters"], occurrences = book["occurrences"], n=charwindow, extent = extent)
                return jsonify(nodes=nodes, links=links)
            else:
                return jsonify(status = 1)

    @app.route('/titleedit', methods=['POST'])
    def edtitle():
        if request.method == 'POST':
            data = request.json
            title = data['title']
            session_client_key = data['client_key']
            logging.info('Updating title')
            memcache_client.set(session_server_key+session_client_key+'_title', title)
            return 'ok'

    @app.route('/export', methods=['POST'])
    def export_book():
        if request.method == 'POST':
            data = request.json
            session_client_key = data['client_key']
            logging.info("Attempting to load book from cache")
            book = utils.strip_cache_keys(memcache_client.get_multi([session_server_key+session_client_key+'_'+k for k in utils.get_book_keys()]))
            print book
            if book:
                logging.info("Loaded book from cache")
                return jsonify(book)
            else:
                return jsonify(status = 1)

    @app.route('/savetodb', methods=['POST'])
    def sv2db():
        if request.method == 'POST':
            data = request.json
            session_client_key = data['client_key']
            q = tasks.get_books_queue()
            q.enqueue(tasks.save_to_db, session_server_key, session_client_key)
            return jsonify(ok='ok')

    @app.route('/saveupdate', methods=['POST'])
    def svupd():
        if request.method == 'POST':
            session_client_key = request.json['client_key']
            logging.info('Getting book id from memcache')
            book_id = memcache_client.get(session_server_key+session_client_key+'_bookid')
            title = memcache_client.get(session_server_key+session_client_key+'_title')
            if book_id:
                logging.info('Book id is: %d' % book_id)
                return jsonify(book_id=book_id, title = title)
            else:
                return jsonify(status = 1)

    @app.route('/bad_extension')
    def extension_error():
        return "Only text files are allowed!"

    @app.route('/cleandb')
    def cleandatabase():
        q = tasks.get_books_queue()
        r = q.enqueue(tasks.clean_db)

    return app
