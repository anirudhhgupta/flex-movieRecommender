import mysql.connector
import pickle
import json
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from fineTuneRecommendations import fineTuneRecommendations as recommender
from flask import Flask, request, render_template, flash, redirect, url_for, session, logging
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
api = Api(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
# db = SQLAlchemy(app)

# class user(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80))
#     password = db.Column(db.String(80))

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

# @app.route("/")
# def index():
#     return render_template("index.html")


# @app.route("/search")
# def searcha():
#     return render_template("search.html")

class search(Resource):
	def get(self,name):
		searchString = name
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

		def dbId(movieId):
			length = len(str(movieId))
			i=0
			temp=""
			for i in range(7-length):
				temp=temp+"0"
			movieId=temp+movieId
			return movieId

		def getDetails(movieRecommendations, conn, mycursor):
			movieData = []
			for movie in movieRecommendations:
				movieId = dbId(movie[1])
				query = "SELECT * FROM `data_country_info` WHERE id="+str(movieId)
				mycursor.execute(query)
				searchResult = mycursor.fetchone()
				data = {'title': searchResult[1], 'year': searchResult[4],'imdbId' : 'tt'+searchResult[6]}
				movieData.append(data)
			return movieData

		def searchMovies(searchString, conn, mycursor):
			query = "SELECT * FROM `data_country_info` WHERE title LIKE '%"+searchString+"%' ORDER BY `avgRating` DESC LIMIT 5;"
			mycursor.execute(query)
			searchResult = mycursor.fetchall()
			return searchResult

		movieList = searchMovies(searchString, conn, mycursor)
		if(len(movieList)==0):
			return {'found':False,'error':'No Movie Found in Database matching with - '+searchString, 'movies':'', 'recommendations':''}

		movieData = []
		i=0
		for movie in movieList:
			data = {'id': i, 'title' : movie[1], 'year': movie[4]}
			movieData.append(data)
			i=i+1

		# movieData = json.dumps(movieData)

		i=0
		recommenderData = []
		for movieInfo in movieList:
			movieRecommendations = recommender.recommendationEngine(movieInfo,titles,documents,ids,model,conn,k=5)
			result = movieData[i]
			movieRecommendations = getDetails(movieRecommendations, conn, mycursor)
			result['recommendations'] = movieRecommendations
			recommenderData.append(result)
			i=i+1
		print(recommenderData)

		resultData = {'found':True,'searchQuery':name,'noOfResults':len(movieList),'results':recommenderData}


		return resultData


api.add_resource(search,'/search/<name>')



if __name__ == '__main__':
	app.run(debug=True)
