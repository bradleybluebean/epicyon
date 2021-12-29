__filename__ = "media.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.2.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Timeline"

import os
import time
import datetime
import subprocess
import random
from random import randint
from hashlib import sha1
from auth import create_password
from utils import get_base_content_from_post
from utils import get_full_domain
from utils import get_image_extensions
from utils import get_video_extensions
from utils import get_audio_extensions
from utils import get_media_extensions
from utils import has_object_dict
from utils import acct_dir
from shutil import copyfile
from shutil import rmtree
from shutil import move
from city import spoof_geolocation


def _get_blur_hash() -> str:
    """You may laugh, but this is a lot less computationally intensive,
    especially on large images, while still providing some visual variety
    in the timeline
    """
    hashes = [
        "UfGuaW01%gRi%MM{azofozo0V@xuozn#ofs.",
        "UFD]o8-;9FIU~qD%j[%M-;j[ofWB?bt7IURj",
        "UyO|v_1#im=s%y#U%OxDwRt3W9R-ogjHj[WX",
        "U96vAQt6H;WBt7ofWBa#MbWBo#j[byaze-oe",
        "UJKA.q01M|IV%LM|RjNGIVj[f6oLjrofaeof",
        "U9MPjn]?~Cxut~.PS1%1xXIo0fEer_$*^jxG",
        "UtLENXWCRjju~qayaeaz00j[ofayIVkCkCfQ",
        "UHGbeg-pbzWZ.ANI$wsQ$H-;E9W?0Nx]?FjE",
        "UcHU%#4n_ND%?bxatRWBIU%MazxtNaRjs:of",
        "ULR:TsWr~6xZofWWf6s-~6oK9eR,oes-WXNJ",
        "U77VQB-:MaMx%L%MogRkMwkCxuoIS*WYjEsl",
        "U%Nm{8R+%MxuE1t6WBNG-=RjoIt6~Vj]RkR*",
        "UCM7u;?boft7oft7ayj[~qt7WBoft7oft7Rj"
    ]
    return random.choice(hashes)


def _replace_silo_domain(post_json_object: {},
                         siloDomain: str, replacementDomain: str,
                         system_language: str) -> None:
    """Replace a silo domain with a replacement domain
    """
    if not replacementDomain:
        return
    if not has_object_dict(post_json_object):
        return
    if not post_json_object['object'].get('content'):
        return
    contentStr = get_base_content_from_post(post_json_object, system_language)
    if siloDomain not in contentStr:
        return
    contentStr = contentStr.replace(siloDomain, replacementDomain)
    post_json_object['object']['content'] = contentStr
    if post_json_object['object'].get('contentMap'):
        post_json_object['object']['contentMap'][system_language] = contentStr


def replace_you_tube(post_json_object: {}, replacementDomain: str,
                     system_language: str) -> None:
    """Replace YouTube with a replacement domain
    This denies Google some, but not all, tracking data
    """
    _replace_silo_domain(post_json_object, 'www.youtube.com',
                         replacementDomain, system_language)


def replace_twitter(post_json_object: {}, replacementDomain: str,
                    system_language: str) -> None:
    """Replace Twitter with a replacement domain
    This allows you to view twitter posts without having a twitter account
    """
    _replace_silo_domain(post_json_object, 'twitter.com',
                         replacementDomain, system_language)


def _remove_meta_data(image_filename: str, outputFilename: str) -> None:
    """Attempts to do this with pure python didn't work well,
    so better to use a dedicated tool if one is installed
    """
    copyfile(image_filename, outputFilename)
    if not os.path.isfile(outputFilename):
        print('ERROR: unable to remove metadata from ' + image_filename)
        return
    if os.path.isfile('/usr/bin/exiftool'):
        print('Removing metadata from ' + outputFilename + ' using exiftool')
        os.system('exiftool -all= ' + outputFilename)  # nosec
    elif os.path.isfile('/usr/bin/mogrify'):
        print('Removing metadata from ' + outputFilename + ' using mogrify')
        os.system('/usr/bin/mogrify -strip ' + outputFilename)  # nosec


def _spoof_meta_data(base_dir: str, nickname: str, domain: str,
                     outputFilename: str, spoofCity: str,
                     content_license_url: str) -> None:
    """Spoof image metadata using a decoy model for a given city
    """
    if not os.path.isfile(outputFilename):
        print('ERROR: unable to spoof metadata within ' + outputFilename)
        return

    # get the random seed used to generate a unique pattern for this account
    decoySeedFilename = acct_dir(base_dir, nickname, domain) + '/decoyseed'
    decoySeed = 63725
    if os.path.isfile(decoySeedFilename):
        with open(decoySeedFilename, 'r') as fp:
            decoySeed = int(fp.read())
    else:
        decoySeed = randint(10000, 10000000000000000)
        try:
            with open(decoySeedFilename, 'w+') as fp:
                fp.write(str(decoySeed))
        except OSError:
            print('EX: unable to write ' + decoySeedFilename)

    if os.path.isfile('/usr/bin/exiftool'):
        print('Spoofing metadata in ' + outputFilename + ' using exiftool')
        curr_timeAdjusted = \
            datetime.datetime.utcnow() - \
            datetime.timedelta(minutes=randint(2, 120))
        published = curr_timeAdjusted.strftime("%Y:%m:%d %H:%M:%S+00:00")
        (latitude, longitude, latitudeRef, longitudeRef,
         camMake, camModel, camSerialNumber) = \
            spoof_geolocation(base_dir, spoofCity, curr_timeAdjusted,
                              decoySeed, None, None)
        if os.system('exiftool -artist=@"' + nickname + '@' + domain + '" ' +
                     '-Make="' + camMake + '" ' +
                     '-Model="' + camModel + '" ' +
                     '-Comment="' + str(camSerialNumber) + '" ' +
                     '-DateTimeOriginal="' + published + '" ' +
                     '-FileModifyDate="' + published + '" ' +
                     '-CreateDate="' + published + '" ' +
                     '-GPSLongitudeRef=' + longitudeRef + ' ' +
                     '-GPSAltitude=0 ' +
                     '-GPSLongitude=' + str(longitude) + ' ' +
                     '-GPSLatitudeRef=' + latitudeRef + ' ' +
                     '-GPSLatitude=' + str(latitude) + ' ' +
                     '-copyright="' + content_license_url + '" ' +
                     '-Comment="" ' +
                     outputFilename) != 0:  # nosec
            print('ERROR: exiftool failed to run')
    else:
        print('ERROR: exiftool is not installed')
        return


def convert_image_to_low_bandwidth(image_filename: str) -> None:
    """Converts an image to a low bandwidth version
    """
    low_bandwidthFilename = image_filename + '.low'
    if os.path.isfile(low_bandwidthFilename):
        try:
            os.remove(low_bandwidthFilename)
        except OSError:
            print('EX: convert_image_to_low_bandwidth unable to delete ' +
                  low_bandwidthFilename)

    cmd = \
        '/usr/bin/convert +noise Multiplicative ' + \
        '-evaluate median 10% -dither Floyd-Steinberg ' + \
        '-monochrome  ' + image_filename + ' ' + low_bandwidthFilename
    print('Low bandwidth image conversion: ' + cmd)
    subprocess.call(cmd, shell=True)
    # wait for conversion to happen
    ctr = 0
    while not os.path.isfile(low_bandwidthFilename):
        print('Waiting for low bandwidth image conversion ' + str(ctr))
        time.sleep(0.2)
        ctr += 1
        if ctr > 100:
            print('WARN: timed out waiting for low bandwidth image conversion')
            break
    if os.path.isfile(low_bandwidthFilename):
        try:
            os.remove(image_filename)
        except OSError:
            print('EX: convert_image_to_low_bandwidth unable to delete ' +
                  image_filename)
        os.rename(low_bandwidthFilename, image_filename)
        if os.path.isfile(image_filename):
            print('Image converted to low bandwidth ' + image_filename)
    else:
        print('Low bandwidth converted image not found: ' +
              low_bandwidthFilename)


def process_meta_data(base_dir: str, nickname: str, domain: str,
                      image_filename: str, outputFilename: str,
                      city: str, content_license_url: str) -> None:
    """Handles image metadata. This tries to spoof the metadata
    if possible, but otherwise just removes it
    """
    # first remove the metadata
    _remove_meta_data(image_filename, outputFilename)

    # now add some spoofed data to misdirect surveillance capitalists
    _spoof_meta_data(base_dir, nickname, domain, outputFilename, city,
                     content_license_url)


def _is_media(image_filename: str) -> bool:
    """Is the given file a media file?
    """
    if not os.path.isfile(image_filename):
        print('WARN: Media file does not exist ' + image_filename)
        return False
    permittedMedia = get_media_extensions()
    for m in permittedMedia:
        if image_filename.endswith('.' + m):
            return True
    print('WARN: ' + image_filename + ' is not a permitted media type')
    return False


def create_media_dirs(base_dir: str, mediaPath: str) -> None:
    if not os.path.isdir(base_dir + '/media'):
        os.mkdir(base_dir + '/media')
    if not os.path.isdir(base_dir + '/' + mediaPath):
        os.mkdir(base_dir + '/' + mediaPath)


def get_media_path() -> str:
    curr_time = datetime.datetime.utcnow()
    weeksSinceEpoch = int((curr_time - datetime.datetime(1970, 1, 1)).days / 7)
    return 'media/' + str(weeksSinceEpoch)


def get_attachment_media_type(filename: str) -> str:
    """Returns the type of media for the given file
    image, video or audio
    """
    mediaType = None
    imageTypes = get_image_extensions()
    for mType in imageTypes:
        if filename.endswith('.' + mType):
            return 'image'
    videoTypes = get_video_extensions()
    for mType in videoTypes:
        if filename.endswith('.' + mType):
            return 'video'
    audioTypes = get_audio_extensions()
    for mType in audioTypes:
        if filename.endswith('.' + mType):
            return 'audio'
    return mediaType


def _update_etag(mediaFilename: str) -> None:
    """ calculate the etag, which is a sha1 of the data
    """
    # only create etags for media
    if '/media/' not in mediaFilename:
        return

    # check that the media exists
    if not os.path.isfile(mediaFilename):
        return

    # read the binary data
    data = None
    try:
        with open(mediaFilename, 'rb') as mediaFile:
            data = mediaFile.read()
    except OSError:
        print('EX: _update_etag unable to read ' + str(mediaFilename))

    if not data:
        return
    # calculate hash
    etag = sha1(data).hexdigest()  # nosec
    # save the hash
    try:
        with open(mediaFilename + '.etag', 'w+') as etagFile:
            etagFile.write(etag)
    except OSError:
        print('EX: _update_etag unable to write ' +
              str(mediaFilename) + '.etag')


def attach_media(base_dir: str, http_prefix: str,
                 nickname: str, domain: str, port: int,
                 post_json: {}, image_filename: str,
                 mediaType: str, description: str,
                 city: str, low_bandwidth: bool,
                 content_license_url: str) -> {}:
    """Attaches media to a json object post
    The description can be None
    """
    if not _is_media(image_filename):
        return post_json

    fileExtension = None
    acceptedTypes = get_media_extensions()
    for mType in acceptedTypes:
        if image_filename.endswith('.' + mType):
            if mType == 'jpg':
                mType = 'jpeg'
            if mType == 'mp3':
                mType = 'mpeg'
            fileExtension = mType
    if not fileExtension:
        return post_json
    mediaType = mediaType + '/' + fileExtension
    print('Attached media type: ' + mediaType)

    if fileExtension == 'jpeg':
        fileExtension = 'jpg'
    if mediaType == 'audio/mpeg':
        fileExtension = 'mp3'

    domain = get_full_domain(domain, port)

    mPath = get_media_path()
    mediaPath = mPath + '/' + create_password(32) + '.' + fileExtension
    if base_dir:
        create_media_dirs(base_dir, mPath)
        mediaFilename = base_dir + '/' + mediaPath

    mediaPath = \
        mediaPath.replace('media/', 'system/media_attachments/files/', 1)
    attachmentJson = {
        'mediaType': mediaType,
        'name': description,
        'type': 'Document',
        'url': http_prefix + '://' + domain + '/' + mediaPath
    }
    if mediaType.startswith('image/'):
        attachmentJson['blurhash'] = _get_blur_hash()
        # find the dimensions of the image and add them as metadata
        attachImageWidth, attachImageHeight = \
            get_image_dimensions(image_filename)
        if attachImageWidth and attachImageHeight:
            attachmentJson['width'] = attachImageWidth
            attachmentJson['height'] = attachImageHeight

    post_json['attachment'] = [attachmentJson]

    if base_dir:
        if mediaType.startswith('image/'):
            if low_bandwidth:
                convert_image_to_low_bandwidth(image_filename)
            process_meta_data(base_dir, nickname, domain,
                              image_filename, mediaFilename, city,
                              content_license_url)
        else:
            copyfile(image_filename, mediaFilename)
        _update_etag(mediaFilename)

    return post_json


def archive_media(base_dir: str, archive_directory: str,
                  maxWeeks: int) -> None:
    """Any media older than the given number of weeks gets archived
    """
    if maxWeeks == 0:
        return

    curr_time = datetime.datetime.utcnow()
    weeksSinceEpoch = int((curr_time - datetime.datetime(1970, 1, 1)).days/7)
    minWeek = weeksSinceEpoch - maxWeeks

    if archive_directory:
        if not os.path.isdir(archive_directory):
            os.mkdir(archive_directory)
        if not os.path.isdir(archive_directory + '/media'):
            os.mkdir(archive_directory + '/media')

    for subdir, dirs, files in os.walk(base_dir + '/media'):
        for weekDir in dirs:
            if int(weekDir) < minWeek:
                if archive_directory:
                    move(os.path.join(base_dir + '/media', weekDir),
                         archive_directory + '/media')
                else:
                    # archive to /dev/null
                    rmtree(os.path.join(base_dir + '/media', weekDir),
                           ignore_errors=False, onerror=None)
        break


def path_is_video(path: str) -> bool:
    if path.endswith('.ogv') or \
       path.endswith('.mp4'):
        return True
    return False


def path_is_audio(path: str) -> bool:
    if path.endswith('.ogg') or \
       path.endswith('.mp3'):
        return True
    return False


def get_image_dimensions(image_filename: str) -> (int, int):
    """Returns the dimensions of an image file
    """
    try:
        result = subprocess.run(['identify', '-format', '"%wx%h"',
                                 image_filename], stdout=subprocess.PIPE)
    except BaseException:
        print('EX: get_image_dimensions unable to run identify command')
        return None, None
    if not result:
        return None, None
    dimensionsStr = result.stdout.decode('utf-8').replace('"', '')
    if 'x' not in dimensionsStr:
        return None, None
    widthStr = dimensionsStr.split('x')[0]
    if not widthStr.isdigit():
        return None, None
    heightStr = dimensionsStr.split('x')[1]
    if not heightStr.isdigit():
        return None, None
    return int(widthStr), int(heightStr)
