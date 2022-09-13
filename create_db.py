import spacy
from spacy.lang.de.examples import sentences 
import pickle
import os.path

# create intital gender-noun mapping from seed
def initial_seeds():
	nouns = open("files/nouns.txt", "r")
	seed = {key: set() for key in ["Masc", "Fem", "Neut"]}

	for n in nouns:
	    article = n.split()[0]
	    noun = n.split()[1]
	    if article == "der":
	        seed["Masc"].add(noun.lower())
	    elif article == "die":
	        seed["Fem"].add(noun.lower())
	    else:
	        seed["Neut"].add(noun.lower())
	return seed

# create a pickle file that contains spacy object of every line in the corpus
def create_corpus():
	nlp = spacy.load("de_core_news_sm")
	text = []
	with open('files/train.txt') as train:
		text = [nlp(line) for line in train]

	with open('files/corpus.pkl', 'wb') as handle:
	    pickle.dump(text, handle)

def load_corpus():
	with open('files/corpus.pkl', 'rb') as handle:
		corpus = pickle.load(handle)
	# obj = open('files/corpus.pkl', 'rb')
	# corpus = pickle.load(obj)
	# obj.close()
	return corpus

def get_corpus():
	if os.path.exists("files/corpus.pkl"):
		corpus = load_corpus()
	else:
		create_corpus()
		corpus = load_corpus()
	return corpus

def rule_based_classification(corpus, seed):
	processed_nouns = 0
	correctly_categorised_nouns = 0
	for line in corpus:
	    for idx, token in enumerate(line):
	    	if token.pos_ == "NOUN":
	    		# get word preceeding current token
		    	article = (line[idx - 1]).text
		    	# # get case of current token
		    	# case = token.morph.get("Case")
		    	# get text of token
		    	text = token.text
		    	# get gold data for gender, to compare against the calculated gender
		    	spacy_gender = token.morph.get("Gender")
		    	gender = None

	    		# if article in ["der", "die", "das", "dem", "des", "den"]:
		    	# 	if article == "der":
		    	# 		if case == "Nom":
		    	# 			gender = "Masc"
		    	# 		elif case == "Dat" or case == "Gen":
		    	# 			gender = "Fem"
		    	# 	elif article == "die":
		    	# 		gender = "Fem"
		    	# 	elif article == "das":
		    	# 		gender = "Neut"
		    	# 	elif article == "dem" or article == "des":
		    	# 		gender = "Masc"
		    	# 	elif article == "den" and case == "Acc":
		    	# 		gender = "Masc"

		    	# german grammar rules for article/nouns

	    		if article == "das":
	    			gender = "Neut"
	    		elif article == "einem":
	    			gender = "Masc"
	    		elif article in ["eine", "einer"]:
	    			gender = "Fem"

		    	if gender:
		    		# add noun to seed if gender has been determined
		    		seed[gender].add(text)
		    		# # calculate accuracy statistics
		    		if spacy_gender:
		    			processed_nouns = processed_nouns + 1
		    			if gender == spacy_gender[0]:
		    				correctly_categorised_nouns = correctly_categorised_nouns + 1
		    	

	print(f'Total nouns where a gender was assigned and Spacy has the gender categorised is {processed_nouns}')
	print(f'Total number of nouns correctly labelled (considering spacy gender categorisation as gold data)is {correctly_categorised_nouns}. Hence, accuracy is {(correctly_categorised_nouns/processed_nouns)*100}')
	return seed


def create_suffix_bank(seed):
	suffixes_masc = {}
	suffixes_fem = {}
	suffixes_neut = {}

	# Masculine
	c = 0
	# loop through keys and create suffixes for each noun. only add suffixes of length less than or equal to 3
	for nouns in set(seed["Masc"]):
		suffixes = [nouns[i:] for i in range(len(nouns) - 3, len(nouns))]
		for s in suffixes:
			if s in suffixes_masc.keys():
				suffixes_masc[s] = suffixes_masc[s] + 1
			else:
				suffixes_masc[s] = 1

	# delete suffixes with frequency less than 3. Generate probability distribution for rest of the suffixes
	for key in list(suffixes_masc.keys()):
		if suffixes_masc[key] < 3:
			del suffixes_masc[key]
		else:
			c = c + suffixes_masc[key]

	for key, val in suffixes_masc.items():
		suffixes_masc[key] = suffixes_masc[key]/c

	# Feminine
	c = 0
	# loop through keys and create suffixes for each noun. only add suffixes of length less than or equal to 3
	for nouns in set(seed["Fem"]):
		suffixes = [nouns[i:] for i in range(len(nouns) - 3, len(nouns))]
		for s in suffixes:
			if s in suffixes_fem.keys():
				suffixes_fem[s] = suffixes_fem[s] + 1
			else:
				suffixes_fem[s] = 1

	# delete suffixes with frequency less than 3. Generate probability distribution for rest of the suffixes
	for key in list(suffixes_fem.keys()):
		if suffixes_fem[key] < 3:
			del suffixes_fem[key]
		else:
			c = c + suffixes_fem[key]

	for key, val in suffixes_fem.items():
		suffixes_fem[key] = suffixes_fem[key]/c

	# Neutral
	c = 0
	# loop through keys and create suffixes for each noun. only add suffixes of length less than or equal to 3
	for nouns in set(seed["Neut"]):
		suffixes = [nouns[i:] for i in range(len(nouns) - 3, len(nouns))]
		for s in suffixes:
			if s in suffixes_neut.keys():
				suffixes_neut[s] = suffixes_neut[s] + 1
			else:
				suffixes_neut[s] = 1

	# delete suffixes with frequency less than 3. Generate probability distribution for rest of the suffixes
	for key in list(suffixes_neut.keys()):
		if suffixes_neut[key] < 3:
			del suffixes_neut[key]
		else:
			c = c + suffixes_neut[key]

	for key, val in suffixes_neut.items():
		suffixes_neut[key] = suffixes_neut[key]/c


	return suffixes_masc, suffixes_fem, suffixes_neut

def morphology_based_classification(corpus, seed, suffixes_masc, suffixes_fem, suffixes_neut):
	# total number of nouns for which there was a calculated gender and a Spacy assigned gender
	processed_nouns = 0
	# nouns where calculated gender and Spacy assigned gender were the same
	correctly_categorised_nouns = 0
	# nouns where Spacy did not assign gender
	spacy_gender_not_exist = 0
	# total number of nouns in corpus
	total_nouns = 0
	for line in corpus:
	    for idx, token in enumerate(line):
	    	if token.pos_ == "NOUN":
	    		# get article for current token
	    		text = token.text
	    		# get gold data for gender, to compare against the calculated gender
	    		spacy_gender = token.morph.get("Gender")
	    		# total number of nouns in corpus
	    		total_nouns = total_nouns + 1
	    		# suffix array for current token calculated to give suffixes with length less than or equal to 3
	    		suffixes = [text[i:] for i in range(len(text) - 3, len(text))]

	    		# probability of word being neutral/masculine/feminine
		    	neut_p = 0.0
		    	masc_p = 0.0
		    	fem_p = 0.0

		    	for s in suffixes:
		    		if s in suffixes_neut.keys():
		    			neut_p = neut_p + suffixes_neut[s]

		    		if s in suffixes_masc.keys():
		    			masc_p = masc_p + suffixes_masc[s]

		    		if s in suffixes_fem.keys():
		    			fem_p = fem_p + suffixes_fem[s]

		    	# skip nouns where no suffixes were found
		    	if neut_p + masc_p + fem_p == 0:
		    		continue

		    	# normalisation
		    	masc_p = masc_p/(neut_p + masc_p + fem_p)
		    	fem_p = fem_p/(neut_p + masc_p + fem_p)
		    	neut_p = neut_p/(neut_p + masc_p + fem_p)


		    	# assign gender based on highest normalised value
		    	if neut_p > masc_p  and neut_p > fem_p:
		    		gender = "Neut"
		    	elif masc_p > neut_p and masc_p > fem_p:
		    		gender = "Masc"
		    	elif fem_p > neut_p and fem_p > masc_p:
		    		gender = "Fem"
		    	else:
		    		gender = "tbd"

		    	# check if gender was calculated and spacy assigned gender exists. if it does and the assigned gender is corrected compared
		    	# to the spacy assignmend, add it to the seed.
		    	if gender:
		    		# if gender has been assigned, add the noun to the seed
		    		if gender != "tbd":
		    			seed[gender].add(text)
		    		# calculate accuracy statistics
		    		if spacy_gender:
		    			processed_nouns = processed_nouns + 1
		    			if gender == spacy_gender[0]:
		    				correctly_categorised_nouns = correctly_categorised_nouns + 1
		    		
		    	elif len(spacy_gender) == 0:
		    		spacy_gender_not_exist = spacy_gender_not_exist + 1

	print(f'Total number of nouns(duplicates) in corpus is {total_nouns}')
	print(f'Total nouns where a gender was assigned and Spacy has the gender categorised is {processed_nouns}')
	print(f'Total number of nouns for which Spacy did not have gender assigned is {spacy_gender_not_exist}')
	print(f'Total number of nouns correctly labelled (considering spacy gender categorisation as gold data)is {correctly_categorised_nouns}. Hence, accuracy is {(correctly_categorised_nouns/processed_nouns)*100}')
	return seed

if __name__ == "__main__":
	seed = initial_seeds()
	print(f'''After Step 1: Number of masculine nouns is {len(seed["Masc"])}, feminine nouns is {len(seed["Fem"])} and neutral nouns is {len(seed["Neut"])}. 
		The total number of nouns in the seed is {len(seed["Masc"])+len(seed["Fem"])+len(seed["Neut"])}.''')
	corpus = get_corpus()

	# add nouns to seed based on rules around articles. 
	seed = rule_based_classification(corpus, seed)
	print(f'''After Step 2: Number of masculine nouns is {len(seed["Masc"])}, feminine nouns is {len(seed["Fem"])} and neutral nouns is {len(seed["Neut"])}. 
		The total number of nouns in the seed is {len(seed["Masc"])+len(seed["Fem"])+len(seed["Neut"])}.''')

	suffixes_masc, suffixes_fem, suffixes_neut = create_suffix_bank(seed)
	seed = morphology_based_classification(corpus, seed, suffixes_masc, suffixes_fem, suffixes_neut)

	print(f'''After Step 3: Number of masculine nouns is {len(seed["Masc"])}, feminine nouns is {len(seed["Fem"])} and neutral nouns is {len(seed["Neut"])}. 
		The total number of nouns in the seed is {len(seed["Masc"])+len(seed["Fem"])+len(seed["Neut"])}.''')


	# write seed to pickle file
	with open('files/seed.pkl', 'wb') as handle:
	    pickle.dump(seed, handle)

	# write suffix bank to pickle file
	with open('files/neutral_suffix.pkl', 'wb') as handle:
	    pickle.dump(suffixes_neut, handle)

	with open('files/masculine_suffix.pkl', 'wb') as handle:
	    pickle.dump(suffixes_masc, handle)	

	with open('files/feminine_suffix.pkl', 'wb') as handle:
	    pickle.dump(suffixes_fem, handle)	

