import os
from glob import glob
from dateutil import parser
from datetime import datetime, timedelta

wavs = sorted(glob("/home/pi/drive/weather/images/**/**/**.wav"), key=os.path.getmtime)[::-1]
for wav in wavs:
    try:
        print(parser.parse(wav.split("/")[-1].replace(".iq", "").replace(".wav", "").replace("_", " ").replace(".", ":")).strftime('%B %-d, %Y at %-H:%M:%S'))
        if parser.parse(wav.split("/")[-1].replace(".iq", "").replace(".wav", "").replace("_", " ").replace(".", ":")).timestamp() < (datetime.now() - timedelta(30)).timestamp():
            print("DELETE")
            os.remove(wav)
    except:
        pass
