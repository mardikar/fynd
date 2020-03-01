from imdb.service import ImdbService, application


if __name__ == '__main__':
    ImdbService().start()
    application.run()
