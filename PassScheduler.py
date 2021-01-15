import time
import sched
import multiprocessing
from pathlib import Path
from datetime import datetime
import json
import pause
import ephem
import predict

# local imports
from utils import log, download_tle, parse_tle
from _Pass import Pass


class PassScheduler:

    def __init__(self):
        '''Schedules passes for every satellite in the config file.'''
        local_path = Path(__file__).parent

        # get coordinates from secrets file
        with open(local_path / "secrets.json", "r") as f:
            data = json.load(f)
            lat = data["lat"]
            lon = data["lon"]
            elev = data["elev"]

        # get the satellites to be scheduled
        with open(local_path / "config.json", "r") as f:
            data = json.load(f)
            satellites = data["satellites"]
            min_elev = data["minimum elevation"]

        # get the tle file form celestrak
        log("Downloading TLE file")
        download_tle()

        # set the ground station location
        loc = (lat, lon * -1, elev)

        log("Calculating transits")
        passes = []
        # go over overy satellite specified
        for satellite in satellites:
            satellite = satellites[satellite]
            # go over every pass of the satellite
            for p in predict.transits(parse_tle("active.tle", satellite["name"]), loc, time.time() + 900, time.time() + (3600 * 24)):
                # if their peak elevation is higher than 20 degrees, add them to the list of passes
                if p.peak()["elevation"] >= min_elev:
                    passes.append(p)

        # sort the passes by their date (ascending order)
        passes.sort(key=lambda x: x.start)

        # start ephem for sun elevation predictions
        obs = ephem.Observer()
        obs.lat = str(lat)
        obs.long = str(lon)

        # turn the info into json data
        data = []
        for p in passes:
            satellite_name = p.peak()["name"].strip()
            satellite_info = satellites[satellite_name]

            # compute the sun elevation at peak elevation
            obs.date = datetime.utcfromtimestamp(round(p.peak()["epoch"]))
            sun = ephem.Sun(obs)
            sun.compute(obs)
            sun_elev = round(float(sun.alt) * 57.2957795, 1)  # convert from radians to degrees

            data.append({
                # ALL TIMES ARE IN SECONDS SINCE EPOCH (UTC)

                # name of the sat
                "satellite": satellite_name,
                # the frequency in MHz the satellite transmits
                "frequency": satellite_info["frequency"],
                # time the sat rises above the horizon
                "aos": round(p.start),
                # time the sat reaches its max elevation
                "tca": round(p.peak()["epoch"]),
                # time the sat passes below the horizon
                "los": round(p.end),
                # maximum degrees of elevation
                "max_elevation": round(p.peak()["elevation"], 1),
                # duration of the pass in seconds
                "duration":  round(p.duration()),
                # status INCOMING, CURRENT, COMPLETED or FAILED
                "status": "INCOMING",
                # type of satellite
                "type": satellite_info["type"],
                # azimuth at the aos
                "azimuth_aos": round(p.at(p.start)["azimuth"], 1),
                # azimuth at the los
                "azimuth_los": round(p.at(p.end)["azimuth"], 1),
                # either northbound or southbound
                "direction": "northbound" if 90 < p.at(p.start)["azimuth"] > 270 else "southbound",
                # the priority of the satellite
                "priority": satellite_info["priority"],
                # the elevation of the sun at the peak elevation
                "sun_elev": sun_elev
            })

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
        log("Writing pass information to scheduled_passes.json")
        json.dump(data, open(local_path / "scheduled_passes.json", "w"), indent=4, sort_keys=True)

        # convert json data to pass object
        self.passes = []
        for p in data:
            self.passes.append(Pass(p))

    def start(self):
        '''Starts processing the passes in a new process'''
        self.process = multiprocessing.Process(target=self.run_process, args=())

    def run_process(self):
        '''target function for parallel process'''
        for p in self.passes:
            log(f"Waiting until {datetime.fromtimestamp(p.aos).strftime('%B %-d, %Y at %-H:%M:%S')} for {p.max_elevation}° {p.satellite_name} pass...")
            pause.until(p.aos)
            p.process()

    def stop(self):
        '''Stops the scheduler. If a pass is in progress, it will stop after completion of the pass.'''
        self.process.terminate()
