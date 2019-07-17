__filename__ = "epicyon.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "0.0.1"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"


from person import createPerson
from person import createSharedInbox
from person import createCapabilitiesInbox
from person import setPreferredNickname
from person import setBio
from person import validNickname
from person import setProfileImage
from person import setSkillLevel
from person import setRole
from person import setAvailability
from person import setOrganizationScheme
from webfinger import webfingerHandle
from posts import getPosts
from posts import createPublicPost
from posts import deleteAllPosts
from posts import createOutbox
from posts import archivePosts
from posts import sendPostViaServer
from posts import getPublicPostsOfPerson
from posts import getUserUrl
from posts import archivePosts
from session import createSession
from session import getJson
from blocking import addBlock
from blocking import removeBlock
from filters import addFilter
from filters import removeFilter
import json
import os
import shutil
import sys
import requests
from pprint import pprint
from tests import testHttpsig
from daemon import runDaemon
import socket
from follow import clearFollows
from follow import clearFollowers
from utils import followPerson
from follow import followerOfPerson
from follow import unfollowPerson
from follow import unfollowerOfPerson
from follow import getFollowersOfPerson
from tests import testPostMessageBetweenServers
from tests import testFollowBetweenServers
from tests import testClientToServer
from tests import runAllTests
from config import setConfigParam
from config import getConfigParam
from auth import storeBasicCredentials
from auth import removePassword
from auth import createPassword
from utils import getDomainFromActor
from utils import getNicknameFromActor
from media import archiveMedia
import argparse

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

parser = argparse.ArgumentParser(description='ActivityPub Server')
parser.add_argument('-n','--nickname', dest='nickname', type=str,default=None, \
                    help='Nickname of the account to use')
parser.add_argument('--fol','--follow', dest='follow', type=str,default=None, \
                    help='Handle of account to follow. eg. nickname@domain')
parser.add_argument('--unfol','--unfollow', dest='unfollow', type=str,default=None, \
                    help='Handle of account stop following. eg. nickname@domain')
parser.add_argument('-d','--domain', dest='domain', type=str,default=None, \
                    help='Domain name of the server')
parser.add_argument('-p','--port', dest='port', type=int,default=None, \
                    help='Port number to run on')
parser.add_argument('--path', dest='baseDir', \
                    type=str,default=os.getcwd(), \
                    help='Directory in which to store posts')
parser.add_argument('-a','--addaccount', dest='addaccount', \
                    type=str,default=None, \
                    help='Adds a new account')
parser.add_argument('-r','--rmaccount', dest='rmaccount', \
                    type=str,default=None, \
                    help='Remove an account')
parser.add_argument('--pass','--password', dest='password', \
                    type=str,default=None, \
                    help='Set a password for an account')
parser.add_argument('--chpass','--changepassword', \
                    nargs='+',dest='changepassword', \
                    help='Change the password for an account')
parser.add_argument('--actor', dest='actor', type=str,default=None, \
                    help='Show the json actor the given handle')
parser.add_argument('--posts', dest='posts', type=str,default=None, \
                    help='Show posts for the given handle')
parser.add_argument('--postsraw', dest='postsraw', type=str,default=None, \
                    help='Show raw json of posts for the given handle')
parser.add_argument('--json', dest='json', type=str,default=None, \
                    help='Show the json for a given activitypub url')
parser.add_argument('-f','--federate', nargs='+',dest='federationList', \
                    help='Specify federation list separated by spaces')
parser.add_argument("--debug", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Show debug messages")
parser.add_argument("--http", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Use http only")
parser.add_argument("--dat", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Use dat protocol only")
parser.add_argument("--tor", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Route via Tor")
parser.add_argument("--tests", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Run unit tests")
parser.add_argument("--testsnetwork", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Run network unit tests")
parser.add_argument("--testdata", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Generate some data for testing purposes")
parser.add_argument("--ocap", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Always strictly enforce object capabilities")
parser.add_argument("--noreply", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Default capabilities don't allow replies on posts")
parser.add_argument("--nolike", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Default capabilities don't allow likes/favourites on posts")
parser.add_argument("--nopics", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Default capabilities don't allow attached pictures")
parser.add_argument("--noannounce","--norepeat", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Default capabilities don't allow announce/repeat")
parser.add_argument("--cw", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Default capabilities don't allow posts without content warnings")
parser.add_argument('--icon','--avatar', dest='avatar', type=str,default=None, \
                    help='Set the avatar filename for an account')
parser.add_argument('--image','--background', dest='backgroundImage', type=str,default=None, \
                    help='Set the profile background image for an account')
parser.add_argument('--archive', dest='archive', type=str,default=None, \
                    help='Archive old files to the given directory')
parser.add_argument('--archiveweeks', dest='archiveWeeks', type=str,default=None, \
                    help='Specify the number of weeks after which data will be archived')
parser.add_argument('--maxposts', dest='archiveMaxPosts', type=str,default=None, \
                    help='Maximum number of posts in in/outbox')
parser.add_argument('--message', dest='message', type=str,default=None, \
                    help='Message content')
parser.add_argument('--repeat','--announce', dest='announce', type=str,default=None, \
                    help='Announce/repeat a url')
parser.add_argument('--sendto', nargs='+',dest='sendto', \
                    help='List of post recipients')
parser.add_argument('--attach', dest='attach', type=str,default=None, \
                    help='File to attach to a post')
parser.add_argument('--imagedescription', dest='imageDescription', type=str,default=None, \
                    help='Description of an attached image')
parser.add_argument("--blurhash", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Create blurhash for an image")
parser.add_argument('--warning','--warn','--cwsubject','--subject', dest='subject', type=str,default=None, \
                    help='Subject of content warning')
parser.add_argument('--reply','--replyto', dest='replyto', type=str,default=None, \
                    help='Url of post to reply to')
parser.add_argument("--followersonly", type=str2bool, nargs='?', \
                    const=True, default=True, \
                    help="Send to followers only")
parser.add_argument("-c","--client", type=str2bool, nargs='?', \
                    const=True, default=False, \
                    help="Use as an ActivityPub client")
parser.add_argument('--maxreplies', dest='maxReplies', type=int,default=64, \
                    help='Maximum number of replies to a post')
parser.add_argument('--role', dest='role', type=str,default=None, \
                    help='Set a role for a person')
parser.add_argument('--organization','--project', dest='project', type=str,default=None, \
                    help='Set a project for a person')
parser.add_argument('--skill', dest='skill', type=str,default=None, \
                    help='Set a skill for a person')
parser.add_argument('--level', dest='skillLevelPercent', type=int,default=None, \
                    help='Set a skill level for a person as a percentage, or zero to remove')
parser.add_argument('--status','--availability', dest='availability', type=str,default=None, \
                    help='Set an availability status')
parser.add_argument('--block', dest='block', type=str,default=None, \
                    help='Block a particular address')
parser.add_argument('--unblock', dest='unblock', type=str,default=None, \
                    help='Remove a block on a particular address')
parser.add_argument('--filter', dest='filterStr', type=str,default=None, \
                    help='Adds a word or phrase which if present will cause a message to be ignored')
parser.add_argument('--unfilter', dest='unfilterStr', type=str,default=None, \
                    help='Remove a filter on a particular word or phrase')
parser.add_argument('--domainmax', dest='domainMaxPostsPerDay', type=int,default=8640, \
                    help='Maximum number of received posts from a domain per day')
parser.add_argument('--accountmax', dest='accountMaxPostsPerDay', type=int,default=8640, \
                    help='Maximum number of received posts from an account per day')
args = parser.parse_args()

debug=False
if args.debug:
    debug=True

if args.tests:
    runAllTests()
    sys.exit()

if args.testsnetwork:
    print('Network Tests')
    testPostMessageBetweenServers()
    testFollowBetweenServers()
    testClientToServer()
    sys.exit()

if args.posts:
    if '@' not in args.posts:
        print('Syntax: --posts nickname@domain')
        sys.exit()        
    nickname=args.posts.split('@')[0]
    domain=args.posts.split('@')[1]
    getPublicPostsOfPerson(nickname,domain,False,True)
    sys.exit()

if args.postsraw:
    if '@' not in args.postsraw:
        print('Syntax: --postsraw nickname@domain')
        sys.exit()        
    nickname=args.postsraw.split('@')[0]
    domain=args.postsraw.split('@')[1]
    getPublicPostsOfPerson(nickname,domain,True,False)
    sys.exit()

baseDir=args.baseDir
if baseDir.endswith('/'):
    print("--path option should not end with '/'")
    sys.exit()

# get domain name from configuration
configDomain=getConfigParam(baseDir,'domain')
if configDomain:
    domain=configDomain
else:
    domain='localhost'

# get port number from configuration
configPort=getConfigParam(baseDir,'port')
if configPort:
    port=configPort
else:
    port=8085

nickname=None
if args.nickname:
    nickname=nickname

httpPrefix='https'
if args.http:
    httpPrefix='http'

federationList=[]
if args.federationList:
    if len(args.federationList)==1:
        if not (args.federationList[0].lower()=='any' or \
                args.federationList[0].lower()=='all' or \
                args.federationList[0].lower()=='*'):
            for federationDomain in args.federationList:
                if '@' in federationDomain:
                    print(federationDomain+': Federate with domains, not individual accounts')
                    sys.exit()
            federationList=args.federationList.copy()
        setConfigParam(baseDir,'federationList',federationList)
else:
    configFederationList=getConfigParam(baseDir,'federationList')
    if configFederationList:
        federationList=configFederationList

useTor=args.tor
if domain.endswith('.onion'):
    useTor=True

if args.message:
    if not nickname:
        print('Specify a nickname with the --nickname option')
        sys.exit()
        
    if not args.password:
        print('Specify a password with the --password option')
        sys.exit()
        
    session = createSession(domain,port,useTor)        
    if not args.sendto:
        print('Specify an account to sent to: --sendto [nickname@domain]')
        sys.exit()        
    if '@' not in args.sendto and \
       not args.sendto.lower().endswith('public') and \
       not args.sendto.lower().endswith('followers'):
        print('syntax: --sendto [nickname@domain]')
        print('        --sendto public')
        print('        --sendto followers')
        sys.exit()
    if '@' in args.sendto:
        toNickname=args.sendto.split('@')[0]
        toDomain=args.sendto.split('@')[1].replace('\n','')
        toPort=443
        if ':' in toDomain:
            toPort=toDomain.split(':')[1]
            toDomain=toDomain.split(':')[0]
    else:
        if args.sendto.endswith('followers'):
            toNickname=None
            toDomain='followers'
            toPort=port
        else:
            toNickname=None
            toDomain='public'
            toPort=port
        
    #ccUrl=httpPrefix+'://'+domain+'/users/'+nickname+'/followers'
    ccUrl=None
    sendMessage=args.message
    followersOnly=args.followersonly
    clientToServer=args.client
    attachedImageDescription=args.imageDescription
    useBlurhash=args.blurhash
    sendThreads = []
    postLog = []
    personCache={}
    cachedWebfingers={}
    subject=args.subject
    attach=args.attach
    replyTo=args.replyTo
    followersOnly=False
    print('Sending post to '+args.sendto)

    sendPostViaServer(session,nickname,args.password, \
                      domain,port, \
                      toNickname,toDomain,toPort,ccUrl, \
                      httpPrefix,sendMessage,followersOnly, \
                      attach,attachedImageDescription,useBlurhash, \
                      cachedWebfingers,personCache, \
                      args.debug,replyTo,replyTo,subject)
    for i in range(10):
        # TODO detect send success/fail
        time.sleep(1)
    sys.exit()

if args.announce:
    if not nickname:
        print('Specify a nickname with the --nickname option')
        sys.exit()
        
    if not args.password:
        print('Specify a password with the --password option')
        sys.exit()
        
    session = createSession(domain,port,useTor)        
    personCache={}
    cachedWebfingers={}
    print('Sending announce/repeat of '+args.announce)

    sendAnnounceViaServer(session,nickname,args.password,
                          domain,port, \
                          httpPrefix,args.announce, \
                          cachedWebfingers,personCache, \
                          True)
    for i in range(10):
        # TODO detect send success/fail
        time.sleep(1)
    sys.exit()

if args.follow:
    # follow via c2s protocol
    if '.' not in args.follow:
        print("This doesn't look like a fediverse handle")
        sys.exit()
    if not nickname:
        print('Please specify the nickname for the account with --nickname')
        sys.exit()
    if not args.password:
        print('Please specify the password for '+nickname+' on '+domain)
        sys.exit()
        
    followNickname=getNicknameFromActor(args.follow)
    followDomain,followPort=getDomainFromActor(args.follow)

    session = createSession(domain,port,useTor)
    personCache={}
    cachedWebfingers={}
    followHttpPrefix=httpPrefix
    if args.follow.startswith('https'):
        followHttpPrefix='https'

    sendFollowRequestViaServer(session,nickname,args.password, \
                               domain,port, \
                               followNickname,followDomain,followPort, \
                               httpPrefix, \
                               cachedWebfingers,personCache, \
                               debug)
    for t in range(20):
        time.sleep(1)
        # TODO some method to know if it worked
    print('Ok')
    sys.exit()

if args.unfollow:
    # unfollow via c2s protocol
    if '.' not in args.follow:
        print("This doesn't look like a fediverse handle")
        sys.exit()
    if not nickname:
        print('Please specify the nickname for the account with --nickname')
        sys.exit()
    if not args.password:
        print('Please specify the password for '+nickname+' on '+domain)
        sys.exit()
        
    followNickname=getNicknameFromActor(args.unfollow)
    followDomain,followPort=getDomainFromActor(args.unfollow)

    session = createSession(domain,port,useTor)
    personCache={}
    cachedWebfingers={}
    followHttpPrefix=httpPrefix
    if args.follow.startswith('https'):
        followHttpPrefix='https'

    sendUnfollowRequestViaServer(session,nickname,args.password, \
                                 domain,port, \
                                 followNickname,followDomain,followPort, \
                                 httpPrefix, \
                                 cachedWebfingers,personCache, \
                                 debug)
    for t in range(20):
        time.sleep(1)
        # TODO some method to know if it worked
    print('Ok')
    sys.exit()

nickname='admin'
if args.domain:
    domain=args.domain
    setConfigParam(baseDir,'domain',domain)
if args.port:
    port=args.port
    setConfigParam(baseDir,'port',port)
ocapAlways=False    
if args.ocap:
    ocapAlways=args.ocap
if args.dat:
    httpPrefix='dat'

if args.actor:
    if '@' not in args.actor:
        print('Syntax: --actor nickname@domain')
        sys.exit()        
    nickname=args.actor.split('@')[0]
    domain=args.actor.split('@')[1].replace('\n','')
    wfCache={}
    if domain.endswith('.onion'):
        httpPrefix='http'
        port=80
    else:
        httpPrefix='https'
        port=443
    session = createSession(domain,port,useTor)
    wfRequest = webfingerHandle(session,nickname+'@'+domain,httpPrefix,wfCache)
    if not wfRequest:
        print('Unable to webfinger '+nickname+'@'+domain)
        sys.exit()
    asHeader = {'Accept': 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'}
    personUrl = getUserUrl(wfRequest)
    personJson = getJson(session,personUrl,asHeader,None)
    if personJson:
        pprint(personJson)
    else:
        print('Failed to get '+personUrl)
    sys.exit()

if args.json:
    session = createSession(domain,port,True)
    asHeader = {'Accept': 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'}
    testJson = getJson(session,args.json,asHeader,None)
    pprint(testJson)
    sys.exit()

if args.addaccount:
    if '@' in args.addaccount:
        nickname=args.addaccount.split('@')[0]
        domain=args.addaccount.split('@')[1]
    else:
        nickname=args.addaccount
        if not args.domain or not getConfigParam(baseDir,'domain'):
            print('Use the --domain option to set the domain name')
            sys.exit()
    if not validNickname(nickname):
        print(nickname+' is a reserved name. Use something different.')
        sys.exit()        
    if not args.password:
        print('Use the --password option to set the password for '+nickname)
        sys.exit()
    if len(args.password.strip())<8:
        print('Password should be at least 8 characters')
        sys.exit()            
    if os.path.isdir(baseDir+'/accounts/'+nickname+'@'+domain):
        print('Account already exists')
        sys.exit()
    createPerson(baseDir,nickname,domain,port,httpPrefix,True,args.password.strip())
    if os.path.isdir(baseDir+'/accounts/'+nickname+'@'+domain):
        print('Account created for '+nickname+'@'+domain)
    else:
        print('Account creation failed')
    sys.exit()

if args.rmaccount:
    if '@' in args.rmaccount:
        nickname=args.rmaccount.split('@')[0]
        domain=args.rmaccount.split('@')[1]
    else:
        nickname=args.rmaccount
        if not args.domain or not getConfigParam(baseDir,'domain'):
            print('Use the --domain option to set the domain name')
            sys.exit()
    handle=nickname+'@'+domain
    accountRemoved=False
    removePassword(baseDir,nickname)
    if os.path.isdir(baseDir+'/accounts/'+handle):
        shutil.rmtree(baseDir+'/accounts/'+handle)
        accountRemoved=True
    if os.path.isfile(baseDir+'/accounts/'+handle+'.json'):
        os.remove(baseDir+'/accounts/'+handle+'.json')
        accountRemoved=True
    if os.path.isfile(baseDir+'/wfendpoints/'+handle+'.json'):
        os.remove(baseDir+'/wfendpoints/'+handle+'.json')
        accountRemoved=True
    if os.path.isfile(baseDir+'/keys/private/'+handle+'.key'):
        os.remove(baseDir+'/keys/private/'+handle+'.key')
        accountRemoved=True
    if os.path.isfile(baseDir+'/keys/public/'+handle+'.pem'):
        os.remove(baseDir+'/keys/public/'+handle+'.pem')
        accountRemoved=True
    if accountRemoved:
        print('Account for '+handle+' was removed')
    sys.exit()

if args.changepassword:
    if len(args.changepassword)!=2:
        print('--changepassword [nickname] [new password]')
        sys.exit()
    if '@' in args.changepassword[0]:
        nickname=args.changepassword[0].split('@')[0]
        domain=args.changepassword[0].split('@')[1]
    else:
        nickname=args.changepassword[0]
        if not args.domain or not getConfigParam(baseDir,'domain'):
            print('Use the --domain option to set the domain name')
            sys.exit()
    newPassword=args.changepassword[1]
    if len(newPassword)<8:
        print('Password should be at least 8 characters')
        sys.exit()
    if not os.path.isdir(baseDir+'/accounts/'+nickname+'@'+domain):
        print('Account '+nickname+'@'+domain+' not found')
        sys.exit()
    passwordFile=baseDir+'/accounts/passwords'
    if os.path.isfile(passwordFile):
        if nickname+':' in open(passwordFile).read():
            storeBasicCredentials(baseDir,nickname,newPassword)
            print('Password for '+nickname+' was changed')
        else:
            print(nickname+' is not in the passwords file')
    else:
        print('Passwords file not found')
    sys.exit()

archiveWeeks=4
if args.archiveWeeks:
    archiveWeeks=args.archiveWeeks
archiveMaxPosts=256
if args.archiveMaxPosts:
    archiveMaxPosts=args.archiveMaxPosts

if args.archive:
    if args.archive.lower().endswith('null') or \
       args.archive.lower().endswith('delete') or \
       args.archive.lower().endswith('none'):
        args.archive=None
        print('Archiving with deletion of old posts...')
    else:
        print('Archiving to '+args.archive+'...')
    archiveMedia(baseDir,args.archive,archiveWeeks)
    archivePosts(baseDir,httpPrefix,args.archive,archiveMaxPosts)
    print('Archiving complete')
    sys.exit()

if not args.domain and not domain:
    print('Specify a domain with --domain [name]')
    sys.exit()

if args.avatar:
    if not os.path.isfile(args.avatar):
        print(args.avatar+' is not an image filename')
        sys.exit()
    if not args.nickname:
        print('Specify a nickname with --nickname [name]')
        sys.exit()
    if setProfileImage(baseDir,httpPrefix,args.nickname,domain, \
                       port,args.avatar,'avatar','128x128'):
        print('Avatar added for '+args.nickname)
    else:
        print('Avatar was not added for '+args.nickname)
    sys.exit()    

if args.backgroundImage:
    if not os.path.isfile(args.backgroundImage):
        print(args.backgroundImage+' is not an image filename')
        sys.exit()
    if not args.nickname:
        print('Specify a nickname with --nickname [name]')
        sys.exit()
    if setProfileImage(baseDir,httpPrefix,args.nickname,domain, \
                       port,args.backgroundImage,'background','256x256'):
        print('Background image added for '+args.nickname)
    else:
        print('Background image was not added for '+args.nickname)
    sys.exit()    

if args.availability:
    if not nickname:
        print('No nickname given')
        sys.exit()
    if setAvailability(baseDir,nickname,domain,args.availability):
        print('Availablity set to '+args.availability)
    sys.exit()
    
if args.project:
    if not nickname:
        print('No nickname given')
        sys.exit()
        
    if args.role.lower()=='none' or \
       args.role.lower()=='remove' or \
       args.role.lower()=='delete':
        args.role=None
    if args.role:
        if setRole(baseDir,nickname,domain,args.project,args.role):
            print('Role within '+args.project+' set to '+args.role)
    else:
        if setRole(baseDir,nickname,domain,args.project,None):
            print('Left '+args.project)
    sys.exit()

if args.skill:
    if args.skillLevelPercent==0:
        args.skillLevelPercent=None
    if args.skillLevelPercent:
        if setSkillLevel(baseDir,nickname,domain,args.skill,args.skillLevelPercent):
            print('Skill level for '+args.skill+' set to '+str(args.skillLevelPercent)+'%')
    else:
        if setSkillLevel(baseDir,nickname,domain,args.skill,args.skillLevelPercent):
            print('Skill '+args.skill+' removed')
    sys.exit()

if federationList:
    print('Federating with: '+str(federationList))

if not os.path.isdir(baseDir+'/accounts/'+nickname+'@'+domain):
    print('Creating default admin account '+nickname+'@'+domain)
    print('See config.json for the password. You can remove the password from config.json after moving it elsewhere.')
    adminPassword=createPassword(10)
    setConfigParam(baseDir,'adminPassword',adminPassword)
    createPerson(baseDir,nickname,domain,port,httpPrefix,True,adminPassword)

if args.block:
    if not args.nickname:
        print('Please specify a nickname')
        sys.exit()
    if '@' not in args.block:
        print('syntax: --block nickname@domain')
        sys.exit()
    if addBlock(baseDir,args.nickname,domain,args.block.split('@')[0],args.block.split('@')[1].replace('\n','')):
        print(args.block+' is blocked by '+args.nickname)
    sys.exit()

if args.unblock:
    if not args.nickname:
        print('Please specify a nickname')
        sys.exit()
    if '@' not in args.block:
        print('syntax: --unblock nickname@domain')
        sys.exit()
    if removeBlock(baseDir,args.nickname,domain,args.block.split('@')[0],args.block.split('@')[1].replace('\n','')):
        print('The block on '+args.block+' was removed by '+args.nickname)
    sys.exit()

if args.filterStr:
    if not args.nickname:
        print('Please specify a nickname')
        sys.exit()
    if addFilter(baseDir,args.nickname,domain,args.filterStr):
        print('Filter added to '+args.nickname+': '+args.filterStr)
    sys.exit()

if args.unfilterStr:
    if not args.nickname:
        print('Please specify a nickname')
        sys.exit()
    if removeFilter(baseDir,args.nickname,domain,args.unfilterStr):
        print('Filter removed from '+args.nickname+': '+args.unfilterStr)
    sys.exit()

if args.testdata:
    useBlurhash=False    
    nickname='testuser567'
    print('Generating some test data for user: '+nickname)
    createPerson(baseDir,nickname,domain,port,httpPrefix,True,'likewhateveryouwantscoob')
    setSkillLevel(baseDir,nickname,domain,'testing',60)
    setSkillLevel(baseDir,nickname,domain,'typing',50)
    setRole(baseDir,nickname,domain,'epicyon','tester')
    setRole(baseDir,nickname,domain,'epicyon','hacker')
    setRole(baseDir,nickname,domain,'someproject','assistant')
    setAvailability(baseDir,nickname,domain,'busy')
    deleteAllPosts(baseDir,nickname,domain,'inbox')
    deleteAllPosts(baseDir,nickname,domain,'outbox')
    followPerson(baseDir,nickname,domain,'admin',domain,federationList,True)
    followerOfPerson(baseDir,nickname,domain,'admin',domain,federationList,True)
    createPublicPost(baseDir,nickname,domain,port,httpPrefix,"like, this is totally just a test, man",False,True,False,None,None,useBlurhash)
    createPublicPost(baseDir,nickname,domain,port,httpPrefix,"Zoiks!!!",False,True,False,None,None,useBlurhash)
    createPublicPost(baseDir,nickname,domain,port,httpPrefix,"Hey scoob we need like a hundred more milkshakes",False,True,False,None,None,useBlurhash)
    createPublicPost(baseDir,nickname,domain,port,httpPrefix,"Getting kinda spooky around here",False,True,False,None,None,useBlurhash)
    createPublicPost(baseDir,nickname,domain,port,httpPrefix,"And they would have gotten away with it too if it wasn't for those pesky hackers",False,True,False,None,None,useBlurhash)
    createPublicPost(baseDir,nickname,domain,port,httpPrefix,"man, these centralized sites are, like, the worst!",False,True,False,None,None,useBlurhash)
    createPublicPost(baseDir,nickname,domain,port,httpPrefix,"another mystery solved hey",False,True,False,None,None,useBlurhash)
    createPublicPost(baseDir,nickname,domain,port,httpPrefix,"let's go bowling",False,True,False,None,None,useBlurhash)

runDaemon(args.client,baseDir,domain,port,httpPrefix, \
          federationList, \
          args.noreply,args.nolike,args.nopics, \
          args.noannounce,args.cw,ocapAlways, \
          useTor,args.maxReplies, \
          args.domainMaxPostsPerDay,args.accountMaxPostsPerDay, \
          debug)
