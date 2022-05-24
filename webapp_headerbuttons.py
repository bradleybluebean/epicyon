__filename__ = "webapp_headerbuttons.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.3.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Timeline"


import os
import time
from utils import acct_dir
from datetime import datetime
from datetime import timedelta
from happening import day_events_check
from webapp_utils import html_highlight_label


def header_buttons_timeline(default_timeline: str,
                            box_name: str,
                            page_number: int,
                            translate: {},
                            users_path: str,
                            mediaButton: str,
                            blogs_button: str,
                            features_button: str,
                            news_button: str,
                            inbox_button: str,
                            dm_button: str,
                            new_dm: str,
                            replies_button: str,
                            new_reply: str,
                            minimal: bool,
                            sent_button: str,
                            shares_button_str: str,
                            wanted_button_str: str,
                            bookmarks_button_str: str,
                            events_button_str: str,
                            moderation_button_str: str,
                            new_post_button_str: str,
                            base_dir: str,
                            nickname: str, domain: str,
                            timeline_start_time,
                            new_calendar_event: bool,
                            calendar_path: str,
                            calendar_image: str,
                            follow_approvals: str,
                            icons_as_buttons: bool,
                            access_keys: {}) -> str:
    """Returns the header at the top of the timeline, containing
    buttons for inbox, outbox, search, calendar, etc
    """
    # start of the button header with inbox, outbox, etc
    tl_str = '<div class="containerHeader"><nav>\n'
    # first button
    if default_timeline == 'tlmedia':
        tl_str += \
            '<a href="' + users_path + '/tlmedia" tabindex="-1" ' + \
            'accesskey="' + access_keys['menuMedia'] + '"'
        if box_name == 'tlmedia':
            tl_str += ' aria-current="location"'
        tl_str += \
            '><button class="' + \
            mediaButton + '"><span>' + translate['Media'] + \
            '</span></button></a>'
    elif default_timeline == 'tlblogs':
        tl_str += \
            '<a href="' + users_path + \
            '/tlblogs" tabindex="-1"'
        if box_name == 'tlblogs':
            tl_str += ' aria-current="location"'
        tl_str += \
            '><button class="' + \
            blogs_button + '"><span>' + translate['Blogs'] + \
            '</span></button></a>'
    elif default_timeline == 'tlfeatures':
        tl_str += \
            '<a href="' + users_path + \
            '/tlfeatures" tabindex="-1"'
        if box_name == 'tlfeatures':
            tl_str += ' aria-current="location"'
        tl_str += \
            '><button class="' + \
            features_button + '"><span>' + translate['Features'] + \
            '</span></button></a>'
    else:
        tl_str += \
            '<a href="' + users_path + \
            '/inbox" tabindex="-1"><button class="' + \
            inbox_button + '"'
        if box_name == 'inbox':
            tl_str += ' aria-current="location"'
        tl_str += \
            ' accesskey="' + access_keys['menuInbox'] + '">' + \
            '<span>' + translate['Inbox'] + '</span></button></a>'

    # if this is a news instance and we are viewing the news timeline
    features_header = False
    if default_timeline == 'tlfeatures' and box_name == 'tlfeatures':
        features_header = True

    if not features_header:
        tl_str += \
            '<a href="' + users_path + '/dm" tabindex="-1"'
        if box_name == 'dm':
            tl_str += ' aria-current="location"'
        tl_str += \
            '><button class="' + dm_button + \
            '" accesskey="' + access_keys['menuDM'] + '">' + \
            '<span>' + html_highlight_label(translate['DM'], new_dm) + \
            '</span></button></a>'

        replies_index_filename = \
            acct_dir(base_dir, nickname, domain) + '/tlreplies.index'
        if os.path.isfile(replies_index_filename):
            tl_str += \
                '<a href="' + users_path + '/tlreplies" tabindex="-1"'
            if box_name == 'tlreplies':
                tl_str += ' aria-current="location"'
            tl_str += \
                '><button class="' + replies_button + '" ' + \
                'accesskey="' + access_keys['menuReplies'] + '"><span>' + \
                html_highlight_label(translate['Replies'], new_reply) + \
                '</span></button></a>'

    # typically the media button
    if default_timeline != 'tlmedia':
        if not minimal and not features_header:
            tl_str += \
                '<a href="' + users_path + '/tlmedia" tabindex="-1" ' + \
                'accesskey="' + access_keys['menuMedia'] + '"'
            if box_name == 'tlmedia':
                tl_str += ' aria-current="location"'
            tl_str += \
                '><button class="' + \
                mediaButton + '"><span>' + translate['Media'] + \
                '</span></button></a>'
    else:
        if not minimal:
            tl_str += \
                '<a href="' + users_path + \
                '/inbox" tabindex="-1"'
            if box_name == 'inbox':
                tl_str += ' aria-current="location"'
            tl_str += \
                '><button class="' + \
                inbox_button + '"><span>' + translate['Inbox'] + \
                '</span></button></a>'

    if not features_header:
        # typically the blogs button
        # but may change if this is a blogging oriented instance
        if default_timeline != 'tlblogs':
            if not minimal:
                title_str = translate['Blogs']
                if default_timeline == 'tlfeatures':
                    title_str = translate['Article']
                tl_str += \
                    '<a href="' + users_path + \
                    '/tlblogs" tabindex="-1"'
                if box_name == 'tlblogs':
                    tl_str += ' aria-current="location"'
                tl_str += \
                    '><button class="' + \
                    blogs_button + '"><span>' + title_str + \
                    '</span></button></a>'
        else:
            if not minimal:
                tl_str += \
                    '<a href="' + users_path + \
                    '/inbox" tabindex="-1"'
                if box_name == 'inbox':
                    tl_str += ' aria-current="location"'
                tl_str += \
                    '><button class="' + \
                    inbox_button + '"><span>' + translate['Inbox'] + \
                    '</span></button></a>'

    # typically the news button
    # but may change if this is a news oriented instance
    if default_timeline == 'tlfeatures':
        if not features_header:
            tl_str += \
                '<a href="' + users_path + \
                '/inbox" tabindex="-1"'
            if box_name == 'inbox':
                tl_str += ' aria-current="location"'
            tl_str += \
                '><button class="' + \
                inbox_button + '" accesskey="' + \
                access_keys['menuInbox'] + '"><span>' + translate['Inbox'] + \
                '</span></button></a>'

    # show todays events buttons on the first inbox page
    happening_str = ''
    if box_name == 'inbox' and page_number == 1:
        now = datetime.now()
        tomorrow = datetime.now() + timedelta(1)
        twodays = datetime.now() + timedelta(2)
        if day_events_check(base_dir, nickname, domain, now):
            # happening today button
            if not icons_as_buttons:
                happening_str += \
                    '<a href="' + users_path + '/calendar?year=' + \
                    str(now.year) + '?month=' + str(now.month) + \
                    '?day=' + str(now.day) + '" tabindex="-1">' + \
                    '<button class="buttonevent">' + \
                    translate['Happening Today'] + '</button></a>'
            else:
                happening_str += \
                    '<a href="' + users_path + '/calendar?year=' + \
                    str(now.year) + '?month=' + str(now.month) + \
                    '?day=' + str(now.day) + '" tabindex="-1">' + \
                    '<button class="button">' + \
                    translate['Happening Today'] + '</button></a>'

        elif day_events_check(base_dir, nickname, domain, tomorrow):
            # happening tomorrow button
            if not icons_as_buttons:
                happening_str += \
                    '<a href="' + users_path + '/calendar?year=' + \
                    str(tomorrow.year) + '?month=' + str(tomorrow.month) + \
                    '?day=' + str(tomorrow.day) + '" tabindex="-1">' + \
                    '<button class="buttonevent">' + \
                    translate['Happening Tomorrow'] + '</button></a>'
            else:
                happening_str += \
                    '<a href="' + users_path + '/calendar?year=' + \
                    str(tomorrow.year) + '?month=' + str(tomorrow.month) + \
                    '?day=' + str(tomorrow.day) + '" tabindex="-1">' + \
                    '<button class="button">' + \
                    translate['Happening Tomorrow'] + '</button></a>'
        elif day_events_check(base_dir, nickname, domain, twodays):
            if not icons_as_buttons:
                happening_str += \
                    '<a href="' + users_path + \
                    '/calendar" tabindex="-1">' + \
                    '<button class="buttonevent">' + \
                    translate['Happening This Week'] + '</button></a>'
            else:
                happening_str += \
                    '<a href="' + users_path + \
                    '/calendar" tabindex="-1">' + \
                    '<button class="button">' + \
                    translate['Happening This Week'] + '</button></a>'

    if not features_header:
        # button for the outbox
        tl_str += \
            '<a href="' + users_path + '/outbox"'
        if box_name == 'outbox':
            tl_str += ' aria-current="location"'
        tl_str += \
            '><button class="' + \
            sent_button + '" tabindex="-1" accesskey="' + \
            access_keys['menuOutbox'] + '">' + \
            '<span>' + translate['Sent'] + '</span></button></a>'

        # add other buttons
        tl_str += \
            shares_button_str + wanted_button_str + bookmarks_button_str + \
            events_button_str + \
            moderation_button_str + happening_str + new_post_button_str

    if not features_header:
        if not icons_as_buttons:
            # the search icon
            tl_str += \
                '<a class="imageAnchor" href="' + users_path + \
                '/search"><img loading="lazy" decoding="async" src="/' + \
                'icons/search.png" title="' + \
                translate['Search and follow'] + '" alt="| ' + \
                translate['Search and follow'] + \
                '" class="timelineicon"/></a>'
        else:
            # the search button
            tl_str += \
                '<a href="' + users_path + \
                '/search" tabindex="-1"><button class="button">' + \
                '<span>' + translate['Search'] + \
                '</span></button></a>'

    # benchmark 5
    time_diff = int((time.time() - timeline_start_time) * 1000)
    if time_diff > 100:
        print('TIMELINE TIMING ' + box_name + ' 5 = ' + str(time_diff))

    # the calendar button
    if not features_header:
        calendar_alt_text = translate['Calendar']
        if new_calendar_event:
            # indicate that the calendar icon is highlighted
            calendar_alt_text = '*' + calendar_alt_text + '*'
        if not icons_as_buttons:
            tl_str += \
                '      <a class="imageAnchor" href="' + \
                users_path + calendar_path + \
                '"><img loading="lazy" decoding="async" src="/icons/' + \
                calendar_image + '" title="' + translate['Calendar'] + \
                '" alt="| ' + calendar_alt_text + \
                '" class="timelineicon"/></a>\n'
        else:
            tl_str += \
                '<a href="' + users_path + calendar_path + \
                '" tabindex="-1"><button class="button">' + \
                '<span>' + translate['Calendar'] + \
                '</span></button></a>'

    if not features_header:
        # the show/hide button, for a simpler header appearance
        if not icons_as_buttons:
            tl_str += \
                '      <a class="imageAnchor" href="' + \
                users_path + '/minimal' + \
                '"><img loading="lazy" decoding="async" src="/icons' + \
                '/showhide.png" title="' + translate['Show/Hide Buttons'] + \
                '" alt="| ' + translate['Show/Hide Buttons'] + \
                '" class="timelineicon"/></a>\n'
        else:
            tl_str += \
                '<a href="' + users_path + '/minimal' + \
                '" tabindex="-1"><button class="button">' + \
                '<span>' + translate['Show/Hide Buttons'] + \
                '</span></button></a>'

    if features_header:
        tl_str += \
            '<a href="' + users_path + '/inbox" tabindex="-1"'
        if box_name == 'inbox':
            tl_str += ' aria-current="location"'
        tl_str += \
            '><button class="button">' + \
            '<span>' + translate['User'] + '</span></button></a>'

    # the newswire button to show right column links
    if not icons_as_buttons:
        tl_str += \
            '<a class="imageAnchorMobile" href="' + \
            users_path + '/newswiremobile">' + \
            '<img loading="lazy" decoding="async" src="/icons' + \
            '/newswire.png" title="' + translate['News'] + \
            '" alt="| ' + translate['News'] + \
            '" class="timelineicon"/></a>'
    else:
        # NOTE: deliberately no \n at end of line
        tl_str += \
            '<a href="' + \
            users_path + '/newswiremobile' + \
            '" tabindex="-1"><button class="buttonMobile">' + \
            '<span>' + translate['Newswire'] + \
            '</span></button></a>'

    # the links button to show left column links
    if not icons_as_buttons:
        tl_str += \
            '<a class="imageAnchorMobile" href="' + \
            users_path + '/linksmobile">' + \
            '<img loading="lazy" decoding="async" src="/icons' + \
            '/links.png" title="' + translate['Edit Links'] + \
            '" alt="| ' + translate['Edit Links'] + \
            '" class="timelineicon"/></a>'
    else:
        # NOTE: deliberately no \n at end of line
        tl_str += \
            '<a href="' + \
            users_path + '/linksmobile' + \
            '" tabindex="-1"><button class="buttonMobile">' + \
            '<span>' + translate['Links'] + \
            '</span></button></a>'

    if features_header:
        tl_str += \
            '<a href="' + users_path + '/editprofile" tabindex="-1">' + \
            '<button class="buttonDesktop">' + \
            '<span>' + translate['Settings'] + '</span></button></a>'

    if not features_header:
        tl_str += follow_approvals

    if not icons_as_buttons:
        # end of headericons div
        tl_str += '</div>'

    # end of the button header with inbox, outbox, etc
    tl_str += '    </nav></div>\n'
    return tl_str
