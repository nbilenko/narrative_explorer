from __future__ import absolute_import
import numpy as np
from flask import Flask, request, redirect, url_for, send_from_directory, render_template, jsonify
import logging
from werkzeug.utils import secure_filename
import os
import json
import uuid
# from app.util.content import Content
from .util.utils import parse_characters, get_occurrences, get_links
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
        current_book = model.load_book(book_id)
        current_book['book_id'] = book_id
        current_book["links"] = get_links(current_book['occurrences'], characters=current_book['characters'], n=2, extent=[0,None])
        current_book["nodes"] = [{"name": char['title'], "occurrences": current_book['occurrences'][char['title']]} for char in current_book['characters']]
        current_book["id"] = session_client_key
        memcache_client.set(session_server_key+session_client_key, current_book)
        return jsonify(current_book)

    @app.route('/uploadajax', methods=['POST'])
    def upldfile():
        if request.method == 'POST':
            session_client_key = str(uuid.uuid4())
            file = request.files['file']
            q = tasks.get_books_queue()
            if file and allowed_file(file.filename):
                filetext = file.read().decode('utf-8')
                r = q.enqueue(tasks.process_book, filetext, session_server_key, session_client_key)
            elif file and allowed_import(file.filename):
                data = json.loads(file.read())
                r = q.enqueue(tasks.process_json, data, session_server_key, session_client_key)
            else:
                return redirect('/bad_extension')
            return jsonify(session_key = session_client_key)

    @app.route('/update', methods=['POST'])
    def upd_viz():
        if request.method == 'POST':
            session_client_key = request.json['client_key']
            logging.info('Received client key: %s' % session_client_key)
            session_key = session_server_key+session_client_key
            book = memcache_client.get(session_key)
            # if book:
                # return jsonify(book)
            # else:
                # book = model.load_book_bykey(session_client_key)
            if book:
                return jsonify(book)
            else:
                return jsonify(status = 1)

    @app.route('/charajax', methods=['POST'])
    def char2viz():
        if request.method == 'POST':
            data = request.json
            session_client_key = data['client_key']
            hierarchy = data['hierarchy']
            charwindow = int(data['charwindow'])/2
            extent = data['extent']
            logging.info("Attempting to load book from cache")
            book = memcache_client.get(session_server_key+session_client_key)
            if book:
                logging.info("Loaded book %s from cache" % book["title"])
                current_book = book
            # else:
                # logging.info("Could not find book in the cache, loading from the database")
                # current_book = model.load_book_bykey(session_client_key)
            if current_book:
                new_characters = parse_characters(hierarchy)
                occurrences = {}
                for char in new_characters:
                    occurrences[char['title']] = get_occurrences(char, current_book['sentences'])
                memcache_client.set(session_server_key+session_client_key, current_book)
                q = tasks.get_books_queue()
                r = q.enqueue(tasks.update_characters, new_characters, occurrences, session_server_key, session_client_key)
                nodes=[{"name": char['title'], "occurrences": occurrences[char['title']]} for char in new_characters]
                if len(new_characters):
                    links = get_links(occurrences, characters=new_characters, n=charwindow, extent=extent)
                else:
                    links = {}
                memcache_client.set(session_server_key+session_client_key, current_book)
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
            book = memcache_client.get(session_server_key+session_client_key)
            if book:
                logging.info("Loaded book %s from cache" % book["title"])
                current_book = book
            # else:
                # logging.info("Could not find book in the cache, loading from the database")
                # current_book = model.load_book_bykey(session_client_key)
            if current_book:
                nodes=[{"name": char['title'], "occurrences": current_book['occurrences'][char['title']]} for char in current_book['characters']]
                links = get_links(current_book['occurrences'], characters=current_book['characters'], n=charwindow, extent=extent)
                return jsonify(nodes=nodes, links=links)
            else:
                return jsonify(status = 1)

    @app.route('/export', methods=['POST'])
    def export_book():
        if request.method == 'POST':
            data = request.json
            session_client_key = data['client_key']
            logging.info("Attempting to load book from cache")
            book = memcache_client.get(session_server_key+session_client_key)
            if book:
                logging.info("Loaded book %s from cache" % book["title"])
                current_book = book
            # else:
                # logging.info("Could not find book in the cache, loading from the database")
                # current_book = model.load_book_bykey(session_client_key)
            if current_book:
                current_book['title'] = data['title']
                memcache_client.set(session_server_key+session_client_key, current_book)
                book = {}
                for label in ['sentences', 'sentiments', 'characters', 'occurrences', 'title']:
                    book[label] = current_book[label]
                return jsonify(book)
            else:
                return jsonify(status = 1)

    @app.route('/savetodb', methods=['POST'])
    def sv2db():
        if request.method == 'POST':
            data = request.json
            session_client_key = data['client_key']
            logging.info("Attempting to load book from cache")
            current_book = memcache_client.get(session_server_key+session_client_key)
            if current_book:
                logging.info("Loaded book %s from cache" % current_book["title"])
                current_book['title'] = data['title']
                q = tasks.get_books_queue()
                r = q.enqueue(tasks.save_to_db, current_book, session_server_key, session_client_key)
                return jsonify(session_key = session_client_key)
            else:
                return jsonify(status=1)

    @app.route('/saveupdate', methods=['POST'])
    def svupd():
        if request.method == 'POST':
            session_client_key = request.json['client_key']
            logging.info('Getting book id from memcache')
            book_id_key = session_server_key[:10]+session_client_key
            book_id = memcache_client.get(book_id_key)
            book = memcache_client.get(session_server_key+session_client_key)
            if book_id:
                logging.info('Book id is: %d' % book_id)
                return jsonify(book_id=book_id, title = book['title'])
            else:
                return jsonify(status = 1)

    @app.route('/bad_extension')
    def extension_error():
        return "Only text files are allowed!"

    return app
