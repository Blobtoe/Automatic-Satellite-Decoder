from multiprocessing import Process, Pipe

# local imports
from PassScheduler import PassScheduler
from WebServer import WebServer

parent, child = Pipe()

scheduler = PassScheduler()
webserver = WebServer(scheduler)

scheduler_process = Process(target = scheduler.start())
webserver_process = Process(target = webserver.start())

scheduler_process.start()
webserver_process.start()

input()