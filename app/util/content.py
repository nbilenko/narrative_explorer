import os
from collections import Counter
import nltk
import cPickle

class Content():
	'''Process file'''
	def __init__(self, filetext, basedir):
		try:
			nltk.data.find('tokenizers/punkt')
		except LookupError:
			nltk.download('punkt')

		try:
			nltk.data.find('chunkers/maxent_ne_chunker')
		except LookupError:
			nltk.download('maxent_ne_chunker')

		try:
			nltk.data.find('taggers/averaged_perceptron_tagger')
		except LookupError:
			nltk.download('averaged_perceptron_tagger')

		try:
			nltk.data.find('corpora/words')
		except LookupError:
			nltk.download('words')

		self.text = filetext
		self.basedir = basedir
		self.sentences = nltk.sent_tokenize(self.text)
		self.tokenized_sentences = [nltk.word_tokenize(sentence) for sentence in self.sentences]
		self.char_recognition()
		self.sentiment_analysis()

	def char_recognition(self, char_number = 20):
		tagged_sentences = nltk.pos_tag_sents(self.tokenized_sentences)
		self.entities = []
		entity_names = []
		if nltk.__version__[0] == '3':
			chunked_sentences = nltk.ne_chunk_sents(tagged_sentences, binary=False)
			for tree in chunked_sentences:
				entity_names.extend(extract_entity_names3(tree))
		else:
			chunked_sentences = nltk.batch_ne_chunk(tagged_sentences, binary=False)
			for tree in chunked_sentences:
				entity_names.extend(extract_entity_names(tree))
		count = Counter([name for name in entity_names])
		for c in count.most_common(char_number):
			self.entities.append(c[0])

	def fast_char_recognition(self, char_number = 30):
		self.entities = []
		entity_names = []
		stopwords = ['I', 'You', 'We', 'It', 'They', 'He', 'She', 'The', 'A', 'Where', 'When', 'What', 'Why', 'Who', 'There', 'Here', 'This', 'That', 'Mr.', 'Ms.', 'Mrs.', 'And', 'But', 'North', 'South', 'East', 'West', 'Yes', 'No']
		for sent in self.tokenized_sentences:
			for word in sent[1:]:
				if word.istitle() and word not in stopwords:
					entity_names.append(word)
		count = Counter([name for name in entity_names])
		for c in count.most_common(char_number):
			self.entities.append(c[0])

	def sentiment_analysis(self):
		classifier = cPickle.load(open(os.path.join(self.basedir, 'classifiers/classifier.pkl'), 'rb'))
		def word_feats(words):
			return dict([(word, True) for word in words])
		probs = classifier.prob_classify_many([word_feats(s) for s in self.tokenized_sentences])
		self.sentiment = [2.*(i.prob('pos')-0.5) for i in probs]

def extract_entity_names(t):
	entity_names = []
	if hasattr(t, 'node') and t.node:
		if t.node == 'PERSON':
			entity_names.append(' '.join([child[0] for child in t]))
		else:
			for child in t:
				entity_names.extend(extract_entity_names(child))
	return entity_names

def extract_entity_names3(t):
	entity_names = []
	if hasattr(t, 'label') and t.label:
		if t.label() == 'PERSON':
			entity_names.append(' '.join([child[0] for child in t]))
		else:
			for child in t:
				entity_names.extend(extract_entity_names3(child))
	return entity_names
