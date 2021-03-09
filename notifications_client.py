__filename__ = "notifications_client.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.2.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@freedombone.net"
__status__ = "Production"

import os
import html
import time
import sys
import select
from session import createSession
from speaker import getSpeakerFromServer
from speaker import getSpeakerPitch
from speaker import getSpeakerRate
from speaker import getSpeakerRange


def _waitForKeypress(timeout: int, debug: bool) -> str:
    """Waits for a keypress with a timeout
    Returns the key pressed, or None on timeout
    """
    i, o, e = select.select([sys.stdin], [], [], timeout)

    if (i):
        text = sys.stdin.readline().strip()
        if debug:
            print("Text entered: " + text)
        return text
    else:
        if debug:
            print("Timeout")
        return None


def _speakerEspeak(espeak, pitch: int, rate: int, srange: int,
                   sayText: str) -> None:
    """Speaks the given text with espeak
    """
    espeak.set_parameter(espeak.Parameter.Pitch, pitch)
    espeak.set_parameter(espeak.Parameter.Rate, rate)
    espeak.set_parameter(espeak.Parameter.Range, srange)
    espeak.synth(html.unescape(sayText))


def _speakerPicospeaker(pitch: int, rate: int, systemLanguage: str,
                        sayText: str) -> None:
    speakerLang = 'en-GB'
    if systemLanguage:
        if systemLanguage.startswith('fr'):
            speakerLang = 'fr-FR'
        elif systemLanguage.startswith('es'):
            speakerLang = 'es-ES'
        elif systemLanguage.startswith('de'):
            speakerLang = 'de-DE'
        elif systemLanguage.startswith('it'):
            speakerLang = 'it-IT'
    speakerCmd = 'picospeaker ' + \
        '-l ' + speakerLang + \
        ' -r ' + str(rate) + \
        ' -p ' + str(pitch) + ' "' + \
        html.unescape(sayText) + '"'
    # print(speakerCmd)
    os.system(speakerCmd)


def _playNotificationSound(soundFilename: str, player='ffplay') -> None:
    """Plays a sound
    """
    if not os.path.isfile(soundFilename):
        return

    if player == 'ffplay':
        os.system('ffplay ' + soundFilename +
                  ' -autoexit -hide_banner -nodisp')


def _desktopNotification(notificationType: str,
                         title: str, message: str)) -> None:
    """Shows a desktop notification
    """
    if not notificationType:
        return

    if notificationType == 'notify-send':
        # Ubuntu
        os.system('notify-send "' + title + '" "' + message + '"')
    elif notificationType == 'osascript':
        # Mac
        os.system("osascript -e 'display notification \"" +
                  message + "\" with title \"" + title + "\"'")
    elif notificationType == 'New-BurntToastNotification':
        # Windows
        os.system("New-BurntToastNotification -Text \"" +
                  title + "\", '" + message + "'")


def runNotificationsClient(baseDir: str, proxyType: str, httpPrefix: str,
                           nickname: str, domain: str, port: int,
                           password: str, screenreader: str,
                           systemLanguage: str, debug: bool) -> None:
    """Runs the notifications and screen reader client,
    which announces new inbox items
    """
    if screenreader:
        if screenreader == 'espeak':
            print('Setting up espeak')
            from espeak import espeak
        elif screenreader != 'picospeaker':
            print(screenreader + ' is not a supported TTS system')
            return

        print('Running ' + screenreader + ' for ' + nickname + '@' + domain)

    prevSay = ''
    prevDM = False
    prevReply = False
    prevCalendar = False
    prevFollow = False
    prevLike = ''
    prevShare = False
    dmSoundFilename = 'dm.ogg'
    replySoundFilename = 'reply.ogg'
    calendarSoundFilename = 'calendar.ogg'
    followSoundFilename = 'follow.ogg'
    likeSoundFilename = 'like.ogg'
    shareSoundFilename = 'share.ogg'
    player = 'ffplay'
    notificationType = 'notify-send'
    instanceTitle = 'Epicyon'
    while (1):
        session = createSession(proxyType)
        speakerJson = \
            getSpeakerFromServer(baseDir, session, nickname, password,
                                 domain, port, httpPrefix, True, __version__)
        if speakerJson:
            if speakerJson.get('notify'):
                soundsDir = 'theme/default/sounds'
                if speakerJson['notify'].get('theme'):
                    soundsDir = \
                        'theme/' + speakerJson['notify']['theme'] + '/sounds'
                    if not os.path.isdir(soundsDir):
                        soundsDir = 'theme/default/sounds'
                if dmSoundFilename:
                    if speakerJson['notify']['dm'] != prevDM:
                        _playNotificationSound(soundsDir + '/' +
                                               dmSoundFilename, player)
                        _desktopNotification(notificationType,
                                             instanceTitle,
                                             'New direct message')
                elif replySoundFilename:
                    if speakerJson['notify']['reply'] != prevReply:
                        _playNotificationSound(soundsDir + '/' +
                                               replySoundFilename, player)
                        _desktopNotification(notificationType,
                                             instanceTitle,
                                             'New reply')
                elif calendarSoundFilename:
                    if speakerJson['notify']['calendar'] != prevCalendar:
                        _playNotificationSound(soundsDir + '/' +
                                               calendarSoundFilename, player)
                        _desktopNotification(notificationType,
                                             instanceTitle,
                                             'New calendar event')
                elif followSoundFilename:
                    if speakerJson['notify']['followRequests'] != prevFollow:
                        _playNotificationSound(soundsDir + '/' +
                                               followSoundFilename, player)
                        _desktopNotification(notificationType,
                                             instanceTitle,
                                             'New follow request')
                elif likeSoundFilename:
                    if speakerJson['notify']['likedBy'] != prevLike:
                        _playNotificationSound(soundsDir + '/' +
                                               likeSoundFilename, player)
                        _desktopNotification(notificationType,
                                             instanceTitle,
                                             'New like')
                elif shareSoundFilename:
                    if speakerJson['notify']['share'] != prevShare:
                        _playNotificationSound(soundsDir + '/' +
                                               shareSoundFilename, player)
                        _desktopNotification(notificationType,
                                             instanceTitle,
                                             'New shared item')

                prevDM = speakerJson['notify']['dm']
                prevReply = speakerJson['notify']['reply']
                prevCalendar = speakerJson['notify']['calendar']
                prevFollow = speakerJson['notify']['followRequests']
                prevLike = speakerJson['notify']['likedBy']
                prevShare = speakerJson['notify']['share']

            if speakerJson.get('say'):
                if speakerJson['say'] != prevSay:
                    if speakerJson.get('name'):
                        nameStr = speakerJson['name']
                        gender = 'They/Them'
                        if speakerJson.get('gender'):
                            gender = speakerJson['gender']

                        # get the speech parameters
                        pitch = getSpeakerPitch(nameStr, screenreader, gender)
                        rate = getSpeakerRate(nameStr, screenreader)
                        srange = getSpeakerRange(nameStr)

                        # say the speaker's name
                        if screenreader == 'espeak':
                            _speakerEspeak(espeak, pitch, rate, srange,
                                           nameStr)
                        elif screenreader == 'picospeaker':
                            _speakerPicospeaker(pitch, rate,
                                                systemLanguage, nameStr)
                        time.sleep(2)

                        # append image description if needed
                        if not speakerJson.get('imageDescription'):
                            sayStr = speakerJson['say']
                            # echo spoken text to the screen
                            print(html.unescape(nameStr) + ': ' +
                                  html.unescape(speakerJson['say']) + '\n')
                        else:
                            sayStr = speakerJson['say'] + '. ' + \
                                speakerJson['imageDescription']
                            # echo spoken text to the screen
                            imageDescription = \
                                html.unescape(speakerJson['imageDescription'])
                            print(html.unescape(nameStr) + ': ' +
                                  html.unescape(speakerJson['say']) + '\n' +
                                  imageDescription)

                        # speak the post content
                        if screenreader == 'espeak':
                            _speakerEspeak(espeak, pitch, rate, srange, sayStr)
                        elif screenreader == 'picospeaker':
                            _speakerPicospeaker(pitch, rate,
                                                systemLanguage, sayStr)

                    prevSay = speakerJson['say']

        # wait for a while, or until a key is pressed
        keyPress = _waitForKeypress(30, debug)
        if keyPress:
            if keyPress.startswith('/'):
                keyPress = keyPress[1:]
            if keyPress == 'q' or keyPress == 'quit' or keyPress == 'exit':
                break
