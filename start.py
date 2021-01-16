'''

run flask server and start the scheduler

'''

import time

# local imports
from PassScheduler import PassScheduler

scheduler = PassScheduler()
scheduler.start()
time.sleep(10000)
