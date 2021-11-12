# Made by Felix (Blobtoe)

import os
from PIL import Image
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path

# local imports
from utils import log

local_path = Path(__file__).parent


def METEOR(_pass, output_filename_base, scheduler):
    '''records, demodulates, and decodes METEOR-M 2 given the Pass object for the pass and the output file name, then returns the image's file path'''
    global local_path

    #set the status
    scheduler.status = {
        "status": "recording",
        "pass": _pass.info
    }

    # record pass baseband with rtl_fm
    print("recording pass...")
    os.system(f"timeout {_pass.duration} /usr/local/bin/rtl_fm -M raw -s 110k -f {_pass.frequency} -E dc -g 49.6 -p 0 - | sox -t raw -r 110k -c 2 -b 16 -e s - -t wav {output_filename_base}.iq.wav rate 192k")

    #os.system(f"screen -dmS meteor; screen -S meteor -X stuff '/usr/bin/meteor_demod -B -r 72000 -m qpsk -o {output_filename_base}.qpsk -s 110000 /tmp/meteor_iq \r'")
    #os.system(f"timeout {_pass.duration} /usr/local/bin/rtl_fm -M raw -s 110k -f {_pass.frequency} -E dc -g 49.6 -p 0 /tmp/meteor_iq; screen -X -S meteor quit")

    #set the status
    scheduler.status = {
        "status": "demodulating",
        "pass": _pass.info
    }

    # demodulate the signal
    print("demodulating meteor signal...")
    os.system(f"/usr/bin/meteor_demod -B -r 72000 -m qpsk -o {output_filename_base}.qpsk {output_filename_base}.iq.wav")

    if not os.path.exists(f"{output_filename_base}.qpsk"):
        log("Failed demodulation")
        return [], None

    #set the status
    scheduler.status = {
        "status": "decoding",
        "pass": _pass.info
    }

    output_directory = '/'.join(output_filename_base.split('/')[:-1])
    try:
        os.system(f"( cd /home/pi/satdump/build && ./satdump meteor_m2_lrpt soft {output_filename_base}.qpsk products {output_directory} -samplerate 192000 -baseband_format i16 )")
        
        for file in os.listdir(f"{output_directory}/MSU-MR/"):
            if file.endswith(("EQU.png", "5.png")):
                os.system(f"( cd /home/pi/satdump/build && ./satdump project 3000 3000 {output_filename_base}.{'-'.join(file.split('-')[2:])[:-4]}-proj.png stereo CN89ks 0.9 {output_directory}/MSU-MR/{file} {output_directory}/MSU-MR/{file[:-4]}.georef )")
            
            if file.endswith("CORRECTED.png"):
                os.rename(f"{output_directory}/MSU-MR/{file}", f"{output_filename_base}.{'-'.join(file.split('-')[2:])}")
    except Exception as e:
        print(e)

    # old code using medet_arm
    '''
    # decode the signal into an image
    print("decoding image...")
    #rgb122
    os.system(f"/usr/local/bin/medet_arm {output_filename_base}.qpsk {output_filename_base}.rgb122 -q -cd -r 65 -g 65 -b 64")
    #rgb555
    os.system(f"/usr/local/bin/medet_arm {output_filename_base}.rgb122.dec {output_filename_base}.ir -d -q -r 68 -g 68 -b 68")
    #rgb 123
    os.system(f"/usr/local/bin/medet_arm {output_filename_base}.rgb122.dec {output_filename_base}.rgb123 -d -q -r 66 -g 65 -b 64")

    # convert bmp to jpg
    for img in [f"{output_filename_base}.rgb122.bmp", f"{output_filename_base}.ir.bmp", f"{output_filename_base}.rgb123.bmp"]:
        # load bmp
        bmp = Image.open(img)
        # save as jpg
        bmp.save(".".join(img.split(".")[:-1]) + ".jpg")

    
    # get rid of the blue tint in the image (thanks to PotatoSalad for the code)
    #img = Image.open(outfile + ".jpg")
    #pix = img.load()
    #for y in range(img.size[1]):
    #    for x in range(img.size[0]):
    #        if pix[x, y][2] > 140 and pix[x, y][0] < pix[x, y][2]:
    #            pix[x, y] = (pix[x, y][2], pix[x, y][1], pix[x, y][2])
    #img.save(outfile + ".equalized.jpg")
    

    # rectify images
    os.system(f"/usr/local/bin/rectify-jpg {output_filename_base}.rgb122.jpg")
    os.system(f"/usr/local/bin/rectify-jpg {output_filename_base}.ir.jpg")
    os.system(f"/usr/local/bin/rectify-jpg {output_filename_base}.rgb123.jpg")

    # rename file
    os.rename(f"{output_filename_base}.rgb122-rectified.jpg", f"{output_filename_base}.rgb122.jpg")
    os.rename(f"{output_filename_base}.ir-rectified.jpg", f"{output_filename_base}.ir.jpg")
    os.rename(f"{output_filename_base}.rgb123-rectified.jpg", f"{output_filename_base}.rgb123.jpg")

    # rotate images if necessary
    for img in [f"{output_filename_base}.rgb122.jpg", f"{output_filename_base}.ir.jpg", f"{output_filename_base}.rgb123.jpg"]:
        if _pass.direction == "northbound":
            # load image
            jpg = Image.open(img)
            # rotate if necessary
            jpg.rotate(180, expand=True)
            # save as image
            jpg.save(img)
    '''

    # add precipitaion overlay to main image (should only be activated when ir is enabled)
    '''
    THRESHOLD = 25
    ir = cv2.imread(f"{output_filename_base}.ir.jpg", cv2.IMREAD_GRAYSCALE)
    image = cv2.imread(f"{output_filename_base}.{main_tag}.jpg")
    clut = cv2.imread(str(local_path / "clut.png"))

    _, mask = cv2.threshold(ir, THRESHOLD, 255, cv2.THRESH_BINARY_INV)
    image[np.where(mask == 255)] = [clut[0][int(value)] for value in ir[np.where(mask == 255)] * [255] / [THRESHOLD]]
    cv2.imwrite(f"{output_filename_base}.{main_tag}-precip.jpg", image)
    '''

    final_images = []
    main_tag = "RGB-221-EQU-proj"
    # convert png to jpg
    for file in os.listdir(output_directory):
        if file.endswith(("proj.png" , "CORRECTED.png")):
            # set IR as main tag if channel is available and sun is below threshold
            if file.endswith("5-proj.png") and _pass.sun_elev <= -10:
                main_tag = "5-proj"
            Image.open(f"{output_directory}/{file}").save(f"{output_directory}/{file[:-3]+'jpg'}")
            os.remove(f"{output_directory}/{file}")
            final_images.append(f"{output_directory}/{file[:-3]+'jpg'}")

    # return the image's file path
    return final_images, main_tag
    


def NOAA(_pass, output_filename_base, scheduler):
    '''records and decodes NOAA APT satellites given the Pass object for the pass and the output file name, then returns the images' file paths'''
    global local_path

    #set the status
    scheduler.status = {
        "status": "recording",
        "pass": _pass.info
    }

    # record the pass with rtl_fm
    print(f"writing to file: {output_filename_base}.wav")
    os.system(f"timeout {_pass.duration} /usr/local/bin/rtl_fm -d 0 -f {_pass.frequency} -g 49.6 -s 37000 -E deemp -F 9 - | sox -traw -esigned -c1 -b16 -r37000 - {output_filename_base}.wav rate 11025")

    #set the status
    scheduler.status = {
        "status": "decoding",
        "pass": _pass.info
    }

    # check if the wav file was properly created
    if os.path.isfile(f"{output_filename_base}.wav") == True and os.stat(f"{output_filename_base}.wav").st_size > 50:
        pass
    else:
        raise Exception("wav file was not created correctly. Aborting")

    # create map overlay
    print("creating map")
    date = (datetime.utcfromtimestamp(_pass.aos) + timedelta(0, 90)).strftime("%d %b %Y %H:%M:%S")
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


def SSTV(_pass, output_filename_base):
    global local_path

    print(f"writing to file: {output_filename_base}.iq.wav")
    os.system(f"timeout {_pass.duration} /usr/local/bin/rtl_fm -M raw -s 100k -f {_pass.frequency} -g 49.6  -s 37000 -E dc -p 0 - | sox -t raw -e s -c 2 -b 16 -r 100k - -t wav {output_filename_base}.iq.wav")
