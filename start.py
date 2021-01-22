'''

run flask server and start the scheduler

'''
from flask import Flask, jsonify
import json

# local imports
from PassScheduler import PassScheduler

app = Flask(__name__)
scheduler = PassScheduler()


@app.route('/next/pass', methods=['GET'])
def home():
    return jsonify(scheduler.get_next_pass().info)


if __name__ == "__main__":
    scheduler.start()
    app.run(port=5000, host="0.0.0.0")
