'''

run flask server and start the scheduler

'''
from flask import Flask, request, abort, render_template

# local imports
from PassScheduler import PassScheduler

app = Flask(__name__)
scheduler = PassScheduler()


@app.route('/', methods=['GET'])
def home():
    return scheduler.passes


if __name__ == "__main__":
    scheduler.start()
    app.run(port=5000, host="0.0.0.0")
