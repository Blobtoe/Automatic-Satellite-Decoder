from datetime import datetime
import requests
from PIL import Image
from pathlib import Path
import json
import ephem


local_path = Path(__file__).parent


def log(message):
    '''
    prints a message to the console with the date and time
    '''

    print(f"LOG: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')} - {str(message)}")


def download_tle():
    '''
    download the "active" tle file from celestrak
    '''

    log("Downloading TLE file")
    # make the request to the website
    r = requests.get("https://www.celestrak.com/NORAD/elements/active.txt")
    # save the response to a file
    open(local_path / "active.tle", "w+").write(r.text.replace("\r", ""))


def parse_tle(tle_file_name, satellite_name):
    '''
    returns the parsed tle lines from a tle file
    '''

    # pad the satellite name with spaces to make it 24 characters long
    satellite_name = satellite_name.ljust(24, " ")
    # read the lines of the tle file
    lines = open(tle_file_name, "r").read().splitlines()
    # get the index of the satellite's name
    index = lines.index(satellite_name)
    # return the 3 lines at the index
    return "\n".join(lines[index:index+3])


def get_config():
    '''returns the json data in the config file'''

    with open(local_path / "config.json") as f:
        return json.load(f)


def get_secrets():
    '''returns the json data in the secrets file'''

    with open(local_path / "secrets.json") as f:
        return json.load(f)


def parse_pass_info(p):
    '''creates a dict for a predicted transit'''

    satellite_name = p.peak()["name"].strip()
    satellite_config = get_config()["satellites"][satellite_name]

    # compute the sun elevation at peak elevation
    # start ephem for sun elevation predictions
    obs = ephem.Observer()
    obs.lat = str(get_secrets()["lat"])
    obs.long = str(get_secrets()["lon"])
    obs.date = datetime.utcfromtimestamp(round(p.peak()["epoch"]))
    sun = ephem.Sun(obs)
    sun.compute(obs)
    sun_elev = round(float(sun.alt) * 57.2957795, 1)  # convert from radians to degrees

    return {
        # ALL TIMES ARE IN SECONDS SINCE EPOCH (UTC)

        # name of the sat
        "satellite": satellite_name,
        # the frequency in MHz the satellite transmits
        "frequency": satellite_config["frequency"],
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
        "type": satellite_config["type"],
        # azimuth at the tca
        "azimuth_tca": round(p.peak()["azimuth"], 1),
        # azimuth at the aos
        "azimuth_aos": round(p.at(p.start)["azimuth"], 1),
        # azimuth at the los
        "azimuth_los": round(p.at(p.end)["azimuth"], 1),
        # either northbound or southbound
        "direction": "northbound" if 90 < p.at(p.start)["azimuth"] > 270 else "southbound",
        # the priority of the satellite
        "priority": satellite_config["priority"],
        # the elevation of the sun at the peak elevation
        "sun_elev": sun_elev
    }
