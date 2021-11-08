from datetime import datetime
import json
import os
import piexif
import piexif.helper
from pathlib import Path

# local imports
import process_satellite
import share
import utils


class Pass:

    def __init__(self, pass_info):
        self.info = pass_info

        self.satellite_name = pass_info["satellite"]
        self.frequency = pass_info["frequency"]
        self.aos = pass_info["aos"]
        self.tca = pass_info["tca"]
        self.los = pass_info["los"]
        self.max_elevation = pass_info["max_elevation"]
        self.duration = pass_info["duration"]
        self.type = pass_info["type"]
        self.azimuth_aos = pass_info["azimuth_aos"]
        self.azimuth_los = pass_info["azimuth_los"]
        self.direction = pass_info["direction"]
        self.priority = pass_info["priority"]
        self.sun_elev = pass_info["sun_elev"]

    def process(self, scheduler):
        local_path = Path(__file__).parent

        utils.log(f"Started processing {self.max_elevation}° {self.satellite_name} pass at {datetime.fromtimestamp(self.aos).strftime('%B %-d, %Y at %-H:%M:%S')}")

        # string used for naming the files  (aos in %Y-%m-%d %H.%M.%S format)
        local_time = datetime.fromtimestamp(self.aos).strftime("%Y-%m-%d_%H.%M.%S")
        # string used for naming the parent folder
        day = datetime.fromtimestamp(self.aos).strftime("%Y-%m-%d")
        # the name of the folder where the output files will be created
        with open(local_path / "config.json") as f:
            data = json.load(f)
            output_folder = f"{data['output folder']}{day}/{local_time}"
        # the base name of the output files
        output_filename_base = f"{output_folder}/{local_time}"

        # create the output folder
        try:
            os.makedirs(output_folder)
        except:
            raise Exception("Failed creating new directories for the pass. Aborting")

        # process APT
        if self.type == "APT":
            images, main_tag = process_satellite.NOAA(self, output_filename_base, scheduler)
        # process LRPT
        elif self.type == "LRPT":
            images, main_tag = process_satellite.METEOR(self, output_filename_base, scheduler)
        elif self.type == "SSTV":
            process_satellite.SSTV(self, output_filename_base)

        # upload each image to the internet
        links = {}
        main_image = None
        for image in images:
            # add metadata to image
            exif_dict = piexif.load(image)
            exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(json.dumps(self.info), encoding="unicode")
            piexif.insert(piexif.dump(exif_dict), image)

            # upload image and get a link
            tag = image.split(".")[-2]
            link = share.imgbb(image)
            if tag == main_tag:
                main_image = link
            links[tag] = link

        self.links = links
        self.info["links"] = links
        self.main_image = main_image
        self.info["main_image"] = main_image

        # write pass info to json file
        with open(f"{output_filename_base}.json", "w") as f:
            json.dump(self.info, f, indent=4, sort_keys=True)

        # send discord webhook(s)
        share.discord_webhook(self.info)

        # send to home assistant webhook
        share.home_assistant(self.info, scheduler.get_future_passes()[0].info)

        #send to home server
        share.home_server(f"{output_filename_base}.json".split("/")[-1], self.info)

        # update the status in daily_passes.json
        '''
        with open("/home/pi/website/weather/scripts/scheduled_passes.json", "r+") as f:
            data = json.load(f)
            data[pass_index]["status"] = "PASSED"
            json.dump(data, f, indent=4, sort_keys=True)
        '''

        # append the pass to the passes list
        with open(f"{local_path}/passes.json", "r+") as f:
            data = json.load(f)
            data.append(f"{output_filename_base}.json")
            f.seek(0)
            json.dump(data, f, indent=4, sort_keys=True)

        # send status to console
        #scheduler.set_status(f"Finished processing {self.max_elevation}° {self.satellite_name} pass at {datetime.fromtimestamp(self.aos).strftime('%B %-d, %Y at %-H:%M:%S')}")
        utils.log(f"Finished processing {self.max_elevation}° {self.satellite_name} pass at {datetime.fromtimestamp(self.aos).strftime('%B %-d, %Y at %-H:%M:%S')}")
