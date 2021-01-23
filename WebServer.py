import multiprocessing
from flask import Flask, jsonify, request, render_template

# local imports
from start import scheduler
import utils

app = Flask(__name__)


class WebServer:
    def __init__(self):
        # create the background process
        self.process = multiprocessing.Process(target=app.run, kwargs=({"port": 5000, "host": "0.0.0.0"}))

        # create flask app
        self.app = Flask(__name__)

    def start(self):
        '''Starts the webserver in a new process'''
        self.process.start()

    def stop(self):
        '''Stops the webserver process'''
        # stop the process
        self.process.terminate()
        # re-create the background process
        self.process = multiprocessing.Process(target=app.run, kwargs=({"port": 5000, "host": "0.0.0.0"}))

###############
###ENDPOINTS###
###############


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route('/next/pass', methods=['GET'])
def next_pass():
    try:
        # read parameters
        after = int(request.args.get("after")) if request.args.get("after") != None else None
        pass_count = int(request.args.get("pass_count")) if request.args.get("pass_count") != None else None
        # return the json info of the requested passes
        return jsonify([p.info for p in scheduler.get_future_passes(after=after, pass_count=pass_count)])
    # if we run into an error, print the error and return code 400
    except Exception as e:
        utils.log(e)
        return str(e), 400
