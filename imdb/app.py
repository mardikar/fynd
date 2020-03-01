from imdb.service import ImdbService
import flask


application = flask.Flask(__name__)
ImdbService(application).start()