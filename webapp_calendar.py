__filename__ = "webapp_calendar.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.2.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Calendar"

import os
from datetime import datetime
from datetime import date
from utils import get_display_name
from utils import get_config_param
from utils import get_nickname_from_actor
from utils import get_domain_from_actor
from utils import locate_post
from utils import load_json
from utils import week_day_of_month_start
from utils import get_alt_path
from utils import remove_domain_port
from utils import acct_dir
from utils import local_actor_url
from utils import replace_users_with_at
from happening import get_todays_events
from happening import get_calendar_events
from webapp_utils import set_custom_background
from webapp_utils import html_header_with_external_style
from webapp_utils import html_footer
from webapp_utils import html_hide_from_screen_reader
from webapp_utils import html_keyboard_navigation


def html_calendar_delete_confirm(css_cache: {}, translate: {}, base_dir: str,
                                 path: str, http_prefix: str,
                                 domain_full: str, post_id: str, postTime: str,
                                 year: int, monthNumber: int,
                                 dayNumber: int, calling_domain: str) -> str:
    """Shows a screen asking to confirm the deletion of a calendar event
    """
    nickname = get_nickname_from_actor(path)
    actor = local_actor_url(http_prefix, nickname, domain_full)
    domain, port = get_domain_from_actor(actor)
    messageId = actor + '/statuses/' + post_id

    post_filename = locate_post(base_dir, nickname, domain, messageId)
    if not post_filename:
        return None

    post_json_object = load_json(post_filename)
    if not post_json_object:
        return None

    delete_postStr = None
    cssFilename = base_dir + '/epicyon-profile.css'
    if os.path.isfile(base_dir + '/epicyon.css'):
        cssFilename = base_dir + '/epicyon.css'

    instanceTitle = \
        get_config_param(base_dir, 'instanceTitle')
    delete_postStr = \
        html_header_with_external_style(cssFilename, instanceTitle, None)
    delete_postStr += \
        '<center><h1>' + postTime + ' ' + str(year) + '/' + \
        str(monthNumber) + \
        '/' + str(dayNumber) + '</h1></center>'
    delete_postStr += '<center>'
    delete_postStr += '  <p class="followText">' + \
        translate['Delete this event'] + '</p>'

    postActor = get_alt_path(actor, domain_full, calling_domain)
    delete_postStr += \
        '  <form method="POST" action="' + postActor + '/rmpost">\n'
    delete_postStr += '    <input type="hidden" name="year" value="' + \
        str(year) + '">\n'
    delete_postStr += '    <input type="hidden" name="month" value="' + \
        str(monthNumber) + '">\n'
    delete_postStr += '    <input type="hidden" name="day" value="' + \
        str(dayNumber) + '">\n'
    delete_postStr += \
        '    <input type="hidden" name="pageNumber" value="1">\n'
    delete_postStr += \
        '    <input type="hidden" name="messageId" value="' + \
        messageId + '">\n'
    delete_postStr += \
        '    <button type="submit" class="button" name="submitYes">' + \
        translate['Yes'] + '</button>\n'
    delete_postStr += \
        '    <a href="' + actor + '/calendar?year=' + \
        str(year) + '?month=' + \
        str(monthNumber) + '"><button class="button">' + \
        translate['No'] + '</button></a>\n'
    delete_postStr += '  </form>\n'
    delete_postStr += '</center>\n'
    delete_postStr += html_footer()
    return delete_postStr


def _html_calendar_day(person_cache: {}, css_cache: {}, translate: {},
                       base_dir: str, path: str,
                       year: int, monthNumber: int, dayNumber: int,
                       nickname: str, domain: str, dayEvents: [],
                       monthName: str, actor: str) -> str:
    """Show a day within the calendar
    """
    accountDir = acct_dir(base_dir, nickname, domain)
    calendarFile = accountDir + '/.newCalendar'
    if os.path.isfile(calendarFile):
        try:
            os.remove(calendarFile)
        except OSError:
            print('EX: _html_calendar_day unable to delete ' + calendarFile)

    cssFilename = base_dir + '/epicyon-calendar.css'
    if os.path.isfile(base_dir + '/calendar.css'):
        cssFilename = base_dir + '/calendar.css'

    calActor = actor
    if '/users/' in actor:
        calActor = '/users/' + actor.split('/users/')[1]

    instanceTitle = get_config_param(base_dir, 'instanceTitle')
    calendarStr = \
        html_header_with_external_style(cssFilename, instanceTitle, None)
    calendarStr += '<main><table class="calendar">\n'
    calendarStr += '<caption class="calendar__banner--month">\n'
    calendarStr += \
        '  <a href="' + calActor + '/calendar?year=' + str(year) + \
        '?month=' + str(monthNumber) + '">\n'
    calendarStr += \
        '  <h1>' + str(dayNumber) + ' ' + monthName + \
        '</h1></a><br><span class="year">' + str(year) + '</span>\n'
    calendarStr += '</caption>\n'
    calendarStr += '<tbody>\n'

    if dayEvents:
        for eventPost in dayEvents:
            eventTime = None
            eventDescription = None
            eventPlace = None
            post_id = None
            senderName = ''
            senderActor = None
            eventIsPublic = False
            # get the time place and description
            for ev in eventPost:
                if ev['type'] == 'Event':
                    if ev.get('post_id'):
                        post_id = ev['post_id']
                    if ev.get('startTime'):
                        eventDate = \
                            datetime.strptime(ev['startTime'],
                                              "%Y-%m-%dT%H:%M:%S%z")
                        eventTime = eventDate.strftime("%H:%M").strip()
                    if 'public' in ev:
                        if ev['public'] is True:
                            eventIsPublic = True
                    if ev.get('sender'):
                        # get display name from sending actor
                        if ev.get('sender'):
                            senderActor = ev['sender']
                            dispName = \
                                get_display_name(base_dir, senderActor,
                                                 person_cache)
                            if dispName:
                                senderName = \
                                    '<a href="' + senderActor + '">' + \
                                    dispName + '</a>: '
                    if ev.get('name'):
                        eventDescription = ev['name'].strip()
                elif ev['type'] == 'Place':
                    if ev.get('name'):
                        eventPlace = ev['name']

            # prepend a link to the sender of the calendar item
            if senderName and eventDescription:
                # if the sender is also mentioned within the event
                # description then this is a reminder
                senderActor2 = replace_users_with_at(senderActor)
                if senderActor not in eventDescription and \
                   senderActor2 not in eventDescription:
                    eventDescription = senderName + eventDescription
                else:
                    eventDescription = \
                        translate['Reminder'] + ': ' + eventDescription

            deleteButtonStr = ''
            if post_id:
                deleteButtonStr = \
                    '<td class="calendar__day__icons"><a href="' + calActor + \
                    '/eventdelete?eventid=' + post_id + \
                    '?year=' + str(year) + \
                    '?month=' + str(monthNumber) + \
                    '?day=' + str(dayNumber) + \
                    '?time=' + eventTime + \
                    '">\n<img class="calendardayicon" loading="lazy" alt="' + \
                    translate['Delete this event'] + ' |" title="' + \
                    translate['Delete this event'] + '" src="/' + \
                    'icons/delete.png" /></a></td>\n'

            eventClass = 'calendar__day__event'
            calItemClass = 'calItem'
            if eventIsPublic:
                eventClass = 'calendar__day__event__public'
                calItemClass = 'calItemPublic'
            if eventTime and eventDescription and eventPlace:
                calendarStr += \
                    '<tr class="' + calItemClass + '">' + \
                    '<td class="calendar__day__time"><b>' + eventTime + \
                    '</b></td><td class="' + eventClass + '">' + \
                    '<span class="place">' + \
                    eventPlace + '</span><br>' + eventDescription + \
                    '</td>' + deleteButtonStr + '</tr>\n'
            elif eventTime and eventDescription and not eventPlace:
                calendarStr += \
                    '<tr class="' + calItemClass + '">' + \
                    '<td class="calendar__day__time"><b>' + eventTime + \
                    '</b></td><td class="' + eventClass + '">' + \
                    eventDescription + '</td>' + deleteButtonStr + '</tr>\n'
            elif not eventTime and eventDescription and not eventPlace:
                calendarStr += \
                    '<tr class="' + calItemClass + '">' + \
                    '<td class="calendar__day__time">' + \
                    '</td><td class="' + eventClass + '">' + \
                    eventDescription + '</td>' + deleteButtonStr + '</tr>\n'
            elif not eventTime and eventDescription and eventPlace:
                calendarStr += \
                    '<tr class="' + calItemClass + '">' + \
                    '<td class="calendar__day__time"></td>' + \
                    '<td class="' + eventClass + '"><span class="place">' + \
                    eventPlace + '</span><br>' + eventDescription + \
                    '</td>' + deleteButtonStr + '</tr>\n'
            elif eventTime and not eventDescription and eventPlace:
                calendarStr += \
                    '<tr class="' + calItemClass + '">' + \
                    '<td class="calendar__day__time"><b>' + eventTime + \
                    '</b></td><td class="' + eventClass + '">' + \
                    '<span class="place">' + \
                    eventPlace + '</span></td>' + \
                    deleteButtonStr + '</tr>\n'

    calendarStr += '</tbody>\n'
    calendarStr += '</table></main>\n'
    calendarStr += html_footer()

    return calendarStr


def html_calendar(person_cache: {}, css_cache: {}, translate: {},
                  base_dir: str, path: str,
                  http_prefix: str, domain_full: str,
                  text_mode_banner: str, accessKeys: {}) -> str:
    """Show the calendar for a person
    """
    domain = remove_domain_port(domain_full)

    monthNumber = 0
    dayNumber = None
    year = 1970
    actor = http_prefix + '://' + domain_full + path.replace('/calendar', '')
    if '?' in actor:
        first = True
        for p in actor.split('?'):
            if not first:
                if '=' in p:
                    if p.split('=')[0] == 'year':
                        numStr = p.split('=')[1]
                        if numStr.isdigit():
                            year = int(numStr)
                    elif p.split('=')[0] == 'month':
                        numStr = p.split('=')[1]
                        if numStr.isdigit():
                            monthNumber = int(numStr)
                    elif p.split('=')[0] == 'day':
                        numStr = p.split('=')[1]
                        if numStr.isdigit():
                            dayNumber = int(numStr)
            first = False
        actor = actor.split('?')[0]

    currDate = datetime.now()
    if year == 1970 and monthNumber == 0:
        year = currDate.year
        monthNumber = currDate.month

    nickname = get_nickname_from_actor(actor)

    set_custom_background(base_dir, 'calendar-background',
                          'calendar-background')

    months = (
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    )
    monthName = translate[months[monthNumber - 1]]

    if dayNumber:
        dayEvents = None
        events = \
            get_todays_events(base_dir, nickname, domain,
                              year, monthNumber, dayNumber)
        if events:
            if events.get(str(dayNumber)):
                dayEvents = events[str(dayNumber)]
        return _html_calendar_day(person_cache, css_cache,
                                  translate, base_dir, path,
                                  year, monthNumber, dayNumber,
                                  nickname, domain, dayEvents,
                                  monthName, actor)

    events = \
        get_calendar_events(base_dir, nickname, domain, year, monthNumber)

    prevYear = year
    prevMonthNumber = monthNumber - 1
    if prevMonthNumber < 1:
        prevMonthNumber = 12
        prevYear = year - 1

    nextYear = year
    nextMonthNumber = monthNumber + 1
    if nextMonthNumber > 12:
        nextMonthNumber = 1
        nextYear = year + 1

    print('Calendar year=' + str(year) + ' month=' + str(monthNumber) +
          ' ' + str(week_day_of_month_start(monthNumber, year)))

    if monthNumber < 12:
        daysInMonth = \
            (date(year, monthNumber + 1, 1) - date(year, monthNumber, 1)).days
    else:
        daysInMonth = \
            (date(year + 1, 1, 1) - date(year, monthNumber, 1)).days
    # print('daysInMonth ' + str(monthNumber) + ': ' + str(daysInMonth))

    cssFilename = base_dir + '/epicyon-calendar.css'
    if os.path.isfile(base_dir + '/calendar.css'):
        cssFilename = base_dir + '/calendar.css'

    calActor = actor
    if '/users/' in actor:
        calActor = '/users/' + actor.split('/users/')[1]

    instanceTitle = \
        get_config_param(base_dir, 'instanceTitle')
    headerStr = \
        html_header_with_external_style(cssFilename, instanceTitle, None)

    # the main graphical calendar as a table
    calendarStr = '<main><table class="calendar">\n'
    calendarStr += '<caption class="calendar__banner--month">\n'
    calendarStr += \
        '  <a href="' + calActor + '/calendar?year=' + str(prevYear) + \
        '?month=' + str(prevMonthNumber) + '" ' + \
        'accesskey="' + accessKeys['Page up'] + '">'
    calendarStr += \
        '  <img loading="lazy" alt="' + translate['Previous month'] + \
        '" title="' + translate['Previous month'] + '" src="/icons' + \
        '/prev.png" class="buttonprev"/></a>\n'
    calendarStr += '  <a href="' + calActor + '/inbox" title="'
    calendarStr += translate['Switch to timeline view'] + '" ' + \
        'accesskey="' + accessKeys['menuTimeline'] + '">'
    calendarStr += '  <h1>' + monthName + '</h1></a>\n'
    calendarStr += \
        '  <a href="' + calActor + '/calendar?year=' + str(nextYear) + \
        '?month=' + str(nextMonthNumber) + '" ' + \
        'accesskey="' + accessKeys['Page down'] + '">'
    calendarStr += \
        '  <img loading="lazy" alt="' + translate['Next month'] + \
        '" title="' + translate['Next month'] + '" src="/icons' + \
        '/prev.png" class="buttonnext"/></a>\n'
    calendarStr += '</caption>\n'
    calendarStr += '<thead>\n'
    calendarStr += '<tr>\n'
    days = ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')
    for d in days:
        calendarStr += '  <th scope="col" class="calendar__day__header">' + \
            translate[d] + '</th>\n'
    calendarStr += '</tr>\n'
    calendarStr += '</thead>\n'
    calendarStr += '<tbody>\n'

    # beginning of the links used for accessibility
    navLinks = {}
    timelineLinkStr = html_hide_from_screen_reader('🏠') + ' ' + \
        translate['Switch to timeline view']
    navLinks[timelineLinkStr] = calActor + '/inbox'

    dayOfMonth = 0
    dow = week_day_of_month_start(monthNumber, year)
    for weekOfMonth in range(1, 7):
        if dayOfMonth == daysInMonth:
            continue
        calendarStr += '  <tr>\n'
        for dayNumber in range(1, 8):
            if (weekOfMonth > 1 and dayOfMonth < daysInMonth) or \
               (weekOfMonth == 1 and dayNumber >= dow):
                dayOfMonth += 1

                isToday = False
                if year == currDate.year:
                    if currDate.month == monthNumber:
                        if dayOfMonth == currDate.day:
                            isToday = True
                if events.get(str(dayOfMonth)):
                    url = calActor + '/calendar?year=' + \
                        str(year) + '?month=' + \
                        str(monthNumber) + '?day=' + str(dayOfMonth)
                    dayDescription = monthName + ' ' + str(dayOfMonth)
                    dayLink = '<a href="' + url + '" ' + \
                        'title="' + dayDescription + '">' + \
                        str(dayOfMonth) + '</a>'
                    # accessibility menu links
                    menuOptionStr = \
                        html_hide_from_screen_reader('📅') + ' ' + \
                        dayDescription
                    navLinks[menuOptionStr] = url
                    # there are events for this day
                    if not isToday:
                        calendarStr += \
                            '    <td class="calendar__day__cell" ' + \
                            'data-event="">' + \
                            dayLink + '</td>\n'
                    else:
                        calendarStr += \
                            '    <td class="calendar__day__cell" ' + \
                            'data-today-event="">' + \
                            dayLink + '</td>\n'
                else:
                    # No events today
                    if not isToday:
                        calendarStr += \
                            '    <td class="calendar__day__cell">' + \
                            str(dayOfMonth) + '</td>\n'
                    else:
                        calendarStr += \
                            '    <td class="calendar__day__cell" ' + \
                            'data-today="">' + str(dayOfMonth) + '</td>\n'
            else:
                calendarStr += '    <td class="calendar__day__cell"></td>\n'
        calendarStr += '  </tr>\n'

    calendarStr += '</tbody>\n'
    calendarStr += '</table></main>\n'

    # end of the links used for accessibility
    nextMonthStr = \
        html_hide_from_screen_reader('→') + ' ' + translate['Next month']
    navLinks[nextMonthStr] = calActor + '/calendar?year=' + str(nextYear) + \
        '?month=' + str(nextMonthNumber)
    prevMonthStr = \
        html_hide_from_screen_reader('←') + ' ' + translate['Previous month']
    navLinks[prevMonthStr] = calActor + '/calendar?year=' + str(prevYear) + \
        '?month=' + str(prevMonthNumber)
    navAccessKeys = {
    }
    screenReaderCal = \
        html_keyboard_navigation(text_mode_banner, navLinks, navAccessKeys,
                                 monthName)

    newEventStr = \
        '<br><center>\n<p>\n' + \
        '<a href="' + calActor + '/newreminder">➕ ' + \
        translate['Add to the calendar'] + '</a>\n</p>\n</center>\n'

    calStr = \
        headerStr + screenReaderCal + calendarStr + newEventStr + html_footer()

    return calStr
