import multiprocessing
from flask import Flask, jsonify, request, render_template
import json
from pathlib import Path

# local imports
import utils

app = Flask(__name__)
scheduler = None

local_path = Path(__file__).parent


class WebServer:
    def __init__(self, sched):
        global scheduler
        scheduler = sched

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
    return render_template("index.html", data={"config": utils.get_config()})


@app.route('/get/next/pass', methods=['GET'])
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


@app.route("/update/config", methods=["POST"])
def update_config():
    with open(local_path / "config.json", "w") as f:
        f.write(json.dumps(request.json, indent=4, sort_keys=True))
    return "Success", 200


@app.route("/get/config", methods=["GET"])
def get_config():
    with open(local_path / "config.json") as f:
        return jsonify(json.load(f))
