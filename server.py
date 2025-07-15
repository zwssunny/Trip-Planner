from waitress import serve
from trips.wsgi import application
from config import conf, load_config


def main():
    load_config()
    sport = conf().get("port", 8000)
    serve(application, port=sport, threads=4, connection_limit=1000)


if __name__ == "__main__":
    main()
