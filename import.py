'''
This code assumes that a table named books is already created in given 
database .
'''
import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# engine = create_engine(os.getenv("postgresql://postgres:j@localhost:5432/postgres"))
# engine = create_engine("postgresql://prashantsingh:j@localhost:5432/postgres")
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def saveToBooksTable(fileName):
	file = open(fileName)
	csvReader = csv.reader(file, delimiter=",")
	i = 0
	for isbn, title, author, year in csvReader:
		if i > 0:
			db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",{"isbn": isbn, "title": title, "author": author, "year": year})
		i += 1
	db.commit()



saveToBooksTable("books.csv")