__filename__ = "webfinger.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "0.0.1"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

import base64
from Crypto.PublicKey import RSA
from Crypto.Util import number
import requests
import json
import commentjson
import os
from session import getJson
from cache import storeWebfingerInCache
from cache import getWebfingerFromCache

def parseHandle(handle: str) -> (str,str):
    if '.' not in handle:
        return None, None
    if '/@' in handle:
        domain, nickname = \
            handle.replace('https://','').replace('http://','').replace('dat://','').split('/@')
    else:
        if '/users/' in handle:
            domain, nickname = \
                handle.replace('https://','').replace('http://','').replace('dat://','').split('/users/')
        else:
            if '@' in handle:
                nickname, domain = handle.split('@')
            else:
                return None, None

    return nickname, domain

def webfingerHandle(session,handle: str,httpPrefix: str,cachedWebfingers: {}) -> {}:
    if not session:
        print('WARN: No session specified for webfingerHandle')
        return None

    nickname, domain = parseHandle(handle)
    print('wfTest2 '+nickname+' '+domain)
    if not nickname:
        return None
    wfDomain=domain
    if ':' in wfDomain:
        #wfPort=int(wfDomain.split(':')[1])
        #if wfPort==80 or wfPort==443:
        wfDomain=wfDomain.split(':')[0]
    wf=getWebfingerFromCache(nickname+'@'+wfDomain,cachedWebfingers)
    if wf:
        return wf
    url = '{}://{}/.well-known/webfinger'.format(httpPrefix,domain)
    par = {'resource': 'acct:{}'.format(nickname+'@'+wfDomain)}
    hdr = {'Accept': 'application/jrd+json'}
    try:
        result = getJson(session, url, hdr, par)
    except:
        print("Unable to webfinger " + url)
        print('headers: '+str(hdr))
        print('params: '+str(par))
        return None
    storeWebfingerInCache(nickname+'@'+wfDomain,result,cachedWebfingers)
    return result

def generateMagicKey(publicKeyPem) -> str:
    """See magic_key method in
       https://github.com/tootsuite/mastodon/blob/707ddf7808f90e3ab042d7642d368c2ce8e95e6f/app/models/account.rb
    """
    privkey = RSA.importKey(publicKeyPem)    
    mod = base64.urlsafe_b64encode(number.long_to_bytes(privkey.n)).decode("utf-8")
    pubexp = base64.urlsafe_b64encode(number.long_to_bytes(privkey.e)).decode("utf-8")
    return f"data:application/magic-public-key,RSA.{mod}.{pubexp}"

def storeWebfingerEndpoint(nickname: str,domain: str,baseDir: str, \
                           wfJson: {}) -> bool:
    """Stores webfinger endpoint for a user to a file
    """
    handle=nickname+'@'+domain
    wfSubdir='/wfendpoints'
    if not os.path.isdir(baseDir+wfSubdir):
        os.mkdir(baseDir+wfSubdir)
    filename=baseDir+wfSubdir+'/'+handle.lower()+'.json'
    with open(filename, 'w') as fp:
        commentjson.dump(wfJson, fp, indent=4, sort_keys=False)
    return True

def createWebfingerEndpoint(nickname: str,domain: str,port: int, \
                            httpPrefix: str,publicKeyPem) -> {}:
    """Creates a webfinger endpoint for a user
    """
    originalDomain=domain
    if port!=80 and port!=443:
        domain=domain+':'+str(port)

    account = {
        "aliases": [
            httpPrefix+"://"+domain+"/@"+nickname,
            httpPrefix+"://"+domain+"/users/"+nickname
        ],
        "links": [
            {
                "href": httpPrefix+"://"+domain+"/@"+nickname,
                "rel": "http://webfinger.net/rel/profile-page",
                "type": "text/html"
            },
            {
                "href": httpPrefix+"://"+domain+"/users/"+nickname+".atom",
                "rel": "http://schemas.google.com/g/2010#updates-from",
                "type": "application/atom+xml"
            },
            {
                "href": httpPrefix+"://"+domain+"/users/"+nickname,
                "rel": "self",
                "type": "application/activity+json"
            },
            {
                "href": httpPrefix+"://"+domain+"/api/salmon/1",
                "rel": "salmon"
            },
            {
                "href": generateMagicKey(publicKeyPem),
                "rel": "magic-public-key"
            },
            {
                "rel": "http://ostatus.org/schema/1.0/subscribe",
                "template": httpPrefix+"://"+domain+"/authorize_interaction?uri={uri}"
            }
        ],
        "subject": "acct:"+nickname+"@"+originalDomain
    }
    return account

def webfingerMeta() -> str:
    """
    """
    return "<?xml version=’1.0' encoding=’UTF-8'?>" \
        "<XRD xmlns=’http://docs.oasis-open.org/ns/xri/xrd-1.0'" \
        " xmlns:hm=’http://host-meta.net/xrd/1.0'>" \
        "" \
        "<hm:Host>example.com</hm:Host>" \
        "" \
        "<Link rel=’lrdd’" \
        " template=’http://example.com/describe?uri={uri}'>" \
        " <Title>Resource Descriptor</Title>" \
        " </Link>" \
        "</XRD>"

def webfingerLookup(path: str,baseDir: str) -> {}:
    """Lookup the webfinger endpoint for an account
    """
    if not path.startswith('/.well-known/webfinger?'):
        return None
    handle=None
    if 'resource=acct:' in path:
        handle=path.split('resource=acct:')[1].strip()        
    else:
        if 'resource=acct%3A' in path:
            handle=path.split('resource=acct%3A')[1].replace('%40','@').strip()            
    if not handle:
        return None
    if '&' in handle:
        handle=handle.split('&')[0].strip()
    if '@' not in handle:
        return None
    filename=baseDir+'/wfendpoints/'+handle.lower()+'.json'
    if not os.path.isfile(filename):
        return None
    wfJson={"nickname": "unknown"}
    with open(filename, 'r') as fp:
        wfJson=commentjson.load(fp)
    return wfJson
