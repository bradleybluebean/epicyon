__filename__ = "media.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "0.0.1"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

from blurhash import blurhash_encode as blurencode
from PIL import Image
import numpy
import os
import json
import commentjson
import datetime
from auth import createPassword
from shutil import copyfile

def getImageHash(imageFilename: str):
    return blurencode(numpy.array(Image.open("img/logo.png").convert("RGB")))

def isImage(imageFilename: str) -> bool:
    if imageFilename.endswith('.png') or \
       imageFilename.endswith('.jpg') or \
       imageFilename.endswith('.gif'):
        return True
    return False

def createMediaPath(baseDir: str,weeksSinceEpoch: int) -> None:    
    if not os.path.isdir(baseDir+'/media'):
        os.mkdir(baseDir+'/media')
    if not os.path.isdir(baseDir+'/media/'+str(weeksSinceEpoch)):
        os.mkdir(baseDir+'/media/'+str(weeksSinceEpoch))

def attachImage(baseDir: str,httpPrefix: str,domain: str,port: int, \
                postJson: {},imageFilename: str,description: str, \
                useBlurhash: bool) -> {}:
    """Attaches an image to a json object post
    The description can be None
    Blurhash is optional, since low power systems may take a long time to calculate it
    """
    if not isImage(imageFilename):
        return postJson

    mediaType='image/png'
    fileExtension='png'
    if imageFilename.endswith('.jpg'):
        mediaType='image/jpeg'
        fileExtension='jpg'
    if imageFilename.endswith('.gif'):
        mediaType='image/gif'        
        fileExtension='gif'

    if port!=80 and port!=443:
        if ':' not in domain:
            domain=domain+':'+str(port)

    currTime=datetime.datetime.utcnow()
    weeksSinceEpoch=(currTime - datetime.datetime(1970,1,1)).days/7
    createMediaPath(baseDir,weeksSinceEpoch)
    mediaPath='media/'+str(weeksSinceEpoch)+'/'+createPassword(32)+'.'+fileExtension
    mediaFilename=baseDir+'/'+mediaPath

    attachmentJson={
        'mediaType': mediaType,
        'name': description,
        'type': 'Document',
        'url': httpPrefix+'://'+domain+'/'+mediaPath
    }
    if useBlurhash:
        attachmentJson['blurhash']=getImageHash(imageFilename)
    postJson['attachment']=[attachmentJson]

    copyfile(imageFilename,mediaFilename)
             
    return postJson

def removeAttachment(baseDir: str,httpPrefix: str,domain: str,postJson: {}):
    if not postJson.get('attachment'):
        return
    if not postJson['attachment'][0].get('url'):
        return
    if port!=80 and port!=443:
        if ':' not in domain:
            domain=domain+':'+str(port)
    attachmentUrl=postJson['attachment'][0]['url']
    if not attachmentUrl:
        return
    mediaFilename=baseDir+'/'+attachmentUrl.replace(httpPrefix+'://'+domain+'/','')
    if os.path.isfile(mediaFilename):
        os.remove(mediaFilename)
    postJson['attachment']=[]
