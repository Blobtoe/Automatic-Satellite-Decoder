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

        # create the background process for processing passes
        self.process = multiprocessing.Process(target=self._run_process, args=())

        # download a new tle
        utils.download_tle()
        self.tle_updated_time = time.time()
        self.tle_update_frequency = utils.get_config()["tle update frequency"]

    def get_next_pass(self, after=time.time(), pass_count=1):
        '''Returns a Pass object of the next scheduled pass.'''

        # download a new tle file if needed
        if time.time() - self.tle_updated_time > self.tle_update_frequency * 3600:
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
            # get the first pass above the minimum elevation and that starts after the specified time
            first_pass = next(predictor["transits"])
            while predictor["minimum elevation"] > first_pass.peak()["elevation"] or first_pass.start < after:
                first_pass = next(predictor["transits"])
            # parse information from the pass and add it to the list
            first_passes.append(utils.parse_pass_info(first_pass))
        # sort the passes by their start time
        first_passes.sort(key=lambda x: x["aos"])

        passes = []
        # go over the first passes
        i = 1
        while i < len(first_passes) and len(passes) < pass_count:
            p = first_passes[i]
            if first_passes[0]["los"] > p["aos"]:
                # calculate the priorities (max elevation + preset priority) (higher elevation passes have more priority)
                priority1 = first_passes[0]["max_elevation"] + first_passes[0]["priority"]
                priority2 = p["max_elevation"] + p["priority"]

                # keep the pass with highest priority
                if priority1 >= priority2:
                    # calculate the next pass above the minimum elevation
                    next_pass = next(predictors[p["satellite"]]["transits"])
                    while predictors[p["satellite"]]["minimum elevation"] > next_pass.peak()["elevation"] or next_pass.start < after:
                        next_pass = next(predictors[p["satellite"]]["transits"])
                    # replace the pass in the list
                    first_passes[i] = utils.parse_pass_info(next_pass)

                elif priority2 > priority1:
                    # calculate the next pass above the minimum elevation
                    next_pass = next(predictors[first_passes[0]["satellite"]]["transits"])
                    while predictors[first_passes[0]["satellite"]]["minimum elevation"] > next_pass.peak()["elevation"] or next_pass.start < after:
                        next_pass = next(predictors[first_passes[0]["satellite"]]["transits"])
                    # replace the pass in the list
                    first_passes[0] = utils.parse_pass_info(next_pass)

                # re-sort the list by their start time
                first_passes.sort(key=lambda x: x["aos"])
                # reset the counter
                i = 1

            else:
                i += 1

            # if we gone through all the first_passes list (found a good pass)
            if i >= len(first_passes):
                # add the pass the final passes list
                passes.append(first_passes[0])
                # calculate the next pass above the minimum elevation
                next_pass = next(predictors[first_passes[0]["satellite"]]["transits"])
                while predictors[first_passes[0]["satellite"]]["minimum elevation"] > next_pass.peak()["elevation"] or next_pass.start < after:
                    next_pass = next(predictors[first_passes[0]["satellite"]]["transits"])
                # replace the pass in the list
                first_passes[0] = utils.parse_pass_info(next_pass)

                # re-sort the list by their start time
                first_passes.sort(key=lambda x: x["aos"])
                # reset the counter
                i = 1

        # return the first pass in the list
        return Pass(passes[0]) if len(passes) == 1 else [Pass(p) for p in passes]

    def start(self):
        '''Starts processing the passes in a new process.'''
        self.process.start()

    def _run_process(self):
        '''target function for parallel process'''

        next_pass = self.get_next_pass()

        # loop forever (or until the process is terminated)
        while True:
            # wait until the pass starts
            utils.log(f"Waiting until {datetime.fromtimestamp(next_pass.aos).strftime('%B %-d, %Y at %-H:%M:%S')} for {next_pass.max_elevation}° {next_pass.satellite_name} pass...")
            pause.until(next_pass.aos)
            # start processing the pass
            next_pass.process()
            # get the next pass to process
            next_pass = self.get_next_pass(after=next_pass.los)

    def stop(self):
        '''Stops the scheduler. If a pass is in progress, it will stop after completion of the pass.'''
        self.process.terminate()
