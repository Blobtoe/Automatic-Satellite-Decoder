# Made by Felix (Blobtoe)

import json
import os
import time
import base64
from imgurpython import ImgurClient
from discord_webhook import DiscordWebhook, DiscordEmbed
import requests
from datetime import datetime
from pathlib import Path
import traceback

import utils

#######################################
# sends a message to a discord webhook given the json file for the pass and the webhook url
def discord_webhook(pass_info):
    local_path = Path(__file__).parent

    print("sharing to discord")

    # create the embed
    embed = DiscordEmbed(title=pass_info["satellite"], description="Pass over Vancouver, Canada", color=242424)
    embed.add_embed_field(name='Max Elevation', value=str(pass_info["max_elevation"]) + "°")
    embed.add_embed_field(name='Frequency', value=str(pass_info["frequency"]) + " Hz")
    embed.add_embed_field(name="Duration", value=str(round(pass_info["duration"])) + " seconds")
    embed.add_embed_field(name='Pass Start', value=datetime.utcfromtimestamp(pass_info["aos"]).strftime("%B %-d, %Y at %-H:%M:%S UTC"))
    embed.add_embed_field(name='Sun Elevation', value=str(pass_info["sun_elev"]) + "°")
    embed.set_image(url=pass_info["main_image"])

    # add all the image links
    links_string = ""
    for link in pass_info["links"]:
        links_string += "[{}]({}), ".format(link, pass_info["links"][link])
    embed.add_embed_field(name="Other Image Links", value=links_string)

    # send to every discord webhook we have
    with open(local_path / "secrets.json") as f:
        for webhook_url in json.load(f)["discord_webhook_urls"]:
            webhook = DiscordWebhook(url=webhook_url, username="Blobtoe's Kinda Crappy Images")
            webhook.add_embed(embed)
            webhook.execute()

    print("done")


#######################################
# uploads an image to imgur given the json file for the pass and the image's file path, then returns the link
def imgur(path, image):
    local_path = Path(__file__).parent
    print("sharing to imgur")

    # check if the file exists
    if os.path.isfile(image) == False:
        print("Error: Image does not exists.")
        return

    # create title for imgur post
    with open(path) as f:
        data = json.load(f)
        title = "{} at {}° at {}".format(data["satellite"],
                                         data["max_elevation"], data["aos"])

    # get imgur credentials from secrets.json
    with open(local_path / "secrets.json") as f:
        data = json.load(f)
        client_id = data["imgur_id"]
        client_secret = data["imgur_secret"]

    client = ImgurClient(client_id, client_secret)
    config = {'name': title, 'title': title}

    # try 10 times to upload image
    count = 0
    while True:
        try:
            img = client.upload_from_path(image, config=config)
            link = img["link"]
            print("done")
            return link
        except Exception as e:
            count += 1
            print("failed to upload image... trying again  {}/10".format(count))
            print(traceback.format_exc())
            time.sleep(2)

            if count >= 10:
                return None


#######################################
# uploads an image to imgbb.com given the image's file path, then return a link
def imgbb(image):
    local_path = Path(__file__).parent
    with open(image, "rb") as file:
        with open(local_path / "secrets.json") as s:
            payload = {
                "key": json.load(s)["imgbb_id"],
                "image": base64.b64encode(file.read()),
            }
        for i in range(1, 11):
            try:
                res = requests.post("https://api.imgbb.com/1/upload",
                                    payload,
                                    timeout=400,
                                    verify=False)
                data = json.loads(res.content)
                return data["data"]["url"]
            except Exception as e:
                print(f"failed to upload image... trying again  {i}/10")
                print(e)
                time.sleep(2)
        return None

#######################################
# sends the pass info to the home assistant webhook
def home_assistant(pass_info, next_pass_info):
    utils.log("Sharing to home assistant")
    requests.post("http://192.168.1.101:8123/api/webhook/latest_satellite_pass", json=pass_info)
    requests.post("http://192.168.1.101:8123/api/webhook/next_satellite_pass", json=next_pass_info)
    utils.log("done")

#######################################
# sends the pass info to the home server
def home_server(filename, pass_info):
    requests.post("http://192.168.1.101:5000/save_pass", json={"filename": filename, "data": pass_info})