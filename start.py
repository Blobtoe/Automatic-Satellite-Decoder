# local imports
from PassScheduler import PassScheduler
from WebServer import WebServer

scheduler = PassScheduler()
webserver = WebServer(scheduler)

scheduler.start()
webserver.start()

input()