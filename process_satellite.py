# Made by Felix (Blobtoe)

import os
import json
from PIL import Image
from datetime import datetime, timedelta
import cv2
import numpy as np
from pathlib import Path

# local imports
from utils import log


def METEOR(_pass, output_filename_base):
    '''records, demodulates, and decodes METEOR-M 2 given the Pass object for the pass and the output file name, then returns the image's file path'''
    local_path = Path(__file__).parent

    # record pass baseband with rtl_fm
    print("recording pass...")
    os.system(f"timeout {_pass.duration} /usr/local/bin/rtl_fm -M raw -s 110k -f {_pass.frequency} -E dc -g 49.6 -p 0 - | sox -t raw -r 110k -c 2 -b 16 -e s - -t wav {output_filename_base}.iq.wav rate 192k")

    # demodulate the signal
    print("demodulating meteor signal...")
    os.system(f"/usr/bin/meteor_demod -B -r 72000 -m qpsk -o {output_filename_base}.qpsk {output_filename_base}.iq.wav")

    # decode the signal into an image
    print("decoding image...")
    os.system(f"/usr/local/bin/medet_arm {output_filename_base}.qpsk {output_filename_base}.rgb122 -q -cd -r 65 -g 65 -b 64")
    os.system(f"/usr/local/bin/medet_arm {output_filename_base}.rgb122.dec {output_filename_base}.ir -d -q -r 68 -g 68 -b 68")

    # convert bmp to jpg and rotate if nessesary
    for img in [f"{output_filename_base}.rgb122.bmp", f"{output_filename_base}.ir.bmp"]:
        # load bmp
        bmp = Image.open(img)
        # rotate if nessesary
        if _pass.direction == "southbound":
            bmp.rotate(180, expand=True)
        # save as jpg
        bmp.save(".".join(img.split(".")[:-1]) + ".jpg")

    '''
    # get rid of the blue tint in the image (thanks to PotatoSalad for the code)
    img = Image.open(outfile + ".jpg")
    pix = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            if pix[x, y][2] > 140 and pix[x, y][0] < pix[x, y][2]:
                pix[x, y] = (pix[x, y][2], pix[x, y][1], pix[x, y][2])
    img.save(outfile + ".equalized.jpg")
    '''

    # rectify images
    os.system(f"/usr/local/bin/rectify-jpg {output_filename_base}.rgb122.jpg")
    os.system(f"/usr/local/bin/rectify-jpg {output_filename_base}.ir.jpg")

    # rename file
    os.rename(f"{output_filename_base}.rgb122-rectified.jpg", f"{output_filename_base}.rgb122.jpg")
    os.rename(f"{output_filename_base}.ir-rectified.jpg", f"{output_filename_base}.ir.jpg")

    main_tag = "rgb122"
    if _pass.sun_elev <= 10:
        main_tag = "ir"

    # add precipitaion overlay to main image
    THRESHOLD = 25
    ir = cv2.imread(f"{output_filename_base}.ir.jpg", cv2.IMREAD_GRAYSCALE)
    image = cv2.imread(f"{output_filename_base}.{main_tag}.jpg")
    clut = cv2.imread(str(local_path / "clut.png"))

    _, mask = cv2.threshold(ir, THRESHOLD, 255, cv2.THRESH_BINARY_INV)
    image[np.where(mask == 255)] = [clut[0][int(value)] for value in ir[np.where(mask == 255)] * [255] / [THRESHOLD]]
    cv2.imwrite(f"{output_filename_base}.{main_tag}-precip.jpg", image)

    # return the image's file path
    return [
        f"{output_filename_base}.rgb122.jpg",
        f"{output_filename_base}.ir.jpg",
        f"{output_filename_base}.{main_tag}-precip.jpg"
    ], f"{main_tag}-precip"


def NOAA(_pass, output_filename_base):
    '''records and decodes NOAA APT satellites given the Pass object for the pass and the output file name, then returns the images' file paths'''
    local_path = Path(__file__).parent

    # record the pass with rtl_fm
    print(f"writing to file: {output_filename_base}.wav")
    os.system(f"timeout {_pass.duration} /usr/local/bin/rtl_fm -d 0 -f {_pass.frequency} -g 49.6 -s 37000 -E deemp -F 9 - | sox -traw -esigned -c1 -b16 -r37000 - {output_filename_base}.wav rate 11025")

    # check if the wav file was properly created
    if os.path.isfile(f"{output_filename_base}.wav") == True and os.stat(f"{output_filename_base}.wav").st_size > 10:
        pass
    else:
        raise Exception("wav file was not created correctly. Aborting")

    # create map overlay
    print("creating map")
    date = (datetime.utcfromtimestamp(_pass.aos)+timedelta(0, 90)).strftime("%d %b %Y %H:%M:%S")
    os.system(f"/usr/local/bin/wxmap -T \"{_pass.satellite_name}\" -H \"{local_path / 'active.tle'}\" -p 0 -l 0 -g 0 -o \"{date}\" \"{output_filename_base}-map.png\"")

    # create images
    os.system(f"/usr/local/bin/wxtoimg -m {output_filename_base}-map.png -A -i JPEG -a -e contrast {output_filename_base}.wav {output_filename_base}.a.jpg")
    os.system(f"/usr/local/bin/wxtoimg -m {output_filename_base}-map.png -A -i JPEG -b -e contrast {output_filename_base}.wav {output_filename_base}.b.jpg")
    os.system(f"/usr/local/bin/wxtoimg -m {output_filename_base}-map.png -A -i JPEG -e HVCT {output_filename_base}.wav {output_filename_base}.HVCT.jpg")
    os.system(f"/usr/local/bin/wxtoimg -m {output_filename_base}-map.png -A -i JPEG -e MSA {output_filename_base}.wav {output_filename_base}.MSA.jpg")
    os.system(f"/usr/local/bin/wxtoimg -m {output_filename_base}-map.png -A -i JPEG -e MSA-precip {output_filename_base}.wav {output_filename_base}.MSA-precip.jpg")
    os.system(f"/usr/local/bin/wxtoimg -m {output_filename_base}-map.png -A -i JPEG {output_filename_base}.wav {output_filename_base}.raw.jpg")

    # change the main image depending on the sun elevation
    if _pass.sun_elev <= 10:
        main_tag = "b"
    elif _pass.sun_elev <= 30 or _pass.max_elevation <= 30:
        main_tag = "HVCT"
    else:
        main_tag = "MSA-precip"

    # return the images' file paths
    return [
        f"{output_filename_base}.a.jpg",
        f"{output_filename_base}.b.jpg",
        f"{output_filename_base}.HVCT.jpg",
        f"{output_filename_base}.MSA.jpg",
        f"{output_filename_base}.MSA-precip.jpg",
        f"{output_filename_base}.raw.jpg"], main_tag
