import time
import sched
import multiprocessing
from pathlib import Path
from datetime import datetime
import json
import pause
import predict

# local imports
import utils
from _Pass import Pass


local_path = Path(__file__).parent


class PassScheduler:

    def __init__(self):
        # get coordinates from secrets file
        lat = utils.get_secrets()["lat"]
        lon = utils.get_secrets()["lon"]
        elev = utils.get_secrets()["elev"]
        # set the ground station location
        self.loc = (lat, lon * -1, elev)

        # get the satellites to be scheduled
        self.satellites = utils.get_config()["satellites"]

    def get_next_pass(self, after=time.time()):
        '''Returns a Pass object of the next scheduled pass.'''

        # download a new tle file
        utils.download_tle()

        utils.log("Calculating transits")
        predictors = {}
        # go over overy satellite specified
        for satellite in self.satellites:
            satellite = self.satellites[satellite]

            # store the specified minimum elevation and the transits iterator in a dict
            predictors[satellite["name"]] = {
                "minimum elevation": satellite["minimum elevation"],
                "transits": predict.transits(utils.parse_tle(local_path / "active.tle", satellite["name"]), self.loc, ending_after=after)
            }

        # get the first pass of every predictor
        first_passes = []
        for predictor in predictors:
            predictor = predictors[predictor]
            first_pass = next(predictor["transits"])
            while predictor["minimum elevation"] > first_pass.peak()["elevation"] and first_pass.start > after:
                first_pass = next(predictor["transits"])
            first_passes.append(utils.parse_pass_info(first_pass))
        # sort the passes by their start time
        first_passes.sort(key=lambda x: x["aos"])

        # go over the first passes
        i = 1
        while i < len(first_passes):
            p = first_passes[i]
            if first_passes[0]["los"] > p["aos"]:
                # calculate the priorities (max elevation + preset priority) (higher elevation passes have more priority)
                priority1 = first_passes[0]["max_elevation"] + first_passes[0]["priority"]
                priority2 = p["max_elevation"] + p["priority"]

                # keep the pass with highest priority
                if priority1 >= priority2:
                    # remove the overlapping pass from the list
                    first_passes.pop(i)
                    # calculate the next pass above the minimum elevation
                    next_pass = next(predictors[p["satellite"]]["transits"])
                    while predictors[p["satellite"]]["minimum elevation"] > next_pass.peak()["elevation"] and next_pass.start > after:
                        next_pass = next(predictors[p["satellite"]]["transits"])
                    # add the pass to the list
                    first_passes.append(utils.parse_pass_info(next_pass))

                elif priority2 > priority1:
                    # remove the overlapping pass from the list
                    first_passes.pop(0)
                    # calculate the next pass above the minimum elevation
                    next_pass = next(predictors[first_passes[0]["satellite"]]["transits"])
                    while predictors[first_passes[0]["satellite"]]["minimum elevation"] > next_pass.peak()["elevation"] and next_pass.start > after:
                        next_pass = next(predictors[first_passes[0]["satellite"]]["transits"])
                    # add the pass to the list
                    first_passes.append(utils.parse_pass_info(next_pass))

                # re-sort the list by their start time
                first_passes.sort(key=lambda x: x["aos"])
                # reset the counter
                i = 1

            else:
                i += 1

                # return the first pass in the list
        return Pass(first_passes[0])

    def start(self):
        '''Starts processing the passes in a new process.'''
        self.process = multiprocessing.Process(target=self._run_process, args=())
        self.process.start()

    def _run_process(self):
        '''target function for parallel process'''

        # loop forever (or until the process is terminated)
        while True:
            # get the next pass to process
            self.next_pass = self.get_next_pass()
            # wait until the pass starts
            utils.log(f"Waiting until {datetime.fromtimestamp(self.next_pass.aos).strftime('%B %-d, %Y at %-H:%M:%S')} for {self.next_pass.max_elevation}° {self.next_pass.satellite_name} pass...")
            pause.until(self.next_pass.aos)
            # start processing the pass
            self.next_pass.process()

    def stop(self):
        '''Stops the scheduler. If a pass is in progress, it will stop after completion of the pass.'''
        self.process.terminate()
