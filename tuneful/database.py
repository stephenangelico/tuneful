from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence, ForeignKey

from flask import url_for

from . import app

engine = create_engine(app.config["DATABASE_URI"])
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# Create your models here
class Song(Base):
	__tablename__ = "songs"
	
	id = Column(Integer, primary_key=True)
	file_id = Column(Integer, ForeignKey('files.id'))
	
	def as_dictionary(self):
		song = {
			"id": self.id,
			"file": {
				"id": self.file.id,
				"name": self.file.name
				}
			}
		return song

class File(Base):
	__tablename__ = "files"
	
	id = Column(Integer, primary_key=True)
	name = Column(String(128), nullable=False)
	songs = relationship("Song", backref="file")
	
	def as_dictionary(self):
		file = {
			"id": self.id,
			"name": self.name,
			"path": url_for("uploaded_file", filename=self.name)
			}
		return file

Base.metadata.create_all(engine)
