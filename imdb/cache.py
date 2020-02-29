from imdb.setup import SqliteDb


class ImdbCache(object):

    def __init__(self):
        self.db = SqliteDb()
        self.__hits, self.__misses = 0, 0

    def get(self, movieNames=None, directorNames=None, genres=None, ratingRange=None, moviesAndDirectors=None):
        if genres:
            return self.db.getMoviesFromGenres(genres)
        return self.db.getMovies(movieNames=movieNames, directorNames=directorNames,\
                                 moviesAndDirectors=moviesAndDirectors, ratingRange=ratingRange)

    def add(self, data):
        self.db.add(data)

    def update(self, data):
        self.db.update(data)

    def delete(self, data):
        self.db.delete(data)

    def start(self):
        self.db.start()

    def stop(self):
        self.db.stop()
