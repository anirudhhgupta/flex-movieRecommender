import mysql.connector
import pickle
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from fineTuneRecommendations import fineTuneRecommendations as recommender

def getMovieInfo(matchedMovies):
	i = 1
	for movie in matchedMovies:
		print(i,". - ", matchedMovies[i-1][1],"(",matchedMovies[i-1][4],")")
		i=i+1
	movieNo = int(input("Enter Movie Number : "))
	if(movieNo <= len(matchedMovies)):
		return matchedMovies[movieNo-1]
	else:
		print("Please Enter Valid No.")

def searchMovies(searchString, conn, mycursor):
	query = "SELECT * FROM `data_country_info` WHERE title LIKE '%"+searchString+"%' ORDER BY `avgRating` DESC LIMIT 5;"
	mycursor.execute(query)
	searchResult = mycursor.fetchall()
	return searchResult

def dbId(movieId):
	length = len(str(movieId))
	i=0
	temp=""
	for i in range(7-length):
		temp=temp+"0"
	movieId=temp+movieId
	return movieId

# Connect to DB
conn = mysql.connector.connect(host='localhost',
                               database='flex',
                               user='root',
                               password='')
if conn.is_connected():
    print('Connected to MySQL database')
else:
    print("Error")
    exit()

mycursor = conn.cursor(buffered=True)

# Load Model
fname = 'model/model2'
model = Doc2Vec.load(fname)

#Load Hash Maps and Document File
pickIn = open('model/titles','rb')
titles = pickle.load(pickIn)
pickIn = open('model/documents','rb')
documents = pickle.load(pickIn)
pickIn = open('model/ids','rb')
ids = pickle.load(pickIn)

# Input Function
searchString = input("Search for movie : ")
matchedMovies = searchMovies(searchString, conn, mycursor)
if(len(matchedMovies)==0):
	print("No Movie Found in DB.")
	exit()

movieInfo = getMovieInfo(matchedMovies)
print("Movie Info - ", movieInfo)
movieRecommendations = recommender.recommendationEngine(movieInfo,titles,documents,ids,model,conn,k=5)
print(movieRecommendations)