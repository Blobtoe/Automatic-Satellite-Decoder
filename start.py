'''

run flask server and start the scheduler

'''
from flask import Flask, jsonify, request
import json
import os

# local imports
from PassScheduler import PassScheduler
import utils

app = Flask(__name__)
scheduler = PassScheduler()


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


if __name__ == "__main__":
    scheduler.start()
    app.run(port=5000, host="0.0.0.0")
