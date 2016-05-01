from __future__ import absolute_import
import numpy as np
from flask import Flask, request, redirect, url_for, send_from_directory, render_template, jsonify
from pymemcache.client.base import Client as MemcacheClient
import logging
from werkzeug.utils import secure_filename
import os
import json
# from app.util.content import Content
from app.util.utils import parse_characters, get_occurrences, get_links, json_serializer, json_deserializer
from . import model_cloudsql
from . import tasks

app = Flask(__name__)
app.config.from_object('config')
with app.app_context():
    model = model_cloudsql
    model.init_app(app)

memcache_addr = os.environ.get('MEMCACHE_PORT_11211_TCP_ADDR', 'localhost')
memcache_port = os.environ.get('MEMCACHE_PORT_11211_TCP_PORT', 11211)
memcache_client = MemcacheClient((memcache_addr, int(memcache_port)), serializer=json_serializer,
                deserializer=json_deserializer)


if not app.testing:
    logging.basicConfig(level=logging.INFO)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

def allowed_import(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ['JSON', 'json']

@app.route('/')
def index():
    books = model.load_selected()
    return render_template('index.html', books = books)

@app.route('/uploadajax', methods=['POST'])
def upldfile():
    if request.method == 'POST':
        file = request.files['file']
        q = tasks.get_books_queue()
        if file and allowed_file(file.filename):
            filetext = file.read().decode('utf-8')
            r = q.enqueue(tasks.process_book, filetext)
            # tasks.process_book(filetext)

            # content = Content(filetext, basedir = app.config['BASE_DIR'])
            # current_book = {}
            # current_book['sentences'] = [s for s in content.sentences]
            # current_book['sentiments'] = [s for s in content.sentiment]
            # current_book['characters'] = [{'title': content.entities[i], 'names': [content.entities[i]]} for i in range(len(content.entities))]
            # current_book['occurrences'] = {}
            # for char in current_book['characters']:
            #     current_book['occurrences'][char['title']] = get_occurrences(char, current_book['sentences'])
            # current_book['title'] = 'Click to edit title'
            # if len(current_book['characters']):
            #     current_book['links'] = get_links(current_book['occurrences'], characters=current_book['characters'], n=2, extent=[0,None])
            # else:
            #     current_book['links'] = {}
            # current_book['nodes']=[{"name": char['title'], "occurrences": current_book['occurrences'][char['title']]} for char in current_book['characters']]
        elif file and allowed_import(file.filename):
            data = json.loads(file.read())
            r = q.enqueue(tasks.process_json, data)
            # # Check the data
            # if not set(['sentences', 'sentiments', 'characters', 'occurrences', 'title']).issubset(set(data.keys())):
            #     return jsonify(error='Data format is incorrect')
            # else:
            #     current_book = data
            # current_book['nodes']=[{"name": char['title'], "occurrences": current_book['occurrences'][char['title']]} for char in current_book['characters']]
            # current_book['links'] = get_links(current_book['occurrences'], characters=current_book["characters"], n=2, extent=[0,None])
        else:
            return redirect('/bad_extension')
        current_book = r.result()
        memcache_client.set('current_book', current_book)
        book_id = model.commit_book(current_book, select = 0)
        current_book['book_id'] = book_id
        return jsonify(current_book)

@app.route('/charajax/<book_id>', methods=['POST'])
def char2viz(book_id):
    if request.method == 'POST':
        logging.info("Attempting to load book from cache")
        book = memcache_client.get('current_book')
        if book:
            logging.info("Loaded book %s from cache" % book["title"])
            current_book = book
        else:
            logging.info("Could not find book in the cache, loading from the database")
            current_book = model.load_book(book_id)
        data = request.json
        hierarchy = data['hierarchy']
        charwindow = int(data['charwindow'])/2
        extent = data['extent']
        new_characters = parse_characters(hierarchy)
        occurrences = {}
        for char in new_characters:
            occurrences[char['title']] = get_occurrences(char, current_book['sentences'])
        memcache_client.set("current_book", current_book) 
        model.update_chars(book_id, characters = new_characters, occurrences = occurrences)
        nodes=[{"name": char['title'], "occurrences": occurrences[char['title']]} for char in new_characters]
        if len(new_characters):
            links = get_links(occurrences, characters=new_characters, n=charwindow, extent=extent)
        else:
            links = {}
        return jsonify(nodes=nodes, links=links)

@app.route('/charlinks/<book_id>', methods=['POST'])
def charextent(book_id):
    if request.method == 'POST':
        data = request.json
        extent = data['extent']
        charwindow = int(data['charwindow'])/2
        logging.info("Attempting to load book from cache")
        book = memcache_client.get('current_book')
        if book:
            logging.info("Loaded book %s from cache" % book["title"])
            current_book = book
        else:
            logging.info("Could not find book in the cache, loading from the database")
            current_book = model.load_book(book_id)
            memcache_client.set('current_book', current_book)
        nodes=[{"name": char['title'], "occurrences": current_book['occurrences'][char['title']]} for char in current_book['characters']]
        links = get_links(current_book['occurrences'], characters=current_book['characters'], n=charwindow, extent=extent)
        return jsonify(nodes=nodes, links=links)

@app.route('/export/<book_id>', methods=['POST'])
def export_book(book_id):
    logging.info("Attempting to load book from cache")
    book = memcache_client.get('current_book')
    if book:
        logging.info("Loaded book %s from cache" % book["title"])
        current_book = book
    else:
        logging.info("Could not find book in the cache, loading from the database")
        current_book = model.load_book(book_id)
    current_book['title'] = request.json['title']
    memcache_client.set('current_book', current_book)
    return jsonify(current_book)

@app.route('/select_book/<book_id>', methods=['POST'])
def slct_book(book_id):
    current_book = model.load_book(book_id)
    current_book['book_id'] = book_id
    current_book["links"] = get_links(current_book['occurrences'], characters=current_book['characters'], n=2, extent=[0,None])
    current_book["nodes"] = [{"name": char['title'], "occurrences": current_book['occurrences'][char['title']]} for char in current_book['characters']]
    memcache_client.set('current_book', current_book)
    return jsonify(current_book)

@app.route('/savetodb/<book_id>', methods=['POST'])
def sv2db(book_id):
    logging.info("Attempting to load book from cache")
    book = memcache_client.get('current_book')
    if book:
        logging.info("Loaded book %s from cache" % book["title"])
        current_book = book
    else:
        logging.info("Could not find book in the cache, loading from the database")
        current_book = model.load_book(book_id)
    current_book['title'] = request.json['title']
    memcache_client.set('current_book', current_book)
    model.save_book(book_id, current_book)
    return jsonify(book_id=book_id)

@app.route('/bad_extension')
def extension_error():
    return "Only text files are allowed!"

