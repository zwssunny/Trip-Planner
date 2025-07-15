from waitress import serve
from trips.wsgi import application

serve(application, listen='*:8000', threads=4, connection_limit=1000)