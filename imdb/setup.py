import sqlite3
import simplejson
import logging


def trimStrings(d):
    if isinstance(d, dict):
        for k, v in d.iteritems():
            d[k] = trimStrings(v)
    elif isinstance(d, (list, tuple)):
        return map(trimStrings, d)
    elif isinstance(d, basestring):
        return d.strip()
    return d


def listToString(li):
    return "'"+"','".join(li) + "'"


class SqliteDb(object):

    def __init__(self):
        self.__sqliteClient = None

    @staticmethod
    def joinMoviesAndDirectors(moviesAndDirectors):
        whereClause = " OR ".join(map(lambda t: "(movies.name == '%s' AND\
                     movies.director == '%s')" % (t[0], t[1]), moviesAndDirectors))
        return whereClause

    def getMovies(self, movieNames=None, directorNames=None, ratingRange=None, moviesAndDirectors=None):
        """

        :param moviesAndDirectors: list of tuples
        :param movieNames: list
        :param directorNames: list
        :param ratingRange: tuple
        :return: list of dicts
        """
        query = "select * from movies"
        whereClauses = []
        for colName, data in filter(lambda t: bool(t[1]), [("name", movieNames), ("director", directorNames)]):
            whereClauses.append("%s in (%s)" % (colName, listToString(data)))
        if ratingRange:
            whereClauses.append("imdb_score>= %s" % min(ratingRange))
            whereClauses.append("imdb_score>= %s" % max(ratingRange))
        if whereClauses:
            query += " where " + " AND ".join(whereClauses)
        if moviesAndDirectors:
            whereClause = self.joinMoviesAndDirectors(moviesAndDirectors)
            query = "select * from movies where %s" % whereClause
        response = []
        for row in self.__sqliteClient.execute(query):
            d = dict(zip(["name", "director", "imdb_score", "popularity"], row))
            genreQuery = "select genre from genres where genres.mname == '{name}'\
             and genres.director == '{director}'".format(**d)
            genres = list()
            for genre, in self.__sqliteClient.execute(genreQuery):
                genres.append(genre)
            d['genres'] = genres
            response.append(d)
        return response

    def getMoviesFromGenres(self, genres=None):
        query = "select mname, director from genres"
        if genres:
            genres = list(set(genres))
            query += " where genre in (%s)" % listToString(genres)
        moviesAndDirectors = list()
        for row in self.__sqliteClient.execute(query):
            moviesAndDirectors.append(row)
        return self.getMovies(moviesAndDirectors=moviesAndDirectors)

    def delete(self, moviesAndDirectors):
        cursor = self.__sqliteClient.cursor()
        moviesAndDirectors = [(d['name'], d['director']) for d in moviesAndDirectors]
        deleteQuery = "DELETE FROM movies where %s" % self.joinMoviesAndDirectors(moviesAndDirectors)
        cursor.execute(deleteQuery)
        self.__sqliteClient.commit()

    def update(self, moviesData):
        cursor = self.__sqliteClient.cursor()
        for movieData in moviesData:
            name, director = movieData['name'], movieData['director']
            if self.getMovies(moviesAndDirectors=[(name, director)]):
                updated = 'imdb_score = %s' % movieData['imdb_score']
                updateQuery = "UPDATE movies SET %s where name == '%s' and director == '%s'" % (updated, name, director)
                cursor.execute(updateQuery)
                genres = movieData['genres']
                for genre in genres:
                    cursor.execute("INSERT INTO genres VALUES('%s', '%s', '%s')" % (name, director, genre))
            else:
                self.__sqliteClient.rollback()
                raise Exception("%s doesn't exist! Can't update." % movieData)
        self.__sqliteClient.commit()

    def add(self, moviesData):
        cursor = self.__sqliteClient.cursor()
        for movieData in moviesData:
            name, director = movieData['name'], movieData['director']
            if not self.getMovies(moviesAndDirectors=[(name, director)]):
                t = "'%s', '%s', %s, %s" % (name, director, movieData['imdb_score'], movieData.get('popularity', 'null'))
                updateQuery = "INSERT INTO movies VALUES(%s)" % t
                cursor.execute(updateQuery)
                genres = movieData['genres']
                for genre in genres:
                    cursor.execute("INSERT INTO genres VALUES('%s', '%s', '%s')" % (name, director, genre))
            else:
                self.__sqliteClient.rollback()
                raise Exception("%s already exists! Can't create." % movieData)
        self.__sqliteClient.commit()

    def __createTables(self):
        cursor = self.__sqliteClient.cursor()
        createMoviesTableQuery = """CREATE TABLE movies 
        (name text,  director text, imdb_score real, popularity real, PRIMARY KEY(name, director))"""
        cursor.execute(createMoviesTableQuery)
        createGenreTableQuery = """CREATE TABLE genres
        (mname text, director text, genre text, PRIMARY KEY (mname, director, genre),\
         FOREIGN KEY (mname, director) REFERENCES movies(name, director))"""
        cursor.execute(createGenreTableQuery)
        self.__sqliteClient.commit()

    def __populateDb(self):
        cursor = self.__sqliteClient.cursor()
        moviesData = simplejson.load(open("./imdb_dataset.json"))
        for movieData in moviesData:
            movieData = trimStrings(movieData)
            insertMovieQuery = "INSERT INTO movies VALUES('{name}',\
             '{director}', {imdb_score}, {99popularity})".format(**movieData)
            cursor.execute(insertMovieQuery)
            for genre in movieData['genre']:
                insertGenreQuery = "INSERT INTO genres VALUES('{name}', '{director}',\
                 '{genre}')".format(name=movieData['name'], genre=genre, director=movieData['director'])
                cursor.execute(insertGenreQuery)
        self.__sqliteClient.commit()

    def start(self):
        self.__sqliteClient = sqlite3.connect(":memory:", check_same_thread=False)
        self.__createTables()
        self.__populateDb()

    def stop(self):
        self.__sqliteClient.close()
