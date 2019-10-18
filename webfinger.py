__filename__ = "webfinger.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
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
import time
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

def webfingerHandle(session,handle: str,httpPrefix: str,cachedWebfingers: {}, \
                    fromDomain: str,projectVersion: str) -> {}:
    if not session:
        print('WARN: No session specified for webfingerHandle')
        return None

    nickname, domain = parseHandle(handle)
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
        result = getJson(session, url, hdr, par,projectVersion,httpPrefix,fromDomain)
    except Exception as e:
        print("Unable to webfinger " + url)
        print('nickname: '+str(nickname))
        print('domain: '+str(wfDomain))
        print('headers: '+str(hdr))
        print('params: '+str(par))
        print(e)
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

def storeWebfingerEndpoint(nickname: str,domain: str,port: int,baseDir: str, \
                           wfJson: {}) -> bool:
    """Stores webfinger endpoint for a user to a file
    """
    originalDomain=domain
    if port:
        if port!=80 and port!=443:
            if ':' not in domain:
                domain=domain+':'+str(port)
    handle=nickname+'@'+domain
    wfSubdir='/wfendpoints'
    if not os.path.isdir(baseDir+wfSubdir):
        os.mkdir(baseDir+wfSubdir)
    filename=baseDir+wfSubdir+'/'+handle.lower()+'.json'
    tries=0
    while tries<5:
        try:
            with open(filename, 'w') as fp:
                commentjson.dump(wfJson, fp, indent=2, sort_keys=False)
                break
        except Exception as e:
            print(e)
            time.sleep(1)
            tries+=1
    if nickname=='inbox':
        handle=originalDomain+'@'+domain
        filename=baseDir+wfSubdir+'/'+handle.lower()+'.json'
        tries=0
        while tries<5:
            try:
                with open(filename, 'w') as fp:
                    commentjson.dump(wfJson, fp, indent=2, sort_keys=False)
                    break
            except Exception as e:
                print(e)
                time.sleep(1)
                tries+=1
    return True

def createWebfingerEndpoint(nickname: str,domain: str,port: int, \
                            httpPrefix: str,publicKeyPem) -> {}:
    """Creates a webfinger endpoint for a user
    """
    originalDomain=domain
    if port:
        if port!=80 and port!=443:
            if ':' not in domain:
                domain=domain+':'+str(port)

    personName=nickname
    personId=httpPrefix+"://"+domain+"/users/"+personName
    subjectStr="acct:"+personName+"@"+originalDomain
    profilePageHref=httpPrefix+"://"+domain+"/@"+nickname
    if nickname=='inbox' or nickname==originalDomain:
        personName='actor'
        personId=httpPrefix+"://"+domain+"/"+personName
        subjectStr="acct:"+originalDomain+"@"+originalDomain
        profilePageHref=httpPrefix+'://'+domain+'/about/more?instance_actor=true'
    
    account = {
        "aliases": [
            httpPrefix+"://"+domain+"/@"+personName,
            personId
        ],
        "links": [
            {
                "href": profilePageHref,
                "rel": "http://webfinger.net/rel/profile-page",
                "type": "text/html"
            },
            {
                "href": httpPrefix+"://"+domain+"/users/"+nickname+".atom",
                "rel": "http://schemas.google.com/g/2010#updates-from",
                "type": "application/atom+xml"
            },
            {
                "href": personId,
                "rel": "self",
                "type": "application/activity+json"
            },
            {
                "href": generateMagicKey(publicKeyPem),
                "rel": "magic-public-key"
            }
        ],
        "subject": subjectStr
    }
    return account

def webfingerMeta(httpPrefix: str,domainFull: str) -> str:
    """Return /.well-known/host-meta
    """
    #return \
    #    "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" \
    #    "<XRD xmlns=\"http://docs.oasis-open.org/ns/xri/xrd-1.0\">" \
    #    "<Link rel=\"lrdd\" type=\"application/xrd+xml\" template=\""+httpPrefix+"://"+domainFull+"/.well-known/webfinger?resource={uri}\"/>" \
    #    "</XRD>"

    return \
        "<?xml version=’1.0' encoding=’UTF-8'?>" \
        "<XRD xmlns=’http://docs.oasis-open.org/ns/xri/xrd-1.0'" \
        " xmlns:hm=’http://host-meta.net/xrd/1.0'>" \
        "" \
        "<hm:Host>"+domainFull+"</hm:Host>" \
        "" \
        "<Link rel=’lrdd’" \
        " template=’"+httpPrefix+"://"+domainFull+"/describe?uri={uri}'>" \
        " <Title>Resource Descriptor</Title>" \
        " </Link>" \
        "</XRD>"

def webfingerLookup(path: str,baseDir: str,port: int,debug: bool) -> {}:
    """Lookup the webfinger endpoint for an account
    """
    if not path.startswith('/.well-known/webfinger?'):        
        return None
    handle=None
    if 'resource=acct:' in path:
        handle=path.split('resource=acct:')[1].strip()
        if debug:
            print('DEBUG: WEBFINGER handle '+handle)
    else:
        if 'resource=acct%3A' in path:
            handle=path.split('resource=acct%3A')[1].replace('%40','@',1).replace('%3A',':',1).strip()
            if debug:
                print('DEBUG: WEBFINGER handle '+handle)
    if not handle:
        if debug:
            print('DEBUG: WEBFINGER handle missing')
        return None
    if '&' in handle:
        handle=handle.split('&')[0].strip()
        if debug:
            print('DEBUG: WEBFINGER handle with & removed '+handle)
    if '@' not in handle:
        if debug:
            print('DEBUG: WEBFINGER no @ in handle '+handle)
        return None
    if port:
        if port!=80 and port !=443:
            if ':' not in handle:
                handle=handle+':'+str(port)
    # convert @domain@domain to inbox@domain
    if '@' in handle:
        handleDomain=handle.split('@')[1]
        if handle.startswith(handleDomain+'@'):
            handle='inbox@'+handleDomain
    filename=baseDir+'/wfendpoints/'+handle.lower()+'.json'
    if debug:
        print('DEBUG: WEBFINGER filename '+filename)
    if not os.path.isfile(filename):
        if debug:
            print('DEBUG: WEBFINGER filename not found '+filename)
        return None
    wfJson={"nickname": "unknown"}
    tries=0
    while tries<5:
        try:
            with open(filename, 'r') as fp:
                wfJson=commentjson.load(fp)
                break
        except Exception as e:
            print('WARN: commentjson exception webfingerLookup - '+str(e))
            time.sleep(1)
            tries+=1
    return wfJson
