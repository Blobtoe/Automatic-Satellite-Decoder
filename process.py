# Made by Felix (Blobtoe)

import sys
import json
import os
from datetime import datetime, timezone
import ephem
import piexif
import piexif.helper
from pathlib import Path

# local imports
import process_satellite
import share
from utils import log


def start(pass_info):
    local_path = Path(__file__).parent

    log(f"Started processing {pass_info['max_elevation']}° {pass_info['satellite']} pass at {datetime.fromtimestamp(pass_info['aos']).strftime('%B %-d, %Y at %-H:%M:%S')}")

    # load private info from secrets.json
    with open(local_path / "secrets.json") as f:
        data = json.load(f)
        lat = data["lat"]
        lon = data["lon"]
        elev = data["elev"]

    # get general info from pass json
    sat = pass_info["satellite"]
    sat_type = pass_info["type"]
    frequency = pass_info["frequency"]
    duration = pass_info["duration"]
    max_elevation = pass_info["max_elevation"]

    # string used for naming the files  (aos in %Y-%m-%d %H.%M.%S format)
    local_time = datetime.fromtimestamp(pass_info["aos"]).strftime("%Y-%m-%d_%H.%M.%S")
    # string used for naming the parent folder
    day = datetime.fromtimestamp(pass_info["aos"]).strftime("%Y-%m-%d")
    # the name of the folder where the output files will be created
    with open(local_path / "config.json") as f:
        data = json.load(f)
        output_folder = f"{data['output folder']}{day}/{local_time}"
    # the base name of the output files
    output_filename_base = f"{output_folder}/{local_time}"
    # the name of the json file containing all the info about the pass
    pass_file = f"{output_filename_base}.json"

    # create the output folder
    try:
        os.makedirs(output_folder)
    except:
        print("Failed creating new directories for the pass. Aborting")
        exit()

        # process APT
    if sat_type == "APT":
        images, main_tag = process_satellite.NOAA(pass_info, output_filename_base)
    # process LRPT
    elif sat_type == "LRPT":
        images, main_tag = process_satellite.METEOR(pass_info, output_filename_base)

    # upload each image to the internet
    links = {}
    for image in images:
        # add metadata to image
        exif_dict = piexif.load(image)
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(json.dumps(pass_info), encoding="unicode")
        piexif.insert(piexif.dump(exif_dict), image)

        # upload image and get a link
        tag = image.split(".")[-2]
        link = share.imgbb(image)
        if tag == main_tag:
            main_image = link
        links[tag] = link

    pass_info["links"] = links
    pass_info["main_image"] = main_image

    # write pass info to json file
    with open(pass_file, "w") as f:
        json.dump(pass_info, f, indent=4, sort_keys=True)

    # send discord webhook(s)
    share.discord_webhook(pass_info)

    # update the status in daily_passes.json
    '''
    with open("/home/pi/website/weather/scripts/scheduled_passes.json", "r+") as f:
        data = json.load(f)
        data[pass_index]["status"] = "PASSED"
        json.dump(data, f, indent=4, sort_keys=True)
    '''

    # append the pass to the passes list
    with open(f"{output_folder}/passes.json", "r+") as f:
        data = json.load(f)
        data.append(f"{output_filename_base}.json")
        json.dump(data, f, indent=4, sort_keys=True)

    # commit changes to git repository
    # print("STATUS {} - ".format(datetime.now().strftime("%Y/%m/%d %H:%M:%S")) +
    #      "Commiting changes to github")
    # os.system(
    #    "/home/pi/website/weather/scripts/commit.sh "Automatic commit for satellite pass" >> {}"
    #    .format(log_file))

    # send status to console
    log(f"Finished processing {max_elevation}° {sat} pass at {datetime.fromtimestamp(pass_info['aos']).strftime('%B %-d, %Y at %-H:%M:%S')}")

    # get info about next pass
    '''
    next_pass = {}
    for p in json.load(
            open(local_path / "scheduled_passes.json")):
        if p["status"] == "INCOMING":
            next_pass = p
            break
    if next_pass == {}:
        print("STATUS: {} - ".format(datetime.now().strftime(
            "%Y/%m/%d %H:%M:%S")) +
            "No more passes to process. Rescheduling...")
    else:
        print("STATUS: {} - ".format(datetime.now().strftime(
            "%Y/%m/%d %H:%M:%S")) +
            "Waiting until {} for {}° {} pass...".format(
            datetime.fromtimestamp(next_pass['aos']).strftime(
                "%B %-d, %Y at %-H:%M:%S"), next_pass['max_elevation'],
            next_pass['satellite']))
'''
