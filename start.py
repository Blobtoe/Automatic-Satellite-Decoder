'''

run flask server and start the scheduler

'''

import schedule_passes
while True:
    schedule_passes.start(24)
