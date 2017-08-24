import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

from .database import Song, File
from . import decorators
from . import app
from .database import session
from .utils import upload_path

song_add_schema = {
	"properties": {
		"file": {
			"type": "object",
			"properties": {
				"id": {"type": "integer"}
			},
			"required": ["id"]
		}
	},
	"required": ["file"]
}

song_update_schema = {
	"properties": {
		"id": {"type": "integer"},
		"file": {
			"type": "object",
			"properties": {
				"id": {"type": "integer"}
			},
			"required": ["id"]
		}
	},
	"required": ["id", "file"]
}

@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def songs_get():
	""" Get a list of songs """
	
	# Get a list of songs from the database
	songs = session.query(Song)
	
	# Convert to JSON and return a response
	data = json.dumps([song.as_dictionary() for song in songs])
	return Response(data, 200, mimetype="application/json")

@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def songs_post():
	""" Add new song to database """
	
	data = request.json
	
	# Check that the JSON supplied is valid
	# If not you return a 422 Unprocessable Entity
	try:
		validate(data, song_add_schema)
	except ValidationError as error:
		data = {"message": error.message}
		return Response(json.dumps(data), 422, mimetype="application/json")
	
	# Add the post to the database
	song = Song(file_id=data["file"]["id"])
	session.add(song)
	session.commit()
	
	# Return list of songs as a dictionary
	songs = session.query(Song)
	data = json.dumps([song.as_dictionary() for song in songs])
	return Response(data, 201, mimetype="application/json")

@app.route("/api/songs", methods=["PUT"])
@decorators.accept("application/json")
@decorators.require("application/json")
def songs_update():
	""" Change a song's associated file """
	
	data = request.json
	
	# Check that the JSON supplied is valid
	# If not you return a 422 Unprocessable Entity
	try:
		validate(data, song_update_schema)
	except ValidationError as error:
		data = {"message": error.message}
		return Response(json.dumps(data), 422, mimetype="application/json")
	
	# Get the song from the database
	song = session.query(Song).get(data["id"])
	
	# Check whether the song exists
	# If not return a 404 with a helpful message
	if not song:
		message = "Could not find song with id {}".format(data["id"])
		data = json.dumps({"message": message})
		return Response(data, 404, mimetype="application/json")
		
	# Update the file reference in the database
	song.file_id = data["file"]["id"]
	session.commit()
	
	# Return acknowledgement of updation
	# Song list is retrieved by client automatically on update
	message = "Song #{} updated".format(data["id"])
	data = json.dumps({"message": message})
	return Response(data, 200, mimetype="application/json")

