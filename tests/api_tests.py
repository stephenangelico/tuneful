import unittest
import os
import shutil
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Py2 compatibility
from io import StringIO

import sys; print(list(sys.modules.keys()))
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful.database import Song, File
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
	""" Tests for the tuneful API """
	
	def setUp(self):
		""" Test setup """
		self.client = app.test_client()
		
		# Set up the tables in the database
		Base.metadata.create_all(engine)
		
		# Create folder for test uploads
		os.mkdir(upload_path())

	def tearDown(self):
		""" Test teardown """
		session.close()
		# Remove the tables and their data from the database
		Base.metadata.drop_all(engine)
		
		# Delete test upload folder
		shutil.rmtree(upload_path())
	
	def test_get_empty_songs(self):
		""" Get songs from an empty database """
		response = self.client.get("/api/songs",
			headers=[("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.mimetype, "application/json")
		
		data = json.loads(response.data.decode("ascii"))
		self.assertEqual(data, [])
	
	def test_new_song(self):
		""" Add a song to the database """
		testfile = File(name="chords.wav")
		session.add(testfile)
		session.commit()
				
		data = {
			"file": {
				"id": 1
			}
		}
		
		response = self.client.post("/api/songs",
			data=json.dumps(data),
			content_type="application/json",
			headers=[("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.mimetype, "application/json")
		
		data = json.loads(response.data.decode("ascii"))
		self.assertEqual(data[0]["id"], 1)
		self.assertEqual(data[0]["file"]["id"], 1)
		self.assertEqual(data[0]["file"]["name"], "chords.wav")
	
	def test_invalid_song(self):
		""" Attempt to add a song without a name """
		data = {}
		
		response = self.client.post("/api/songs",
			data=json.dumps(data),
			content_type="application/json",
			headers=[("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 422)
		self.assertEqual(response.mimetype, "application/json")
		
		data = json.loads(response.data.decode("ascii"))
		self.assertEqual(data["message"], "'file' is a required property")
		
		data = {"file": {}}
		
		response = self.client.post("/api/songs",
			data=json.dumps(data),
			content_type="application/json",
			headers=[("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 422)
		self.assertEqual(response.mimetype, "application/json")
		
		data = json.loads(response.data.decode("ascii"))
		self.assertEqual(data["message"], "'id' is a required property")
	
	def test_update_song_name(self):
		""" Rename a song """
		testfile = File(name="chords.wav")
		testfile2 = File(name="blah.flac")
		newsong = Song(file_id=testfile.id)
		session.add_all([testfile, testfile2, newsong])
		session.commit()
		
		data = {
			"id": newsong.id,
			"file": {"id": testfile2.id}
		}
		
		response = self.client.put("/api/songs",
			data=json.dumps(data),
			content_type="application/json",
			headers=[("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.mimetype, "application/json")
		
		data = json.loads(response.data.decode("ascii"))
		self.assertEqual(data["message"], "Song #1 updated")
	
	def test_delete_song(self):
		""" Remove a song from the database """
		testfile = File(name="chords.wav")
		newsong = Song(file_id=testfile.id)
		session.add_all([testfile, newsong])
		session.commit()
		
		data = {"id": newsong.id}
		response = self.client.delete("/api/songs",
			data=json.dumps(data),
			content_type="application/json",
			headers=[("Accept", "application/json")]
		)
		
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.mimetype, "application/json")
		
		data = json.loads(response.data.decode("ascii"))
		self.assertEqual(data["message"], "Song #1 deleted")
	
	def test_test_get_uploaded_file(self):
		path = upload_path("test.txt")
		with open(path, "wb") as f:
			f.write(b"File contents")
		
		response = self.client.get("/uploads/test.txt")
		
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.mimetype, "text/plain")
		self.assertEqual(response.data, b"File contents")
