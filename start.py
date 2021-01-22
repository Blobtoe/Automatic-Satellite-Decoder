'''

run flask server and start the scheduler

'''
from flask import Flask, jsonify, request
import json

# local imports
from PassScheduler import PassScheduler
import utils

app = Flask(__name__)
scheduler = PassScheduler()


@app.route('/next/pass', methods=['GET'])
def next_pass():
    try:
        if request.args.get("after") != None:
            return jsonify(scheduler.get_next_pass(int(request.args.get("after"))).info)
        else:
            return jsonify(scheduler.get_next_pass().info)
    except Exception as e:
        utils.log(e)
        return str(e), 400


if __name__ == "__main__":
    scheduler.start()
    app.run(port=5000, host="0.0.0.0")
