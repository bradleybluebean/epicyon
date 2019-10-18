__filename__ = "skills.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

import json
import commentjson
import os
import time
from webfinger import webfingerHandle
from auth import createBasicAuthHeader
from posts import getPersonBox
from session import postJson
from utils import getNicknameFromActor
from utils import getDomainFromActor

def setSkillLevel(baseDir: str,nickname: str,domain: str, \
                  skill: str,skillLevelPercent: int) -> bool:
    """Set a skill level for a person
    Setting skill level to zero removes it
    """
    if skillLevelPercent<0 or skillLevelPercent>100:
        return False
    actorFilename=baseDir+'/accounts/'+nickname+'@'+domain+'.json'
    if not os.path.isfile(actorFilename):
        return False

    actorJson=None
    tries=0
    while tries<5:
        try:
            with open(actorFilename, 'r') as fp:
                actorJson=commentjson.load(fp)
                break
        except Exception as e:
            print('WARN: commentjson exception setSkillLevel - '+str(e))
            time.sleep(1)
            tries+=1

    if actorJson:
        if not actorJson.get('skills'):
            actorJson['skills']={}
        if skillLevelPercent>0:
            actorJson['skills'][skill]=skillLevelPercent
        else:
            del actorJson['skills'][skill]
        tries=0
        while tries<5:
            try:
                with open(actorFilename, 'w') as fp:
                    commentjson.dump(actorJson, fp, indent=2, sort_keys=False)
                    break
            except Exception as e:
                print(e)
                time.sleep(1)
                tries+=1
    return True

def setSkills(baseDir: str,nickname: str,domain: str,skills: {}) -> None:
    actorFilename=baseDir+'/accounts/'+nickname+'@'+domain+'.json'
    if not os.path.isfile(actorFilename):
        return False

    actorJson=None
    tries=0
    while tries<5:
        try:
            with open(actorFilename, 'r') as fp:
                actorJson=commentjson.load(fp)
                break
        except Exception as e:
            print('WARN: commentjson exception setSkills - '+str(e))
            time.sleep(1)
            tries+=1

    if actorJson:
        actorJson['skills']=skills
        tries=0
        while tries<5:
            try:
                with open(actorFilename, 'w') as fp:
                    commentjson.dump(actorJson, fp, indent=2, sort_keys=False)
                    break
            except Exception as e:
                print(e)
                time.sleep(1)
                tries+=1

def getSkills(baseDir: str,nickname: str,domain: str) -> []:
    """Returns the skills for a given person
    """
    actorFilename=baseDir+'/accounts/'+nickname+'@'+domain+'.json'
    if not os.path.isfile(actorFilename):
        return False

    actorJson=None
    tries=0
    while tries<5:
        try:
            with open(actorFilename, 'r') as fp:
                actorJson=commentjson.load(fp)
                break
        except Exception as e:
            print('WARN: commentjson exception getSkills - '+str(e))
            time.sleep(1)
            tries+=1

    if actorJson:
        if not actorJson.get('skills'):
            return None
        return actorJson['skills']
    return None

def outboxSkills(baseDir: str,nickname: str,messageJson: {},debug: bool) -> bool:
    """Handles receiving a skills update
    """
    if not messageJson.get('type'):
        return False
    if not messageJson['type']=='Skill':
        return False
    if not messageJson.get('actor'):
        return False
    if not messageJson.get('object'):
        return False
    if not isinstance(messageJson['object'], str):
        return False

    actorNickname=getNicknameFromActor(messageJson['actor'])
    if actorNickname!=nickname:
        return False
    domain,port=getDomainFromActor(messageJson['actor'])
    skill=messageJson['object'].replace('"','').split(';')[0].strip()
    skillLevelPercent=int(messageJson['object'].replace('"','').split(';')[1].strip())

    return setSkillLevel(baseDir,nickname,domain, \
                         skill,skillLevelPercent)

def sendSkillViaServer(baseDir: str,session,nickname: str,password: str,
                       domain: str,port: int, \
                       httpPrefix: str, \
                       skill: str,skillLevelPercent: int, \
                       cachedWebfingers: {},personCache: {}, \
                       debug: bool,projectVersion: str) -> {}:
    """Sets a skill for a person via c2s
    """
    if not session:
        print('WARN: No session for sendSkillViaServer')
        return 6

    domainFull=domain
    if port:
        if port!=80 and port!=443:
            if ':' not in domain:
                domainFull=domain+':'+str(port)
        
    toUrl = httpPrefix+'://'+domainFull+'/users/'+nickname
    ccUrl = httpPrefix+'://'+domainFull+'/users/'+nickname+'/followers'

    if skillLevelPercent:
        skillStr=skill+';'+str(skillLevelPercent)
    else:
        skillStr=skill+';0'
    newSkillJson = {
        'type': 'Skill',
        'actor': httpPrefix+'://'+domainFull+'/users/'+nickname,
        'object': '"'+skillStr+'"',
        'to': [toUrl],
        'cc': [ccUrl]
    }

    handle=httpPrefix+'://'+domainFull+'/@'+nickname

    # lookup the inbox for the To handle
    wfRequest = webfingerHandle(session,handle,httpPrefix,cachedWebfingers, \
                                domain,projectVersion)
    if not wfRequest:
        if debug:
            print('DEBUG: announce webfinger failed for '+handle)
        return 1

    postToBox='outbox'

    # get the actor inbox for the To handle
    inboxUrl,pubKeyId,pubKey,fromPersonId,sharedInbox,capabilityAcquisition,avatarUrl,displayName = \
        getPersonBox(baseDir,session,wfRequest,personCache, \
                     projectVersion,httpPrefix,nickname,domain,postToBox)
                     
    if not inboxUrl:
        if debug:
            print('DEBUG: No '+postToBox+' was found for '+handle)
        return 3
    if not fromPersonId:
        if debug:
            print('DEBUG: No actor was found for '+handle)
        return 4
    
    authHeader=createBasicAuthHeader(Nickname,password)
     
    headers = {'host': domain, \
               'Content-type': 'application/json', \
               'Authorization': authHeader}
    postResult = \
        postJson(session,newSkillJson,[],inboxUrl,headers,"inbox:write")
    #if not postResult:
    #    if debug:
    #        print('DEBUG: POST announce failed for c2s to '+inboxUrl)
    #    return 5

    if debug:
        print('DEBUG: c2s POST skill success')

    return newSkillJson
