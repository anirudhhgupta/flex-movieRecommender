from imdb import IMDb
from modelRecommendations import modelRecommendations
from sklearn.feature_extraction.text import TfidfVectorizer
import sklearn.metrics as metrics
import pandas as pd
import json
import re
import string 
import numpy as np
import mysql.connector
import pickle

RE_PUNCT = re.compile('([%s])+' % re.escape(string.punctuation), re.UNICODE)

def title(text):
    # Remove all punctuation and make all lowercase 
    return RE_PUNCT.sub(" ", text).lower().split()

class fineTuneRecommendations:

	# def populate():
	# 	conn = mysql.connector.connect(host='localhost',
	# 	                               database='flex',
	# 	                               user='root',
	# 	                               password='')
	# 	if conn.is_connected():
	# 	    print('Connected to MySQL database')
	# 	else:
	# 	    print("Error")
	# 	    exit()

	# 	mycursor = conn.cursor()

	# 	titles = {}
	# 	ids={}

	# 	# Load Model
	# 	# fname ='model/model'
	# 	fname = 'model/model2'
	# 	model = Doc2Vec.load(fname)
	# 	masterFile = 'db/finalMasterDatawithProdInfo.json'

	# 	with open('model/tfidf_matrix', 'rb') as tfidf_matrixFile:
	# 			tfidf_matrix = pickle.load(tfidf_matrixFile) 
	# 	with open('model/tfidf_indices', 'rb') as tfidf_indices:
	# 			indices = pickle.load(tfidf_indices)

	# 	with open(masterFile) as json_file: 
	# 	    data=json.load(json_file)
	# 	    for line in data:
	# 	    	titles[line['title']]= '_'.join(title(line['title'])+[str(line['year'])])
	# 	    	ids[str(int(line['id']))]= '_'.join(title(line['title'])+[str(line['year'])])  
	# 	    documents=pd.read_json(masterFile)
	# 	    documents=documents.astype({'id': int})
	# 	    documents=documents.astype({'id': str})
	# 	    documents.set_index('id',inplace=True)
	# 	    with open('model/documents', 'wb') as documents_File:
	# 	    	pickle.dump(documents, documents_File)
	# 	    with open('model/ids', 'wb') as ids_File:
	# 	    	pickle.dump(ids, ids_File)
	# 	    with open('model/titles', 'wb') as titles_File:
	# 	    	pickle.dump(titles, titles_File)
	    
	def recommendationEngine(movieInfo,titles,documents,ids,model,conn,k):

		# Helper Functions
		def flatNormaliseSimScores(modelRecommendations):
			maxScore = 0.1
			minScore = 10
			for movie in modelRecommendations:
				if float(movie[2]) > maxScore:
					maxScore = float(movie[2])
				if float(movie[2]) < minScore:
					minScore = float(movie[2])

			for movie in modelRecommendations:
				movie[2] = float(movie[2])/maxScore

			return modelRecommendations

		def minMaxNormaliseSimScores(modelRecommendations):
			maxScore = 0.1
			minScore = 10
			for movie in modelRecommendations:
				if float(movie[2]) > maxScore:
					maxScore = float(movie[2])
				if float(movie[2]) < minScore:
					minScore = float(movie[2])

			for movie in modelRecommendations:
				# movie[2] = float(movie[2])/maxScore
				movie[2] = (float(movie[2])-minScore) / (maxScore-minScore)
			return modelRecommendations

		def getCountrySimilarity(movieCountrySet, defaultCountrySet):

			if(len(movieCountrySet)==0):
				return 0

			z = list((set(movieCountrySet)-set(defaultCountrySet)))
			lengthofSubtractionSet = len(list((set(movieCountrySet)-set(z))))
			# print("Length of Subtraction Set = ", lengthofSubtractionSet)
			if(lengthofSubtractionSet==0):
				return 0
			elif (lengthofSubtractionSet==1 and len(movieCountrySet)==1):
				return 1
			elif (lengthofSubtractionSet==1):
				return 0.5
			elif(lengthofSubtractionSet>=2):
				return 1

		def getYearSimilarity(movie,movieInfo):
			yearDiff = abs(movie[4]-movieInfo[4])
			if(yearDiff>=40):
				return 0.2
			else:
				return 1-(yearDiff/50)

		def getGenreSimilarity(id1, id2):

			return metrics.pairwise.cosine_similarity(tfidf_matrix[indices[str(id1)]],tfidf_matrix[indices[str(id2)]])

		def getMaxGenSim(modelRecommendationResults, movieId):
			maxRes=0.01
			for movie in modelRecommendationResults:
				temp = getGenreSimilarity(movie[1],movieId)
				if (temp > maxRes):
					maxRes = temp
			return maxRes

		# Populate Variables
		mycursor = conn.cursor(buffered=True)
		with open('model/tfidf_matrix', 'rb') as tfidf_matrixFile:
				tfidf_matrix = pickle.load(tfidf_matrixFile) 
		with open('model/tfidf_indices', 'rb') as tfidf_indices:
				indices = pickle.load(tfidf_indices)

		movieTitle = str(movieInfo[1])
		mainMovieId = str(int(movieInfo[6]))
		# print("Movie Title = ", movieTitle, " (", movieInfo[4], ")")

		modelRecommendationResults = list(modelRecommendations.recommend(movieTitle, titles, model, documents,ids))
		modelRecommendationResults = np.array(modelRecommendationResults)
		

		defaultCountrySet = ['United States','India','Australia','United Kingdom']

		# Normalise Similarity scores By Dividing with max of Similarity Score
		modelRecommendationResults = flatNormaliseSimScores(modelRecommendationResults)
		maxGenSim = getMaxGenSim(modelRecommendationResults, mainMovieId)

		for movie in modelRecommendationResults:
			movieId = movie[1]
			# print(movieId)
			found=True
			movieData=[]
			try:
				query = "SELECT * from `data_country_info` where id=" + movieId
				mycursor.execute(query)
				movieData = mycursor.fetchone()
			except:
				# print("None Found")
				found=False
			
			if movieData is None or found is False:
				continue		

			countrySim = getCountrySimilarity(movieData[5].split(','), defaultCountrySet)
			yearSim = getYearSimilarity(movieData,movieInfo)
			# print("MG - ", movieData[0],"\t","MD - ", movieInfo[0], getGenreSimilarity(movieData[1],movieInfo[1]))
			# Normalise Genre Similarity Score
			genreSim = getGenreSimilarity(str(int(movieData[6])),mainMovieId)/maxGenSim

			movie[2] =  0.55 * float(movie[2]) + 0.45 * countrySim + 0.15 * yearSim + 0.4 * float(genreSim[0])

		modelRecommendationResults = minMaxNormaliseSimScores(modelRecommendationResults)

		# modelRecommendationResults.sort(key = lambda x:x[2]) # 0 - Title, 1 -Index, 2 - Sim Score
		modelRecommendationResults = modelRecommendationResults[modelRecommendationResults[:,2].argsort()]
		#Reverse Sorted Array
		modelRecommendationResults = modelRecommendationResults[::-1] 

		return modelRecommendationResults[0:k]




