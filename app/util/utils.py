import numpy as np
import json

def parse_characters(hierarchy):
	characters = []
	for char in hierarchy:
		d = dict(char)
		characters.append({'title': d["name"], 'names': [d["name"]]})
		if "children" in d.keys():
			for child in d["children"]:
				characters[-1]["names"].append(child["name"])
	return characters

def get_occurrences(character, sentences):
	occurrences = [1*any((True for charname in character["names"] if charname in sent)) for sent in sentences]
	return occurrences

def get_links(occurrences, characters, n=2, extent = [0, None]):
	links = []
	if extent[1]>len(occurrences[characters[0]['title']]):
		extent[1] = None
	if n>len(occurrences[characters[0]['title']]):
		n=len(occurrences[characters[0]['title']])
	occurrences_arr = np.array([occurrences[char['title']] for char in characters]).T[extent[0]:extent[1]]
	cooccurrences = np.array([np.dot(rollw(occurrences_arr, i).T, occurrences_arr) for i in range(-n, n+1)]).sum(0)
	for ii in range(len(characters)):
		for jj in range(len(characters)):
			if jj>ii:
				links.append({"source":ii,"target":jj,"value":cooccurrences[ii, jj]})
	return links
		
def rollw(X, d):
	newX = np.zeros(X.shape)
	if d > 0:
		newX[:-d] = X[d:]
	elif d < 0:
		newX[-d:] = X[:d] 
	else:
		newX = X
	return newX