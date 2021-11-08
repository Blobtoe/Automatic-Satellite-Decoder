'''

run flask server and start the scheduler

'''
from flask import Flask, jsonify, request
import json
import os

# local imports
from PassScheduler import PassScheduler
from WebServer import WebServer

scheduler = PassScheduler()
webserver = WebServer(scheduler)

scheduler.start()
webserver.start()

input()