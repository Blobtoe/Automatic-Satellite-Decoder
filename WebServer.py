import multiprocessing
from flask import Flask, jsonify, request, render_template
import json
from pathlib import Path
import traceback
from flask_cors import CORS
import requests

# local imports
import utils
import share

app = Flask(__name__)
CORS(app)
scheduler = None

local_path = Path(__file__).parent


class WebServer:
    def __init__(self, sched):
        global scheduler, app
        scheduler = sched

        # create the background process
        self.process = multiprocessing.Process(target=app.run, kwargs=({"port": 5000}))

        # create flask app
        self.app = app

    def start(self):
        '''Starts the webserver in a new process'''
        self.process.start()

    def stop(self):
        '''Stops the webserver process'''
        # stop the process
        self.process.terminate()
        # re-create the background process
        self.process = multiprocessing.Process(target=app.run, kwargs=({"port": 5000}))

###############
###ENDPOINTS###
###############


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", data={"config": utils.get_config()})


@app.route('/get/next/pass', methods=['GET', "OPTIONS"])
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


@app.route("/get/status", methods=["GET"])
def get_status():
    return jsonify(scheduler.get_status())


@app.route("/get/pass", methods=["GET"])
def get_pass():
    # read pass count parameter
    pass_count = int(request.args.get("pass_count")) if request.args.get("pass_count") != None else 1
    after = float(request.args.get("after")) if request.args.get("after") != None else None
    before = float(request.args.get("before")) if request.args.get("before") != None else None
    satellite_names = request.args.get("satellites").split(",")  if request.args.get("satellites") != None else None
    min_elevation = float(request.args.get("min_elevation")) if request.args.get("min_elevation") != None else None
    max_elevation = float(request.args.get("max_elevation")) if request.args.get("max_elevation") != None else None
    min_sun_elevation = float(request.args.get("min_sun_elevation")) if request.args.get("min_sun_elevation") != None else None
    max_sun_elevation = float(request.args.get("max_sun_elevation")) if request.args.get("max_sun_elevation") != None else None

    passes = scheduler.get_passes(pass_count=pass_count, after=after, before=before, satellite_names=satellite_names, min_elevation=min_elevation, max_elevation=max_elevation, min_sun_elevation=min_sun_elevation, max_sun_elevation=max_sun_elevation)

    return jsonify([p.info for p in passes])


@app.route("/request/home_assistant_latest_pass", methods=["GET"])
def request_home_assistant_latest_pass():
    share.home_assistant(scheduler.get_passes()[0].info, scheduler.get_future_passes()[0].info)
    return "Success", 200


@app.route("/request/home_assistant_next_pass", methods=["GET"])
def request_home_assistant_next_pass():
    utils.log("Sending next pass to home assistant")
    requests.post("http://192.168.1.101:8123/api/webhook/next_satellite_pass", json=scheduler.get_future_passes()[0].info)
    utils.log("done")
    return "Success", 200