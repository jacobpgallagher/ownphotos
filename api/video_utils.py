import os
import ffmpeg
import re
import logging
import subprocess
import io
from dateutil.parser import parser as date_parser

logger = logging.getLogger(__name__)

def get_video_metadata(video_path):
    if not os.path.exists(video_path):
        raise FileNotFoundError

    meta = ffmpeg.probe(video_path)

    return meta

def extract_lat_lng_from_meta(meta):
    qt_string = meta.get('format', {}).get('tags', {}).get('com.apple.quicktime.location.ISO6709')
    if qt_string:
        m = re.match(r'(?P<lat>([\+-]?[0-9]+(\.[0-9]+)?))(?P<lng>([\+-]{1}[0-9]+(\.[0-9]+)?))(?P<alt>([\+-]{1}[0-9]+(\.[0-9]+)?)?)((CRS(?P<crs>.*)\/)?\/?)', qt_string)

        if m:
            return m.group('lat'), m.group('lng'), m.group('alt')
        else:
            logger.warning('Could not parse ISO6709 sring: %s', qt_string)

    return None, None, None

def extract_create_time_from_meta(meta):
    timestring = meta.get('format', {}).get('tags', {}).get('creation_time')
    if timestring:
        return date_parser().parse(timestring)

    return None

def extract_frame_from_video(video_path, output_file=None, timestamp_string=None):
    if timestamp_string is None:
        timestamp_string = '00.00.00.0'

    if output_file is not None:
        stdout = output_file
    else:
        stdout = io.BytesIO()


    proc = subprocess.Popen(['ffmpeg',
                             '-ss', '00:00:00.0',
                             '-i', video_path,
                             '-vframes', '1',
                             '-q:v', '2',
                             '-f', 'image2pipe',
                             '-'],
                            stdout=stdout)
    retcode = proc.wait(timeout=10)

    if retcode != 0:
        raise Exception('Non-zero exist code getting video thumbnail')

    stdout.seek(0)
    return stdout
