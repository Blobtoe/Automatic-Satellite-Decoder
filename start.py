'''

run flask server and start the scheduler

'''

import time

# local imports
from passscheduler import PassScheduler

scheduler = PassScheduler()
scheduler.start()
time.sleep(100000000000)
