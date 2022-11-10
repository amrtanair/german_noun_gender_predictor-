import spacy
from spacy.lang.de.examples import sentences 
import pickle
import os.path
import requests
from typing import List, Set, Dict, Tuple, Optional, Any, Counter


def load_pickle_files() -> Any:
	with open('files/masculine_suffix.pkl', 'rb') as handle:
	    suffixes_masc = pickle.load(handle)

	with open('files/feminine_suffix.pkl', 'rb') as handle:
	    suffixes_fem = pickle.load(handle)

	with open('files/neutral_suffix.pkl', 'rb') as handle:
	    suffixes_neut = pickle.load(handle)

	return suffixes_masc, suffixes_fem, suffixes_neut

def calculate_gender(noun: str, suffixes_masc: Any, suffixes_fem: Any, suffixes_neut: Any) -> str:
	suffixes = [noun[i:] for i in range(len(noun) - 3, len(noun))]

	neut_p = 0.0
	masc_p = 0.0
	fem_p = 0.0

	neut_p = sum([suffixes_neut[key] for key in suffixes if key in suffixes_neut.keys()])
	masc_p = sum([suffixes_masc[key] for key in suffixes if key in suffixes_masc.keys()])
	fem_p = sum([suffixes_fem[key] for key in suffixes if key in suffixes_fem.keys()])
	total = neut_p + masc_p + fem_p

	# skip nouns where no suffixes were found
	if total == 0:
		print("Gender could not be determined")
		exit()

	# normalisation
	masc_p = masc_p/total
	fem_p = fem_p/total
	neut_p = neut_p/total

	# assign gender based on highest normalised value
	if neut_p > masc_p  and neut_p > fem_p:
		gender = "Neutral"
	elif masc_p > neut_p and masc_p > fem_p:
		gender = "Masculine"
	elif fem_p > neut_p and fem_p > masc_p:
		gender = "Feminine"
	else:
		gender = "tbd"

	return gender

if __name__ == "__main__":
	suffixes_masc, suffixes_fem, suffixes_neut = load_pickle_files()
	while True:
		noun = input("Enter noun:")
		gender = calculate_gender(noun, suffixes_masc, suffixes_fem, suffixes_neut)
		print(f'The calculated gender is {gender}')

	    # Using a German Gender API to fetch the gender of the noune
		response = (requests.get("https://german-gender-api.deta.dev/api/v1/nouns/" + noun)).json()

		if "gender" in response.keys():
			print(f'The gender assigned by the German Gender API is {response["gender"]}')
		else:
			print(response["detail"]["message"])
