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

    def schedule(self):
        '''Schedules passes for every satellite in the config file.'''

        # get the satellites to be scheduled
        satellites = utils.get_config()["satellites"]

        # get the tle file form celestrak
        utils.download_tle()

        utils.log("Calculating transits")
        passes = []
        # go over overy satellite specified
        for satellite in satellites:
            satellite = satellites[satellite]

            # set minimum elevation to schedule passes
            min_elev = utils.get_config()["satellites"][satellite]["minimum elevation"]

            # go over every pass of the satellite
            for p in predict.transits(utils.parse_tle(local_path / "active.tle", satellite["name"]), self.loc, time.time() + 900, time.time() + (3600 * 24)):
                # if their peak elevation is higher than the minimum elevation degrees, add them to the list of passes
                if p.peak()["elevation"] >= min_elev:
                    passes.append(p)

        # sort the passes by their start time
        passes.sort(key=lambda x: x.start)

        # turn the info into json data
        data = []
        for p in passes:
            data.append(utils.parse_pass_info(p))

        # check if passes overlap and choose which one to prioritize
        i = 0
        while i < len(data) - 2:
            if data[i]["los"] > data[i + 1]["aos"]:
                # calculate the priorities (max elevation + preset priority) (higher elevation passes have more priority)
                priority1 = data[i]["max_elevation"] + data[i]["priority"]
                priority2 = data[i + 1]["max_elevation"] + data[i + 1]["priority"]

                # keep the pass with highest priority
                if priority1 >= priority2:
                    data.pop(i + 1)
                elif priority2 > priority1:
                    data.pop(i)
            else:
                i += 1

        # write the passes to the json file
        utils.log("Writing pass information to scheduled_passes.json")
        json.dump(data, open(local_path / "scheduled_passes.json", "w"), indent=4, sort_keys=True)

        # convert json data to pass object
        self.passes = []
        for p in data:
            self.passes.append(Pass(p))

    def start(self):
        '''Starts processing the passes in a new process.'''
        self.process = multiprocessing.Process(target=self.run_process, args=())
        self.process.start()

    def get_next_pass(self):
        '''Returns information about the next scheduled pass.'''

        # get the satellites to be scheduled
        satellites = utils.get_config()["satellites"]

        utils.log("Calculating transits")
        predictors = {}
        # go over overy satellite specified
        for satellite in satellites:
            satellite = satellites[satellite]

            # store the specified minimum elevation and the transits iterator in a dict
            predictors[satellite["name"]] = {
                "minimum elevation": satellite["minimum elevation"],
                "transits": predict.transits(utils.parse_tle(local_path / "active.tle", satellite["name"]), self.loc)
            }

        # get the first pass of every predictor
        first_passes = []
        for predictor in predictors:
            predictor = predictors[predictor]
            first_pass = next(predictor["transits"])
            while predictor["minimum elevation"] > first_pass.peak()["elevation"] and first_pass.start > time.time():
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
                    while predictors[p["satellite"]]["minimum elevation"] > next_pass.peak()["elevation"] and next_pass.start > time.time():
                        next_pass = next(predictors[p["satellite"]]["transits"])
                    # add the pass to the list
                    first_passes.append(utils.parse_pass_info(next_pass))

                elif priority2 > priority1:
                    # remove the overlapping pass from the list
                    first_passes.pop(0)
                    # calculate the next pass above the minimum elevation
                    next_pass = next(predictors[first_passes[0]["satellite"]]["transits"])
                    while predictors[first_passes[0]["satellite"]]["minimum elevation"] > next_pass.peak()["elevation"] and next_pass.start > time.time():
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
        return first_passes[0]

    def run_process(self):
        '''target function for parallel process'''
        for p in self.passes:
            utils.log(f"Waiting until {datetime.fromtimestamp(p.aos).strftime('%B %-d, %Y at %-H:%M:%S')} for {p.max_elevation}° {p.satellite_name} pass...")
            pause.until(p.aos)
            p.process()

    def stop(self):
        '''Stops the scheduler. If a pass is in progress, it will stop after completion of the pass.'''
        self.process.terminate()
