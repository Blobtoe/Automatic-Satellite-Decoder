from datetime import datetime
import requests
from PIL import Image


def log(message):
    '''
    prints a message to the console with the date and time
    '''

    print(f"LOG: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')} - {str(message)}")


def download_tle():
    '''
    download the "active" tle file from celestrak
    '''

    # make the request to the website
    r = requests.get("https://www.celestrak.com/NORAD/elements/active.txt")
    # save the response to a file
    open("active.tle", "w+").write(r.text.replace("\r", ""))


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


def bmp_to_jpg(bmp_filename):
    '''
    converts a bmp to jpg
    '''

    # load bmp
    bmp = Image.open(bmp_filename)
    # save as jpg
    bmp.save("".join(bmp_filename.split(".")[:-1]) + ".jpg")
