__filename__ = "cache.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.2.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"
__module_group__ = "ActivityPub"

import os
import datetime
from session import urlExists
from utils import loadJson
from utils import saveJson
from utils import getFileCaseInsensitive


def _removePersonFromCache(baseDir: str, personUrl: str,
                           personCache: {}) -> bool:
    """Removes an actor from the cache
    """
    cacheFilename = baseDir + '/cache/actors/' + \
        personUrl.replace('/', '#') + '.json'
    if os.path.isfile(cacheFilename):
        try:
            os.remove(cacheFilename)
        except BaseException:
            pass
    if personCache.get(personUrl):
        del personCache[personUrl]


def checkForChangedActor(session, baseDir: str,
                         httpPrefix: str, domainFull: str,
                         personUrl: str, avatarUrl: str, personCache: {},
                         timeoutSec: int):
    """Checks if the avatar url exists and if not then
    the actor has probably changed without receiving an actor/Person Update.
    So clear the actor from the cache and it will be refreshed when the next
    post from them is sent
    """
    if not session or not avatarUrl:
        return
    if domainFull in avatarUrl:
        return
    if urlExists(session, avatarUrl, timeoutSec, httpPrefix, domainFull):
        return
    _removePersonFromCache(baseDir, personUrl, personCache)


def storePersonInCache(baseDir: str, personUrl: str,
                       personJson: {}, personCache: {},
                       allowWriteToFile: bool) -> None:
    """Store an actor in the cache
    """
    if 'statuses' in personUrl or personUrl.endswith('/actor'):
        # This is not an actor or person account
        return

    currTime = datetime.datetime.utcnow()
    personCache[personUrl] = {
        "actor": personJson,
        "timestamp": currTime.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    if not baseDir:
        return

    # store to file
    if not allowWriteToFile:
        return
    if os.path.isdir(baseDir + '/cache/actors'):
        cacheFilename = baseDir + '/cache/actors/' + \
            personUrl.replace('/', '#') + '.json'
        if not os.path.isfile(cacheFilename):
            saveJson(personJson, cacheFilename)


def getPersonFromCache(baseDir: str, personUrl: str, personCache: {},
                       allowWriteToFile: bool) -> {}:
    """Get an actor from the cache
    """
    # if the actor is not in memory then try to load it from file
    loadedFromFile = False
    if not personCache.get(personUrl):
        # does the person exist as a cached file?
        cacheFilename = baseDir + '/cache/actors/' + \
            personUrl.replace('/', '#') + '.json'
        actorFilename = getFileCaseInsensitive(cacheFilename)
        if actorFilename:
            personJson = loadJson(actorFilename)
            if personJson:
                storePersonInCache(baseDir, personUrl, personJson,
                                   personCache, False)
                loadedFromFile = True

    if personCache.get(personUrl):
        if not loadedFromFile:
            # update the timestamp for the last time the actor was retrieved
            currTime = datetime.datetime.utcnow()
            currTimeStr = currTime.strftime("%Y-%m-%dT%H:%M:%SZ")
            personCache[personUrl]['timestamp'] = currTimeStr
        return personCache[personUrl]['actor']
    return None


def expirePersonCache(personCache: {}):
    """Expires old entries from the cache in memory
    """
    currTime = datetime.datetime.utcnow()
    removals = []
    for personUrl, cacheJson in personCache.items():
        cacheTime = datetime.datetime.strptime(cacheJson['timestamp'],
                                               "%Y-%m-%dT%H:%M:%SZ")
        daysSinceCached = (currTime - cacheTime).days
        if daysSinceCached > 2:
            removals.append(personUrl)
    if len(removals) > 0:
        for personUrl in removals:
            del personCache[personUrl]
        print(str(len(removals)) + ' actors were expired from the cache')


def storeWebfingerInCache(handle: str, wf, cachedWebfingers: {}) -> None:
    """Store a webfinger endpoint in the cache
    """
    cachedWebfingers[handle] = wf


def getWebfingerFromCache(handle: str, cachedWebfingers: {}) -> {}:
    """Get webfinger endpoint from the cache
    """
    if cachedWebfingers.get(handle):
        return cachedWebfingers[handle]
    return None
