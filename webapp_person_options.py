__filename__ = "webapp_person_options.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.3.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Web Interface"

import os
from shutil import copyfile
from petnames import get_pet_name
from person import is_person_snoozed
from posts import is_moderator
from utils import get_full_domain
from utils import get_config_param
from utils import is_dormant
from utils import remove_html
from utils import get_domain_from_actor
from utils import get_nickname_from_actor
from utils import is_featured_writer
from utils import acct_dir
from utils import text_in_file
from utils import remove_domain_port
from blocking import is_blocked
from follow import is_follower_of_person
from follow import is_following_actor
from followingCalendar import receiving_calendar_events
from notifyOnPost import notify_when_person_posts
from webapp_utils import html_header_with_external_style
from webapp_utils import html_footer
from webapp_utils import get_broken_link_substitute
from webapp_utils import html_keyboard_navigation
from webapp_utils import get_banner_file
from webapp_utils import html_hide_from_screen_reader
from webapp_utils import minimizing_attached_images
from blocking import allowed_announce


def _minimize_attached_images(base_dir: str, nickname: str, domain: str,
                              following_nickname: str,
                              following_domain: str,
                              add: bool) -> None:
    """Adds or removes a handle from the following.txt list into a list
    indicating whether to minimize images from that account
    """
    # check that a following file exists
    domain = remove_domain_port(domain)
    following_filename = \
        acct_dir(base_dir, nickname, domain) + '/following.txt'
    if not os.path.isfile(following_filename):
        print("WARN: following.txt doesn't exist for " +
              nickname + '@' + domain)
        return
    handle = following_nickname + '@' + following_domain

    # check that you are following this handle
    if not text_in_file(handle + '\n', following_filename):
        print('WARN: ' + handle + ' is not in ' + following_filename)
        return

    minimize_filename = \
        acct_dir(base_dir, nickname, domain) + '/followingMinimizeImages.txt'

    # get the contents of the minimize file, which is
    # a set of handles
    minimize_handles = ''
    if os.path.isfile(minimize_filename):
        print('Minimize file exists')
        try:
            with open(minimize_filename, 'r',
                      encoding='utf-8') as minimize_file:
                minimize_handles = minimize_file.read()
        except OSError:
            print('EX: minimize_attached_images ' + minimize_filename)
    else:
        # create a new minimize file from the following file
        print('Creating minimize file ' + minimize_filename)
        if add:
            try:
                with open(minimize_filename, 'w+',
                          encoding='utf-8') as fp_min:
                    fp_min.write('')
            except OSError:
                print('EX: minimize_attached_images unable to write ' +
                      minimize_filename)

    # already in the minimize file?
    if handle + '\n' in minimize_handles:
        print(handle + ' exists in followingMinimizeImages.txt')
        if add:
            # already added
            return
        # remove from minimize file
        minimize_handles = minimize_handles.replace(handle + '\n', '')
        try:
            with open(minimize_filename, 'w+',
                      encoding='utf-8') as fp_min:
                fp_min.write(minimize_handles)
        except OSError:
            print('EX: minimize_attached_images 3 ' + minimize_filename)
    else:
        print(handle + ' not in followingMinimizeImages.txt')
        # not already in the minimize file
        if add:
            # append to the list of handles
            minimize_handles += handle + '\n'
            try:
                with open(minimize_filename, 'w+',
                          encoding='utf-8') as fp_min:
                    fp_min.write(minimize_handles)
            except OSError:
                print('EX: minimize_attached_images 4 ' + minimize_filename)


def person_minimize_images(base_dir: str, nickname: str, domain: str,
                           following_nickname: str,
                           following_domain: str) -> None:
    """Images from this person are minimized by default
    """
    _minimize_attached_images(base_dir, nickname, domain,
                              following_nickname, following_domain, True)


def person_undo_minimize_images(base_dir: str, nickname: str, domain: str,
                                following_nickname: str,
                                following_domain: str) -> None:
    """Images from this person are no longer minimized by default
    """
    _minimize_attached_images(base_dir, nickname, domain,
                              following_nickname, following_domain, False)


def html_person_options(default_timeline: str,
                        translate: {}, base_dir: str,
                        domain: str, domain_full: str,
                        origin_path_str: str,
                        options_actor: str,
                        options_profile_url: str,
                        options_link: str,
                        page_number: int,
                        donate_url: str,
                        web_address: str,
                        gemini_link: str,
                        xmpp_address: str,
                        matrix_address: str,
                        ssb_address: str,
                        blog_address: str,
                        tox_address: str,
                        briar_address: str,
                        cwtch_address: str,
                        enigma_pub_key: str,
                        pgp_pub_key: str,
                        pgp_fingerprint: str,
                        email_address: str,
                        dormant_months: int,
                        back_to_path: str,
                        locked_account: bool,
                        moved_to: str,
                        also_known_as: [],
                        text_mode_banner: str,
                        news_instance: bool,
                        authorized: bool,
                        access_keys: {},
                        is_group: bool,
                        theme: str) -> str:
    """Show options for a person: view/follow/block/report
    """
    options_domain, options_port = get_domain_from_actor(options_actor)
    if not options_domain:
        return None
    options_domain_full = get_full_domain(options_domain, options_port)

    if os.path.isfile(base_dir + '/accounts/options-background-custom.jpg'):
        if not os.path.isfile(base_dir + '/accounts/options-background.jpg'):
            copyfile(base_dir + '/accounts/options-background.jpg',
                     base_dir + '/accounts/options-background.jpg')

    dormant = False
    follow_str = 'Follow'
    if is_group:
        follow_str = 'Join'
    block_str = 'Block'
    nickname = None
    options_nickname = None
    follows_you = False
    if origin_path_str.startswith('/users/'):
        nickname = origin_path_str.split('/users/')[1]
        if '/' in nickname:
            nickname = nickname.split('/')[0]
        if '?' in nickname:
            nickname = nickname.split('?')[0]
#        follower_domain, follower_port = get_domain_from_actor(options_actor)
        if is_following_actor(base_dir, nickname, domain, options_actor):
            follow_str = 'Unfollow'
            if is_group:
                follow_str = 'Leave'
            dormant = \
                is_dormant(base_dir, nickname, domain, options_actor,
                           dormant_months)

        options_nickname = get_nickname_from_actor(options_actor)
        if not options_nickname:
            return None
        options_domain_full = get_full_domain(options_domain, options_port)
        follows_you = \
            is_follower_of_person(base_dir,
                                  nickname, domain,
                                  options_nickname, options_domain_full)
        if is_blocked(base_dir, nickname, domain,
                      options_nickname, options_domain_full):
            block_str = 'Block'

    options_link_str = ''
    if options_link:
        options_link_str = \
            '    <input type="hidden" name="postUrl" value="' + \
            options_link + '">\n'
    css_filename = base_dir + '/epicyon-options.css'
    if os.path.isfile(base_dir + '/options.css'):
        css_filename = base_dir + '/options.css'

    # To snooze, or not to snooze? That is the question
    snooze_button_str = 'Snooze'
    if nickname:
        if is_person_snoozed(base_dir, nickname, domain, options_actor):
            snooze_button_str = 'Unsnooze'

    donate_str = ''
    if donate_url:
        donate_str = \
            '    <a href="' + donate_url + \
            ' tabindex="-1""><button class="button" name="submitDonate">' + \
            translate['Donate'] + '</button></a>\n'

    instance_title = \
        get_config_param(base_dir, 'instanceTitle')
    options_str = \
        html_header_with_external_style(css_filename, instance_title, None)

    # show banner
    banner_file, _ = \
        get_banner_file(base_dir, nickname, domain, theme)
    back_path = '/'
    if nickname:
        back_path = '/users/' + nickname + '/' + default_timeline
        if 'moderation' in back_to_path:
            back_path = '/users/' + nickname + '/moderation'
    if authorized and origin_path_str == '/users/' + nickname:
        banner_link = back_path
    else:
        banner_link = origin_path_str
    options_str += \
        '<header>\n<a href="' + banner_link + \
        '" title="' + translate['Switch to timeline view'] + '" alt="' + \
        translate['Switch to timeline view'] + '" ' + \
        'tabindex="1" accesskey="' + access_keys['menuTimeline'] + '">\n'
    options_str += \
        '<img loading="lazy" decoding="async" ' + \
        'class="timeline-banner" alt="" ' + \
        'src="/users/' + nickname + '/' + banner_file + '" /></a>\n' + \
        '</header>\n<br><br>\n'

    nav_links = {}
    timeline_link_str = html_hide_from_screen_reader('🏠') + ' ' + \
        translate['Switch to timeline view']
    nav_links[timeline_link_str] = \
        '/users/' + nickname + '/' + default_timeline
    nav_access_keys = {
    }
    options_str += \
        html_keyboard_navigation(text_mode_banner, nav_links, nav_access_keys)

    options_str += '<div class="options">\n'
    options_str += '  <div class="optionsAvatar">\n'
    options_str += '  <center>\n'
    options_str += '  <a href="' + options_actor + '">\n'
    options_str += '  <img loading="lazy" decoding="async" ' + \
        'src="' + options_profile_url + \
        '" alt="" ' + get_broken_link_substitute() + '/></a>\n'
    handle_nick = get_nickname_from_actor(options_actor)
    if not handle_nick:
        return None
    handle = handle_nick + '@' + options_domain
    handle_shown = handle
    if locked_account:
        handle_shown += '🔒'
    if moved_to:
        handle_shown += ' ⌂'
    if dormant:
        handle_shown += ' 💤'
    options_str += \
        '  <p class="optionsText">' + translate['Options for'] + \
        ' @' + handle_shown + '</p>\n'
    if follows_you and authorized:
        options_str += \
            '  <p class="optionsText">' + translate['Follows you'] + '</p>\n'
    if moved_to:
        new_nickname = get_nickname_from_actor(moved_to)
        new_domain, _ = get_domain_from_actor(moved_to)
        if new_nickname and new_domain:
            new_handle = new_nickname + '@' + new_domain
            options_str += \
                '  <p class="optionsText">' + \
                translate['New account'] + \
                ': <a href="' + moved_to + '">@' + new_handle + '</a></p>\n'
    elif also_known_as:
        other_accounts_html = \
            '  <p class="optionsText">' + \
            translate['Other accounts'] + ': '

        ctr = 0
        if isinstance(also_known_as, list):
            for alt_actor in also_known_as:
                if alt_actor == options_actor:
                    continue
                if ctr > 0:
                    other_accounts_html += ' '
                ctr += 1
                alt_domain, _ = get_domain_from_actor(alt_actor)
                other_accounts_html += \
                    '<a href="' + alt_actor + '">' + alt_domain + '</a>'
        elif isinstance(also_known_as, str):
            if also_known_as != options_actor:
                ctr += 1
                alt_domain, _ = get_domain_from_actor(also_known_as)
                other_accounts_html += \
                    '<a href="' + also_known_as + '">' + alt_domain + '</a>'
        other_accounts_html += '</p>\n'
        if ctr > 0:
            options_str += other_accounts_html

    if email_address:
        options_str += \
            '<p class="imText">' + translate['Email'] + \
            ': <a href="mailto:' + \
            email_address + '">' + remove_html(email_address) + '</a></p>\n'
    if web_address:
        web_str = remove_html(web_address)
        if '://' not in web_str:
            web_str = 'https://' + web_str
        options_str += \
            '<p class="imText">🌐 <a href="' + web_str + '">' + \
            web_address + '</a></p>\n'
    if gemini_link:
        gemini_str = remove_html(gemini_link)
        if '://' not in gemini_str:
            gemini_str = 'gemini://' + gemini_str
        options_str += \
            '<p class="imText">♊ <a href="' + gemini_str + '">' + \
            gemini_link + '</a></p>\n'
    if xmpp_address:
        options_str += \
            '<p class="imText">' + translate['XMPP'] + \
            ': <a href="xmpp:' + remove_html(xmpp_address) + '">' + \
            xmpp_address + '</a></p>\n'
    if matrix_address:
        options_str += \
            '<p class="imText">' + translate['Matrix'] + ': ' + \
            remove_html(matrix_address) + '</p>\n'
    if ssb_address:
        options_str += \
            '<p class="imText">SSB: ' + remove_html(ssb_address) + '</p>\n'
    if blog_address:
        options_str += \
            '<p class="imText">Blog: <a href="' + \
            remove_html(blog_address) + '">' + \
            remove_html(blog_address) + '</a></p>\n'
    if tox_address:
        options_str += \
            '<p class="imText">Tox: ' + remove_html(tox_address) + '</p>\n'
    if briar_address:
        if briar_address.startswith('briar://'):
            options_str += \
                '<p class="imText">' + \
                remove_html(briar_address) + '</p>\n'
        else:
            options_str += \
                '<p class="imText">briar://' + \
                remove_html(briar_address) + '</p>\n'
    if cwtch_address:
        options_str += \
            '<p class="imText">Cwtch: ' + remove_html(cwtch_address) + '</p>\n'
    if enigma_pub_key:
        options_str += \
            '<p class="imText">Enigma: ' + \
            remove_html(enigma_pub_key) + '</p>\n'
    if pgp_fingerprint:
        options_str += '<p class="pgp">PGP: ' + \
            remove_html(pgp_fingerprint).replace('\n', '<br>') + '</p>\n'
    if pgp_pub_key:
        options_str += '<p class="pgp">' + \
            remove_html(pgp_pub_key).replace('\n', '<br>') + '</p>\n'
    options_str += '  <form method="POST" action="' + \
        origin_path_str + '/personoptions">\n'
    options_str += '    <input type="hidden" name="pageNumber" value="' + \
        str(page_number) + '">\n'
    options_str += '    <input type="hidden" name="actor" value="' + \
        options_actor + '">\n'
    options_str += '    <input type="hidden" name="avatarUrl" value="' + \
        options_profile_url + '">\n'

    if authorized:
        if origin_path_str == '/users/' + nickname:
            if options_nickname:
                # handle = options_nickname + '@' + options_domain_full
                petname = get_pet_name(base_dir, nickname, domain, handle)
                options_str += \
                    '    ' + translate['Petname'] + ': \n' + \
                    '    <input type="text" name="optionpetname" value="' + \
                    petname + '" ' + \
                    'accesskey="' + access_keys['enterPetname'] + '">\n' \
                    '    <button type="submit" class="buttonsmall" ' + \
                    'name="submitPetname">' + \
                    translate['Save'] + '</button><br>\n'

            # Notify when a post arrives from this person
            if is_following_actor(base_dir, nickname, domain, options_actor):
                checkbox_str = \
                    '    <input type="checkbox" class="profilecheckbox" ' + \
                    'name="allowAnnounce" checked> 🔁' + \
                    translate['Allow announces'] + \
                    '\n    <button type="submit" class="buttonsmall" ' + \
                    'name="submitAllowAnnounce">' + \
                    translate['Save'] + '</button><br>\n'
                if not allowed_announce(base_dir, nickname, domain,
                                        options_nickname, options_domain_full):
                    checkbox_str = checkbox_str.replace(' checked>', '>')
                options_str += checkbox_str

                checkbox_str = \
                    '    <input type="checkbox" class="profilecheckbox" ' + \
                    'name="notifyOnPost" checked> 🔔' + \
                    translate['Notify me when this account posts'] + \
                    '\n    <button type="submit" class="buttonsmall" ' + \
                    'name="submitNotifyOnPost">' + \
                    translate['Save'] + '</button><br>\n'
                if not notify_when_person_posts(base_dir, nickname, domain,
                                                options_nickname,
                                                options_domain_full):
                    checkbox_str = checkbox_str.replace(' checked>', '>')
                options_str += checkbox_str

                checkbox_str = \
                    '    <input type="checkbox" ' + \
                    'class="profilecheckbox" name="onCalendar" checked> ' + \
                    translate['Receive calendar events from this account'] + \
                    '\n    <button type="submit" class="buttonsmall" ' + \
                    'name="submitOnCalendar">' + \
                    translate['Save'] + '</button><br>\n'
                if not receiving_calendar_events(base_dir, nickname, domain,
                                                 options_nickname,
                                                 options_domain_full):
                    checkbox_str = checkbox_str.replace(' checked>', '>')
                options_str += checkbox_str

                checkbox_str = \
                    '    <input type="checkbox" class="profilecheckbox" ' + \
                    'name="minimizeImages" checked> ' + \
                    translate['Minimize attached images'] + \
                    '\n    <button type="submit" class="buttonsmall" ' + \
                    'name="submitMinimizeImages">' + \
                    translate['Save'] + '</button><br>\n'
                if not minimizing_attached_images(base_dir, nickname, domain,
                                                  options_nickname,
                                                  options_domain_full):
                    checkbox_str = checkbox_str.replace(' checked>', '>')
                options_str += checkbox_str

            # checkbox for permission to post to newswire
            newswire_posts_permitted = False
            if options_domain_full == domain_full:
                admin_nickname = get_config_param(base_dir, 'admin')
                if (nickname == admin_nickname or
                    (is_moderator(base_dir, nickname) and
                     not is_moderator(base_dir, options_nickname))):
                    newswire_blocked_filename = \
                        base_dir + '/accounts/' + \
                        options_nickname + '@' + options_domain + \
                        '/.nonewswire'
                    checkbox_str = \
                        '    <input type="checkbox" ' + \
                        'class="profilecheckbox" ' + \
                        'name="postsToNews" checked> ' + \
                        translate['Allow news posts'] + \
                        '\n    <button type="submit" class="buttonsmall" ' + \
                        'name="submitPostToNews">' + \
                        translate['Save'] + '</button><br>\n'
                    if os.path.isfile(newswire_blocked_filename):
                        checkbox_str = checkbox_str.replace(' checked>', '>')
                    else:
                        newswire_posts_permitted = True
                    options_str += checkbox_str

            # whether blogs created by this account are moderated on
            # the newswire
            if newswire_posts_permitted:
                moderated_filename = \
                    base_dir + '/accounts/' + \
                    options_nickname + '@' + \
                    options_domain + '/.newswiremoderated'
                checkbox_str = \
                    '    <input type="checkbox" ' + \
                    'class="profilecheckbox" name="modNewsPosts" checked> ' + \
                    translate['News posts are moderated'] + \
                    '\n    <button type="submit" class="buttonsmall" ' + \
                    'name="submitModNewsPosts">' + \
                    translate['Save'] + '</button><br>\n'
                if not os.path.isfile(moderated_filename):
                    checkbox_str = checkbox_str.replace(' checked>', '>')
                options_str += checkbox_str

            # checkbox for permission to post to featured articles
            if news_instance and options_domain_full == domain_full:
                admin_nickname = get_config_param(base_dir, 'admin')
                if (nickname == admin_nickname or
                    (is_moderator(base_dir, nickname) and
                     not is_moderator(base_dir, options_nickname))):
                    checkbox_str = \
                        '    <input type="checkbox" ' + \
                        'class="profilecheckbox" ' + \
                        'name="postsToFeatures" checked> ' + \
                        translate['Featured writer'] + \
                        '\n    <button type="submit" class="buttonsmall" ' + \
                        'name="submitPostToFeatures">' + \
                        translate['Save'] + '</button><br>\n'
                    if not is_featured_writer(base_dir, options_nickname,
                                              options_domain):
                        checkbox_str = checkbox_str.replace(' checked>', '>')
                    options_str += checkbox_str

    options_str += options_link_str
    if authorized:
        options_str += \
            '    <button type="submit" class="button" ' + \
            'name="submitView" accesskey="' + \
            access_keys['viewButton'] + '">' + \
            translate['View'] + '</button>\n'
    options_str += donate_str
    if authorized:
        options_str += \
            '    <button type="submit" class="button" name="submit' + \
            follow_str + \
            '" accesskey="' + access_keys['followButton'] + '">' + \
            translate[follow_str] + '</button>\n'
        options_str += \
            '    <button type="submit" class="button" name="submitDM" ' + \
            'accesskey="' + access_keys['menuDM'] + '">' + \
            translate['DM'] + '</button>\n'
        options_str += \
            '    <button type="submit" class="button" name="submit' + \
            snooze_button_str + '" accesskey="' + \
            access_keys['snoozeButton'] + '">' + \
            translate[snooze_button_str] + '</button>\n'
        options_str += \
            '    <button type="submit" class="button" ' + \
            'name="submitReport" accesskey="' + \
            access_keys['reportButton'] + '">' + \
            translate['Report'] + '</button>\n'

        if is_moderator(base_dir, nickname):
            options_str += \
                '    <button type="submit" class="button" ' + \
                'name="submitPersonInfo" accesskey="' + \
                access_keys['infoButton'] + '">' + \
                translate['Info'] + '</button>\n'
        options_str += \
            '    <button type="submit" class="button" name="submit' + \
            block_str + '" accesskey="' + access_keys['blockButton'] + '">' + \
            translate[block_str] + '</button>\n'

        person_notes = ''
        if origin_path_str == '/users/' + nickname:
            person_notes_filename = \
                acct_dir(base_dir, nickname, domain) + \
                '/notes/' + handle + '.txt'
            if os.path.isfile(person_notes_filename):
                with open(person_notes_filename, 'r',
                          encoding='utf-8') as fp_notes:
                    person_notes = fp_notes.read()

        options_str += \
            '    <br><br>' + translate['Notes'] + ': \n'
        options_str += '    <button type="submit" class="buttonsmall" ' + \
            'name="submitPersonNotes">' + \
            translate['Save'] + '</button><br>\n'
        options_str += \
            '    <textarea id="message" ' + \
            'name="optionnotes" style="height:400px" spellcheck="true" ' + \
            'accesskey="' + access_keys['enterNotes'] + '">' + \
            person_notes + '</textarea>\n'

    options_str += \
        '  </form>\n' + \
        '</center>\n' + \
        '</div>\n' + \
        '</div>\n'
    options_str += html_footer()
    return options_str
