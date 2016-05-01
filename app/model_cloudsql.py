# from __future__ import absolute_import
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.schema import Column, ForeignKey
# from sqlalchemy.dialects.mysql import INTEGER, Float, Text
# from sqlalchemy.types import Integer, Float, UnicodeText
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask

db = SQLAlchemy()


def init_app(app):
    db.init_app(app)

# engine = create_engine('mysql+pymysql://pythonapp:f16842d7-7fd9-411e-bf8b-4ec35e3842a0@173.194.242.97/library?charset=utf8')
# db.session = scoped_session(sessionmaker())
# db.session.configure(bind=engine)
# Base = declarative_base()
# Base.query = db.session.query_property()


class BookInfo(db.Model):
    ''' Book id and path'''

    __tablename__ = 'book_info'

    __auditing_enabled__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.UnicodeText)
    select = db.Column(db.Integer)

class Sentence(db.Model):
    ''' All sentences in the book '''

    __tablename__ = 'sentence'

    __auditing_enabled__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, ForeignKey('book_info.id'), nullable=False, index=True)
    sentence = db.Column(db.UnicodeText)

class Sentiment(db.Model):
    ''' List of sentiments '''

    __tablename__ = 'sentiment'

    __auditing_enabled__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, ForeignKey('book_info.id'), nullable=False, index=True)
    sentence_id = db.Column(db.Integer, ForeignKey('sentence.id'))
    sentiment = db.Column(db.Float)

class Character(db.Model):
    ''' List of characters '''

    __tablename__ = 'character'

    __auditing_enabled__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, ForeignKey('book_info.id'), nullable=False, index=True)
    character = db.Column(db.UnicodeText) # This is the main character name that will appear in the visualization

    character_name = relationship("CharacterName", back_populates='character', cascade="all, delete, delete-orphan")
    record = relationship("CharacterRecord", back_populates='character', cascade="all, delete, delete-orphan")

class CharacterName(db.Model):
    ''' List of character names associated with characters,
    	should include the name from the Character table by default and any alternatives'''

    __tablename__ = 'character_name'

    __auditing_enabled__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, ForeignKey('book_info.id'), nullable=False, index=True)
    character_id = db.Column(db.Integer, ForeignKey('character.id'))
    character = relationship("Character", back_populates="character_name")
    character_name = db.Column(db.UnicodeText)

class CharacterRecord(db.Model):
    '''Each sentence id in which a character appears'''

    __tablename__ = 'character_record'

    __auditing_enabled__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, ForeignKey('book_info.id'), nullable=False, index=True)
    character_id = db.Column(db.Integer, ForeignKey('character.id'), nullable=False, index=True)
    character = relationship("Character", back_populates="record")
    sentence_id = db.Column(db.Integer, ForeignKey('sentence.id'), nullable=False, index=True)
    record = db.Column(db.Integer)

def commit_book(current_book, select = 0):
    new_book = BookInfo(title = current_book['title'], select = select)
    db.session.add(new_book)
    db.session.commit()
    book_id = new_book.id
    db.session.add_all([Sentence(book_id=book_id, sentence=sent) for sent in current_book['sentences']])
    db.session.commit()
    db.session.add_all([Sentiment(book_id=book_id, sentence_id=i+1, sentiment=float(current_book['sentiments'][i])) for i in range(len(current_book['sentiments']))])
    db.session.commit()
    for char in current_book['characters']:
        new_char = Character(book_id=book_id, character=char["title"])
        db.session.add(new_char)
        db.session.commit()
        char_id = new_char.id
        db.session.add_all([CharacterName(book_id=book_id, character_id=char_id, character_name=name) for name in char["names"]])
        db.session.add_all([CharacterRecord(book_id=book_id, character_id=char_id, sentence_id=i+1, record=current_book['occurrences'][char["title"]][i]) for i in range(len(current_book['occurrences'][char["title"]]))])
        db.session.commit()
    return book_id

def save_book(book_id, current_book):
    book = db.session.query(BookInfo).get(book_id)
    book.title = current_book['title']
    book.select = 1
    db.session.commit()

def load_book(book_id):
    current_book = {}
    book = db.session.query(BookInfo).get(book_id)
    current_book['title'] = book.title
    text_query = db.session.query(Sentence).filter(Sentence.book_id == book_id).order_by(Sentence.id)
    current_book['sentences'] = [s.sentence for s in text_query]
    sent_query = db.session.query(Sentiment).filter(Sentiment.book_id == book_id).order_by(Sentiment.sentence_id)
    current_book['sentiments'] = [np.float64(s.sentiment) for s in sent_query]
    characters = []
    occurrences = {}
    char_query = db.session.query(Character).filter(Character.book_id == book_id).order_by(Character.id)
    name_query = db.session.query(CharacterName).filter(CharacterName.book_id == book_id)
    occ_query = db.session.query(CharacterRecord).filter(CharacterRecord.book_id == book_id)
    for char in char_query:
        nq = name_query.filter(CharacterName.character_id == char.id)
        oq = occ_query.filter(CharacterRecord.character_id == char.id).order_by(CharacterRecord.sentence_id)
        characters.append({"title": char.character, "names": [c.character_name for c in nq]})
        occurrences[char.character] = [o.record for o in oq]
    current_book["characters"] = characters
    current_book["occurrences"] = occurrences
    return current_book

def update_chars(book_id, characters, occurrences):
    old_characters = []
    old_occurrences = {}
    char_query = db.session.query(Character).filter(Character.book_id == book_id)
    name_query = db.session.query(CharacterName).filter(CharacterName.book_id == book_id)
    occ_query = db.session.query(CharacterRecord).filter(CharacterRecord.book_id == book_id)
    for char in char_query:
        nq = name_query.filter(CharacterName.character_id == char.id)
        old_characters.append({"title": char.character, "names": [c.character_name for c in nq]})
    create_list = []
    remove_list = old_characters
    for char in characters:
        if char in old_characters:
            remove_list.remove(char)
        else:
            create_list.append(char)

    for char in remove_list:
        cq = char_query.filter(Character.character == char['title'])
        print cq
        occ_query.filter(CharacterRecord.character_id == cq.one().id).delete()
        name_query.filter(CharacterName.character_id == cq.one().id).delete()
        cq.delete()
        db.session.commit()

    for char in create_list:
        new_char = Character(book_id=book_id, character=char["title"])
        db.session.add(new_char)
        db.session.commit()
        char_id = new_char.id
        db.session.add_all([CharacterName(book_id=book_id, character_id=char_id, character_name=name) for name in char["names"]])
        db.session.add_all([CharacterRecord(book_id=book_id, character_id=char_id, sentence_id=i+1, record=occurrences[char["title"]][i]) for i in range(len(occurrences[char["title"]]))])
        db.session.commit()

def load_selected():
    book_query = db.session.query(BookInfo).filter(BookInfo.select == 1).filter(BookInfo.title != None)
    return [{'id': b.id, 'title': b.title} for b in book_query]

def _create_database():
    """
    If this script is run directly, create all the tables necessary to run the
    application.
    """
    app = Flask(__name__)
    app.config.from_pyfile('../config.py')
    init_app(app)
    with app.app_context():
        db.create_all()
    print("All tables created")

if __name__ == '__main__':
    _create_database()
