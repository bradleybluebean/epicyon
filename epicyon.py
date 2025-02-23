__filename__ = "epicyon.py"
__author__ = "Bob Mottram"
__license__ = "AGPL3+"
__version__ = "1.3.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Commandline Interface"

import os
import shutil
import sys
import time
import argparse
import getpass
import datetime
from person import get_actor_json
from person import create_person
from person import create_group
from person import set_profile_image
from person import remove_account
from person import activate_account
from person import deactivate_account
from skills import set_skill_level
from roles import set_role
from webfinger import webfinger_handle
from bookmarks import send_bookmark_via_server
from bookmarks import send_undo_bookmark_via_server
from posts import set_post_expiry_days
from posts import get_instance_actor_key
from posts import send_mute_via_server
from posts import send_undo_mute_via_server
from posts import c2s_box_json
from posts import download_follow_collection
from posts import get_public_post_domains
from posts import get_public_post_domains_blocked
from posts import send_block_via_server
from posts import send_undo_block_via_server
from posts import create_public_post
from posts import delete_all_posts
from posts import expire_posts
from posts import archive_posts
from posts import send_post_via_server
from posts import get_public_posts_of_person
from posts import get_user_url
from posts import check_domains
from session import create_session
from session import get_json
from session import get_vcard
from session import download_html
from session import verify_html
from session import download_ssml
from newswire import get_rss
from filters import add_filter
from filters import remove_filter
from pprint import pprint
from daemon import run_daemon
from follow import get_follow_requests_via_server
from follow import get_following_via_server
from follow import get_followers_via_server
from follow import clear_follows
from follow import add_follower_of_person
from follow import send_follow_request_via_server
from follow import send_unfollow_request_via_server
from tests import test_shared_items_federation
from tests import test_group_follow
from tests import test_post_message_between_servers
from tests import test_follow_between_servers
from tests import test_client_to_server
from tests import test_update_actor
from tests import run_all_tests
from auth import store_basic_credentials
from auth import create_password
from utils import remove_eol
from utils import text_in_file
from utils import remove_domain_port
from utils import get_port_from_domain
from utils import has_users_path
from utils import get_full_domain
from utils import set_config_param
from utils import get_config_param
from utils import get_domain_from_actor
from utils import get_nickname_from_actor
from utils import follow_person
from utils import valid_nickname
from utils import get_protocol_prefixes
from utils import acct_dir
from media import archive_media
from media import get_attachment_media_type
from delete import send_delete_via_server
from like import send_like_via_server
from like import send_undo_like_via_server
from reaction import send_reaction_via_server
from reaction import send_undo_reaction_via_server
from reaction import valid_emoji_content
from skills import send_skill_via_server
from availability import set_availability
from availability import send_availability_via_server
from manualapprove import manual_deny_follow_request
from manualapprove import manual_approve_follow_request
from shares import send_share_via_server
from shares import send_undo_share_via_server
from shares import send_wanted_via_server
from shares import send_undo_wanted_via_server
from shares import add_share
from theme import set_theme
from announce import send_announce_via_server
from socnet import instances_graph
from migrate import migrate_accounts
from desktop_client import run_desktop_client
from happening import dav_month_via_server
from happening import dav_day_via_server
from content import import_emoji


def str2bool(value_str) -> bool:
    """Returns true if the given value is a boolean
    """
    if isinstance(value_str, bool):
        return value_str
    if value_str.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    if value_str.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    raise argparse.ArgumentTypeError('Boolean value expected.')


def _command_options() -> None:
    """Parse the command options
    """
    opt = {}
    search_date = datetime.datetime.now()
    parser = argparse.ArgumentParser(description='ActivityPub Server')
    parser.add_argument('--eventDate', type=str,
                        default=None,
                        help='Date for an event when sending a c2s post' +
                        ' YYYY-MM-DD')
    parser.add_argument('--eventTime', type=str,
                        default=None,
                        help='Time for an event when sending a c2s post' +
                        ' HH:MM')
    parser.add_argument('--eventEndTime', type=str,
                        default=None,
                        help='Time when an event ends when sending a ' +
                        'c2s post HH:MM')
    parser.add_argument('--eventLocation', type=str,
                        default=None,
                        help='Location for an event when sending a c2s post')
    parser.add_argument('--content_license_url', type=str,
                        default='https://creativecommons.org/licenses/by/4.0',
                        help='Url of the license used for the ' +
                        'instance content')
    parser.add_argument('--import_emoji', type=str,
                        default='',
                        help='Import emoji dict from the given filename')
    parser.add_argument('--lists_enabled', type=str,
                        default=None,
                        help='Names of content warning lists enabled. ' +
                        'See the cwlists directory')
    parser.add_argument('--userAgentBlocks', type=str,
                        default=None,
                        help='List of blocked user agents, separated ' +
                        'by commas')
    parser.add_argument('--crawlersAllowed', type=str,
                        default=None,
                        help='List of permitted web crawler user agents, ' +
                        'separated by commas')
    parser.add_argument('--libretranslate', dest='libretranslateUrl', type=str,
                        default=None,
                        help='URL for LibreTranslate service')
    parser.add_argument('--conversationId', dest='conversationId', type=str,
                        default=None,
                        help='Conversation Id which can be added ' +
                        'when sending a post')
    parser.add_argument('--libretranslateApiKey',
                        dest='libretranslateApiKey', type=str,
                        default=None,
                        help='API key for LibreTranslate service')
    parser.add_argument('--defaultCurrency', dest='defaultCurrency', type=str,
                        default=None,
                        help='Default currency EUR/GBP/USD...')
    parser.add_argument('-n', '--nickname', dest='nickname', type=str,
                        default=None,
                        help='Nickname of the account to use')
    parser.add_argument('--screenreader', dest='screenreader', type=str,
                        default=None,
                        help='Name of the screen reader: ' +
                        'espeak/picospeaker/mimic3')
    parser.add_argument('--clacks', dest='clacks', type=str,
                        default=None,
                        help='http header clacks overhead')
    parser.add_argument('--fol', '--follow', dest='follow', type=str,
                        default=None,
                        help='Handle of account to follow. eg. ' +
                        'nickname@domain')
    parser.add_argument('--unfol', '--unfollow', dest='unfollow', type=str,
                        default=None,
                        help='Handle of account stop following. ' +
                        'eg. nickname@domain')
    parser.add_argument('-d', '--domain', dest='domain', type=str,
                        default=None,
                        help='Domain name of the server')
    parser.add_argument('--notificationType', '--notifyType',
                        dest='notificationType', type=str,
                        default='notify-send',
                        help='Type of desktop notification command: ' +
                        'notify-send/zenity/osascript/' +
                        'New-BurntToastNotification')
    parser.add_argument('-o', '--onion', dest='onion', type=str,
                        default=None,
                        help='Onion domain name of the server if ' +
                        'primarily on clearnet')
    parser.add_argument('--i2p_domain', dest='i2p_domain', type=str,
                        default=None,
                        help='i2p domain name of the server if ' +
                        'primarily on clearnet')
    parser.add_argument('-p', '--port', dest='port', type=int,
                        default=None,
                        help='Port number to run on')
    parser.add_argument('--expiryDays', dest='expiryDays', type=int,
                        default=None,
                        help='Number of days after which posts expire ' +
                        'for the given account')
    parser.add_argument('--check-actor-timeout', dest='check_actor_timeout',
                        type=int, default=2,
                        help='Timeout in seconds used for checking is ' +
                        'an actor has changed when clicking their ' +
                        'avatar image')
    parser.add_argument('--year', dest='year', type=int,
                        default=search_date.year,
                        help='Year for calendar query')
    parser.add_argument('--month', dest='month', type=int,
                        default=search_date.month,
                        help='Month for calendar query')
    parser.add_argument('--day', dest='day', type=int,
                        default=None,
                        help='Day for calendar query')
    parser.add_argument('--postsPerSource',
                        dest='max_newswire_posts_per_source', type=int,
                        default=4,
                        help='Maximum newswire posts per feed or account')
    parser.add_argument('--dormant_months',
                        dest='dormant_months', type=int,
                        default=3,
                        help='How many months does a followed account need ' +
                        'to be unseen for before being considered dormant')
    parser.add_argument('--default_reply_interval_hrs',
                        dest='default_reply_interval_hrs', type=int,
                        default=1000,
                        help='How many hours after publication of a post ' +
                        'are replies to it permitted')
    parser.add_argument('--send_threads_timeout_mins',
                        dest='send_threads_timeout_mins', type=int,
                        default=30,
                        help='How many minutes before a thread to send out ' +
                        'posts expires')
    parser.add_argument('--max_newswire_posts',
                        dest='max_newswire_posts', type=int,
                        default=20,
                        help='Maximum newswire posts in the right column')
    parser.add_argument('--maxFeedSize',
                        dest='max_newswire_feed_size_kb', type=int,
                        default=10240,
                        help='Maximum newswire rss/atom feed size in K')
    parser.add_argument('--max_feed_item_size_kb',
                        dest='max_feed_item_size_kb', type=int,
                        default=2048,
                        help='Maximum size of an individual rss/atom ' +
                        'feed item in K')
    parser.add_argument('--max_mirrored_articles',
                        dest='max_mirrored_articles', type=int,
                        default=100,
                        help='Maximum number of news articles to mirror.' +
                        ' Set to zero for indefinite mirroring.')
    parser.add_argument('--max_news_posts',
                        dest='max_news_posts', type=int,
                        default=0,
                        help='Maximum number of news timeline posts ' +
                        'to keep. Zero for no expiry.')
    parser.add_argument('--max_followers',
                        dest='max_followers', type=int,
                        default=2000,
                        help='Maximum number of followers per account. ' +
                        'Zero for no limit.')
    parser.add_argument('--followers',
                        dest='followers', type=str,
                        default='',
                        help='Show list of followers for the given actor')
    parser.add_argument('--postcache', dest='max_recent_posts', type=int,
                        default=512,
                        help='The maximum number of recent posts to ' +
                        'store in RAM')
    parser.add_argument('--proxy', dest='proxy_port', type=int, default=None,
                        help='Proxy port number to run on')
    parser.add_argument('--path', dest='base_dir',
                        type=str, default=os.getcwd(),
                        help='Directory in which to store posts')
    parser.add_argument('--podcast-formats', dest='podcast_formats',
                        type=str, default=None,
                        help='Preferred podcast formats separated ' +
                        'by commas. eg. "opus, mp3, spx"')
    parser.add_argument('--ytdomain', dest='yt_replace_domain',
                        type=str, default=None,
                        help='Domain used to replace youtube.com')
    parser.add_argument('--twitterdomain', dest='twitter_replacement_domain',
                        type=str, default=None,
                        help='Domain used to replace twitter.com')
    parser.add_argument('--language', dest='language',
                        type=str, default=None,
                        help='Specify a single language code, ' +
                        'eg. "en" or "fr" or "de"')
    parser.add_argument('--languagesUnderstood', dest='languages_understood',
                        type=str, default=None,
                        help='List of the default languages understood eg. ' +
                        '"en / fr"')
    parser.add_argument('-a', '--addaccount', dest='addaccount',
                        type=str, default=None,
                        help='Adds a new account')
    parser.add_argument('-g', '--addgroup', dest='addgroup',
                        type=str, default=None,
                        help='Adds a new group')
    parser.add_argument('--activate', dest='activate',
                        type=str, default=None,
                        help='Activate a previously deactivated account')
    parser.add_argument('--deactivate', dest='deactivate',
                        type=str, default=None,
                        help='Deactivate an account')
    parser.add_argument('-r', '--rmaccount', dest='rmaccount',
                        type=str, default=None,
                        help='Remove an account')
    parser.add_argument('--rmgroup', dest='rmgroup',
                        type=str, default=None,
                        help='Remove a group')
    parser.add_argument('--pass', '--password', dest='password',
                        type=str, default=None,
                        help='Set a password for an account')
    parser.add_argument('--chpass', '--changepassword',
                        nargs='+', dest='changepassword',
                        help='Change the password for an account')
    parser.add_argument('--actor', dest='actor', type=str,
                        default=None,
                        help='Show the json actor the given handle')
    parser.add_argument('--posts', dest='posts', type=str,
                        default=None,
                        help='Show posts for the given handle')
    parser.add_argument('--postDomains', dest='postDomains', type=str,
                        default=None,
                        help='Show domains referenced in public '
                        'posts for the given handle')
    parser.add_argument('--postDomainsBlocked', dest='postDomainsBlocked',
                        type=str, default=None,
                        help='Show blocked domains referenced in public '
                        'posts for the given handle')
    parser.add_argument('--check_domains', dest='check_domains', type=str,
                        default=None,
                        help='Check domains of non-mutual followers for '
                        'domains which are globally blocked by this instance')
    parser.add_argument('--socnet', dest='socnet', type=str,
                        default=None,
                        help='Show dot diagram for social network '
                        'of federated instances')
    parser.add_argument('--postsraw', dest='postsraw', type=str,
                        default=None,
                        help='Show raw json of posts for the given handle')
    parser.add_argument('--vcard', dest='vcard', type=str, default=None,
                        help='Show the vcard for a given activitypub ' +
                        'actor url')
    parser.add_argument('--xmlvcard', dest='xmlvcard', type=str, default=None,
                        help='Show the xml vcard for a given ' +
                        'activitypub actor url')
    parser.add_argument('--json', dest='json', type=str, default=None,
                        help='Show the json for a given activitypub url')
    parser.add_argument('--ssml', dest='ssml', type=str, default=None,
                        help='Show the SSML for a given activitypub url')
    parser.add_argument('--htmlpost', dest='htmlpost', type=str, default=None,
                        help='Show the html for a given activitypub url')
    parser.add_argument('--verifyurl', dest='verifyurl', type=str,
                        default=None,
                        help='Verify an identity using the given url')
    parser.add_argument('--rss', dest='rss', type=str, default=None,
                        help='Show an rss feed for a given url')
    parser.add_argument('-f', '--federate', nargs='+', dest='federation_list',
                        help='Specify federation list separated by spaces')
    parser.add_argument('--federateshares', nargs='+',
                        dest='shared_items_federated_domains',
                        help='Specify federation list for shared items, ' +
                        'separated by spaces')
    parser.add_argument("--following", "--followingList",
                        dest='followingList',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Get the following list. Use nickname and " +
                        "domain options to specify the account")
    parser.add_argument("--followersList",
                        dest='followersList',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Get the followers list. Use nickname and " +
                        "domain options to specify the account")
    parser.add_argument("--followRequestsList",
                        dest='followRequestsList',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Get the follow requests list. Use nickname " +
                        "and domain options to specify the account")
    parser.add_argument("--repliesEnabled", "--commentsEnabled",
                        dest='commentsEnabled',
                        type=str2bool, nargs='?',
                        const=True, default=True,
                        help="Enable replies to a post")
    parser.add_argument("--dav",
                        dest='dav',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Caldav")
    parser.add_argument("--show_publish_as_icon",
                        dest='show_publish_as_icon',
                        type=str2bool, nargs='?',
                        const=True, default=True,
                        help="Whether to show newswire publish " +
                        "as an icon or a button")
    parser.add_argument("--full_width_tl_button_header",
                        dest='full_width_tl_button_header',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Whether to show the timeline " +
                        "button header containing inbox and outbox " +
                        "as the full width of the screen")
    parser.add_argument("--icons_as_buttons",
                        dest='icons_as_buttons',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Show header icons as buttons")
    parser.add_argument("--log_login_failures",
                        dest='log_login_failures',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Whether to log longin failures")
    parser.add_argument("--rss_icon_at_top",
                        dest='rss_icon_at_top',
                        type=str2bool, nargs='?',
                        const=True, default=True,
                        help="Whether to show the rss icon at the top or " +
                        "bottom of the timeline")
    parser.add_argument("--low_bandwidth",
                        dest='low_bandwidth',
                        type=str2bool, nargs='?',
                        const=True, default=True,
                        help="Whether to use low bandwidth images")
    parser.add_argument("--publish_button_at_top",
                        dest='publish_button_at_top',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Whether to show the publish button at the " +
                        "top of the newswire column")
    parser.add_argument("--allow_local_network_access",
                        dest='allow_local_network_access',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Whether to allow access to local network " +
                        "addresses. This might be useful when deploying in " +
                        "a mesh network")
    parser.add_argument("--verify_all_signatures",
                        dest='verify_all_signatures',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Whether to require that all incoming " +
                        "posts have valid jsonld signatures")
    parser.add_argument("--broch_mode",
                        dest='broch_mode',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Enable broch mode")
    parser.add_argument("--dyslexic_font",
                        dest='dyslexic_font',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Use dyslexic font")
    parser.add_argument("--nodeinfoaccounts",
                        dest='show_node_info_accounts',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Show numbers of accounts within nodeinfo " +
                        "metadata")
    parser.add_argument("--nodeinfoversion",
                        dest='show_node_info_version',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Show version number within nodeinfo metadata")
    parser.add_argument("--noKeyPress",
                        dest='noKeyPress',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Notification daemon does not wait for " +
                        "keypresses")
    parser.add_argument("--notifyShowNewPosts",
                        dest='notifyShowNewPosts',
                        type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Desktop client shows/speaks new posts " +
                        "as they arrive")
    parser.add_argument("--noapproval", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Allow followers without approval")
    parser.add_argument("--mediainstance", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Media Instance - favor media over text")
    parser.add_argument("--dateonly", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Only show the date at the bottom of posts")
    parser.add_argument("--blogsinstance", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Blogs Instance - favor blogs over microblogging")
    parser.add_argument("--newsinstance", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="News Instance - favor news over microblogging")
    parser.add_argument("--positivevoting", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="On newswire, whether moderators vote " +
                        "positively for or veto against items")
    parser.add_argument("--debug", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Show debug messages")
    parser.add_argument("--notificationSounds", type=str2bool, nargs='?',
                        const=True, default=True,
                        help="Play notification sounds")
    parser.add_argument("--secure_mode", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Requires all GET requests to be signed, " +
                        "so that the sender can be identifies and " +
                        "blocked  if neccessary")
    parser.add_argument("--instance_only_skills_search", type=str2bool,
                        nargs='?', const=True, default=False,
                        help="Skills searches only return " +
                        "results from this instance")
    parser.add_argument("--http", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Use http only")
    parser.add_argument("--gnunet", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Use gnunet protocol only")
    parser.add_argument("--ipfs", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Use ipfs protocol only")
    parser.add_argument("--ipns", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Use ipns protocol only")
    parser.add_argument("--dat", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Use dat protocol only")
    parser.add_argument("--hyper", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Use hypercore protocol only")
    parser.add_argument("--i2p", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Use i2p protocol only")
    parser.add_argument("--tor", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Route via Tor")
    parser.add_argument("--migrations", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Migrate moved accounts")
    parser.add_argument("--tests", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Run unit tests")
    parser.add_argument("--testsnetwork", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Run network unit tests")
    parser.add_argument("--testdata", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Generate some data for testing purposes")
    parser.add_argument('--icon', '--avatar', dest='avatar', type=str,
                        default=None,
                        help='Set the avatar filename for an account')
    parser.add_argument('--image', '--background', dest='backgroundImage',
                        type=str, default=None,
                        help='Set the profile background image for an account')
    parser.add_argument('--archive', dest='archive', type=str,
                        default=None,
                        help='Archive old files to the given directory')
    parser.add_argument('--archiveweeks', dest='archiveWeeks', type=int,
                        default=0,
                        help='Specify the number of weeks after which ' +
                        'media will be archived')
    parser.add_argument('--maxposts', dest='archiveMaxPosts', type=int,
                        default=32000,
                        help='Maximum number of posts in in/outbox')
    parser.add_argument('--maxCacheAgeDays', dest='maxCacheAgeDays', type=int,
                        default=30,
                        help='Maximum age of files in the announce cache')
    parser.add_argument('--minimumvotes', dest='minimumvotes', type=int,
                        default=1,
                        help='Minimum number of votes to remove or add' +
                        ' a newswire item')
    parser.add_argument('--max_like_count', dest='max_like_count', type=int,
                        default=10,
                        help='Maximum number of likes displayed on a post')
    parser.add_argument('--max_hashtags', dest='max_hashtags', type=int,
                        default=20,
                        help='Maximum number of hashtags on a post')
    parser.add_argument('--votingtime', dest='votingtime', type=int,
                        default=1440,
                        help='Time to vote on newswire items in minutes')
    parser.add_argument('--message', dest='message', type=str,
                        default=None,
                        help='Message content')
    parser.add_argument('--delete', dest='delete', type=str,
                        default=None,
                        help='Delete a specified post')
    parser.add_argument("--allowdeletion", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Do not allow deletions")
    parser.add_argument('--repeat', '--announce', dest='announce', type=str,
                        default=None,
                        help='Announce/repeat a url')
    parser.add_argument('--box', type=str,
                        default=None,
                        help='Returns the json for a given timeline, ' +
                        'with authentication')
    parser.add_argument('--page', '--pageNumber', dest='pageNumber', type=int,
                        default=1,
                        help='Page number when using the --box option')
    parser.add_argument('--favorite', '--like', dest='like', type=str,
                        default=None, help='Like a url')
    parser.add_argument('--undolike', '--unlike', dest='undolike', type=str,
                        default=None, help='Undo a like of a url')
    parser.add_argument('--react', '--reaction', dest='react', type=str,
                        default=None, help='Reaction url')
    parser.add_argument('--emoji', type=str,
                        default=None, help='Reaction emoji')
    parser.add_argument('--undoreact', '--undoreaction', dest='undoreact',
                        type=str,
                        default=None, help='Reaction url')
    parser.add_argument('--bookmark', '--bm', dest='bookmark', type=str,
                        default=None,
                        help='Bookmark the url of a post')
    parser.add_argument('--unbookmark', '--unbm', dest='unbookmark', type=str,
                        default=None,
                        help='Undo a bookmark given the url of a post')
    parser.add_argument('--sendto', dest='sendto', type=str,
                        default=None, help='Address to send a post to')
    parser.add_argument('--attach', dest='attach', type=str,
                        default=None, help='File to attach to a post')
    parser.add_argument('--imagedescription', dest='imageDescription',
                        type=str, default=None,
                        help='Description of an attached image')
    parser.add_argument('--city', dest='city', type=str,
                        default='London, England',
                        help='Spoofed city for image metadata misdirection')
    parser.add_argument('--warning', '--warn', '--cwsubject', '--subject',
                        dest='subject', type=str, default=None,
                        help='Subject of content warning')
    parser.add_argument('--reply', '--replyto', dest='replyto', type=str,
                        default=None, help='Url of post to reply to')
    parser.add_argument("--followersonly", type=str2bool, nargs='?',
                        const=True, default=True,
                        help="Send to followers only")
    parser.add_argument("--followerspending", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Show a list of followers pending")
    parser.add_argument('--approve', dest='approve', type=str, default=None,
                        help='Approve a follow request')
    parser.add_argument('--deny', dest='deny', type=str, default=None,
                        help='Deny a follow request')
    parser.add_argument("-c", "--client", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Use as an ActivityPub client")
    parser.add_argument('--maxreplies', dest='max_replies', type=int,
                        default=64,
                        help='Maximum number of replies to a post')
    parser.add_argument('--max_mentions', '--hellthread', dest='max_mentions',
                        type=int, default=10,
                        help='Maximum number of mentions within a post')
    parser.add_argument('--max_emoji', '--maxemoji', dest='max_emoji',
                        type=int, default=10,
                        help='Maximum number of emoji within a post')
    parser.add_argument('--role', dest='role', type=str, default=None,
                        help='Set a role for a person')
    parser.add_argument('--skill', dest='skill', type=str, default=None,
                        help='Set a skill for a person')
    parser.add_argument('--level', dest='skillLevelPercent', type=int,
                        default=None,
                        help='Set a skill level for a person as a ' +
                        'percentage, or zero to remove')
    parser.add_argument('--status', '--availability', dest='availability',
                        type=str, default=None,
                        help='Set an availability status')
    parser.add_argument('--desktop', dest='desktop',
                        type=str, default=None,
                        help='Run desktop client')
    parser.add_argument('--block', dest='block', type=str, default=None,
                        help='Block a particular address')
    parser.add_argument('--unblock', dest='unblock', type=str, default=None,
                        help='Remove a block on a particular address')
    parser.add_argument('--mute', dest='mute', type=str, default=None,
                        help='Mute a particular post URL')
    parser.add_argument('--unmute', dest='unmute', type=str, default=None,
                        help='Unmute a particular post URL')
    parser.add_argument('--filter', dest='filterStr', type=str, default=None,
                        help='Adds a word or phrase which if present will ' +
                        'cause a message to be ignored')
    parser.add_argument('--unfilter', dest='unfilterStr', type=str,
                        default=None,
                        help='Remove a filter on a particular word or phrase')
    parser.add_argument('--domainmax', dest='domain_max_posts_per_day',
                        type=int, default=8640,
                        help='Maximum number of received posts ' +
                        'from a domain per day')
    parser.add_argument('--accountmax', dest='account_max_posts_per_day',
                        type=int, default=8640,
                        help='Maximum number of received posts ' +
                        'from an account per day')
    parser.add_argument('--itemName', dest='itemName', type=str,
                        default=None,
                        help='Name of an item being shared')
    parser.add_argument('--undoItemName', dest='undoItemName', type=str,
                        default=None,
                        help='Name of an shared item to remove')
    parser.add_argument('--wantedItemName', dest='wantedItemName', type=str,
                        default=None,
                        help='Name of a wanted item')
    parser.add_argument('--undoWantedItemName', dest='undoWantedItemName',
                        type=str, default=None,
                        help='Name of a wanted item to remove')
    parser.add_argument('--summary', dest='summary', type=str,
                        default=None,
                        help='Description of an item being shared')
    parser.add_argument('--itemImage', dest='itemImage', type=str,
                        default=None,
                        help='Filename of an image for an item being shared')
    parser.add_argument('--itemQty', dest='itemQty', type=float,
                        default=1,
                        help='Quantity of items being shared')
    parser.add_argument('--itemPrice', dest='itemPrice', type=str,
                        default="0.00",
                        help='Total price of items being shared')
    parser.add_argument('--itemCurrency', dest='itemCurrency', type=str,
                        default="EUR",
                        help='Currency of items being shared')
    parser.add_argument('--itemType', dest='itemType', type=str,
                        default=None,
                        help='Type of item being shared')
    parser.add_argument('--itemCategory', dest='itemCategory', type=str,
                        default=None,
                        help='Category of item being shared')
    parser.add_argument('--location', dest='location', type=str, default=None,
                        help='Location/City of item being shared')
    parser.add_argument('--mapFormat', dest='mapFormat', type=str,
                        default='kml',
                        help='Format for hashtag maps GPX/KML')
    parser.add_argument('--duration', dest='duration', type=str, default=None,
                        help='Duration for which to share an item')
    parser.add_argument('--registration', dest='registration', type=str,
                        default='open',
                        help='Whether new registrations are open or closed')
    parser.add_argument("--nosharedinbox", type=str2bool, nargs='?',
                        const=True, default=False,
                        help='Disable shared inbox')
    parser.add_argument('--maxregistrations', dest='maxRegistrations',
                        type=int, default=10,
                        help='The maximum number of new registrations')
    parser.add_argument("--resetregistrations", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Reset the number of remaining registrations")

    argb = parser.parse_args()

    debug = False
    if argb.debug:
        debug = True
    else:
        if os.path.isfile('debug'):
            debug = True

    if argb.tests:
        run_all_tests()
        sys.exit()
    if argb.testsnetwork:
        print('Network Tests')
        base_dir = os.getcwd()
        test_shared_items_federation(base_dir)
        test_group_follow(base_dir)
        test_post_message_between_servers(base_dir)
        test_follow_between_servers(base_dir)
        test_client_to_server(base_dir)
        test_update_actor(base_dir)
        print('All tests succeeded')
        sys.exit()

    http_prefix = 'https'
    if argb.http or argb.i2p:
        http_prefix = 'http'
    elif argb.ipfs:
        http_prefix = 'ipfs'
    elif argb.ipns:
        http_prefix = 'ipns'
    elif argb.gnunet:
        http_prefix = 'gnunet'

    base_dir = argb.base_dir
    if base_dir.endswith('/'):
        print("--path option should not end with '/'")
        sys.exit()

    if argb.import_emoji:
        import_filename = argb.import_emoji
        print('Importing custom emoji from ' + import_filename)
        session = create_session(None)
        import_emoji(base_dir, import_filename, session)
        sys.exit()

    # automatic translations
    if argb.libretranslateUrl:
        if '://' in argb.libretranslateUrl and \
           '.' in argb.libretranslateUrl:
            set_config_param(base_dir, 'libretranslateUrl',
                             argb.libretranslateUrl)
    if argb.libretranslateApiKey:
        set_config_param(base_dir, 'libretranslateApiKey',
                         argb.libretranslateApiKey)

    if argb.posts:
        if not argb.domain:
            origin_domain = get_config_param(base_dir, 'domain')
        else:
            origin_domain = argb.domain
        if debug:
            print('origin_domain: ' + str(origin_domain))
        if '@' not in argb.posts:
            if '/users/' in argb.posts:
                posts_nickname = get_nickname_from_actor(argb.posts)
                posts_domain, posts_port = get_domain_from_actor(argb.posts)
                argb.posts = \
                    get_full_domain(posts_nickname + '@' + posts_domain,
                                    posts_port)
            else:
                print('Syntax: --posts nickname@domain')
                sys.exit()
        if not argb.http:
            argb.port = 443
        nickname = argb.posts.split('@')[0]
        domain = argb.posts.split('@')[1]
        proxy_type = None
        if argb.tor or domain.endswith('.onion'):
            proxy_type = 'tor'
            if domain.endswith('.onion'):
                argb.port = 80
        elif argb.i2p or domain.endswith('.i2p'):
            proxy_type = 'i2p'
            if domain.endswith('.i2p'):
                argb.port = 80
        elif argb.gnunet:
            proxy_type = 'gnunet'
        if not argb.language:
            argb.language = 'en'
        signing_priv_key_pem = get_instance_actor_key(base_dir, origin_domain)
        get_public_posts_of_person(base_dir, nickname, domain, False, True,
                                   proxy_type, argb.port, http_prefix, debug,
                                   __version__, argb.language,
                                   signing_priv_key_pem, origin_domain)
        sys.exit()

    if argb.postDomains:
        if '@' not in argb.postDomains:
            if '/users/' in argb.postDomains:
                posts_nickname = get_nickname_from_actor(argb.postDomains)
                posts_domain, posts_port = \
                    get_domain_from_actor(argb.postDomains)
                argb.postDomains = \
                    get_full_domain(posts_nickname + '@' + posts_domain,
                                    posts_port)
            else:
                print('Syntax: --postDomains nickname@domain')
                sys.exit()
        if not argb.http:
            argb.port = 443
        nickname = argb.postDomains.split('@')[0]
        domain = argb.postDomains.split('@')[1]
        proxy_type = None
        if argb.tor or domain.endswith('.onion'):
            proxy_type = 'tor'
            if domain.endswith('.onion'):
                argb.port = 80
        elif argb.i2p or domain.endswith('.i2p'):
            proxy_type = 'i2p'
            if domain.endswith('.i2p'):
                argb.port = 80
        elif argb.gnunet:
            proxy_type = 'gnunet'
        word_frequency = {}
        domain_list = []
        if not argb.language:
            argb.language = 'en'
        signing_priv_key_pem = None
        if not argb.domain:
            origin_domain = get_config_param(base_dir, 'domain')
        else:
            origin_domain = argb.domain
        if argb.secure_mode:
            signing_priv_key_pem = \
                get_instance_actor_key(base_dir, origin_domain)
        domain_list = \
            get_public_post_domains(None,
                                    base_dir, nickname, domain,
                                    origin_domain,
                                    proxy_type, argb.port,
                                    http_prefix, debug,
                                    __version__,
                                    word_frequency, domain_list,
                                    argb.language,
                                    signing_priv_key_pem)
        for post_domain in domain_list:
            print(post_domain)
        sys.exit()

    if argb.postDomainsBlocked:
        # Domains which were referenced in public posts by a
        # given handle but which are globally blocked on this instance
        if '@' not in argb.postDomainsBlocked:
            if '/users/' in argb.postDomainsBlocked:
                posts_nickname = \
                    get_nickname_from_actor(argb.postDomainsBlocked)
                posts_domain, posts_port = \
                    get_domain_from_actor(argb.postDomainsBlocked)
                argb.postDomainsBlocked = \
                    get_full_domain(posts_nickname + '@' + posts_domain,
                                    posts_port)
            else:
                print('Syntax: --postDomainsBlocked nickname@domain')
                sys.exit()
        if not argb.http:
            argb.port = 443
        nickname = argb.postDomainsBlocked.split('@')[0]
        domain = argb.postDomainsBlocked.split('@')[1]
        proxy_type = None
        if argb.tor or domain.endswith('.onion'):
            proxy_type = 'tor'
            if domain.endswith('.onion'):
                argb.port = 80
        elif argb.i2p or domain.endswith('.i2p'):
            proxy_type = 'i2p'
            if domain.endswith('.i2p'):
                argb.port = 80
        elif argb.gnunet:
            proxy_type = 'gnunet'
        word_frequency = {}
        domain_list = []
        if not argb.language:
            argb.language = 'en'
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        domain_list = \
            get_public_post_domains_blocked(None,
                                            base_dir, nickname, domain,
                                            proxy_type, argb.port,
                                            http_prefix, debug,
                                            __version__,
                                            word_frequency, domain_list,
                                            argb.language,
                                            signing_priv_key_pem)
        for post_domain in domain_list:
            print(post_domain)
        sys.exit()

    if argb.check_domains:
        # Domains which were referenced in public posts by a
        # given handle but which are globally blocked on this instance
        if '@' not in argb.check_domains:
            if '/users/' in argb.check_domains:
                posts_nickname = get_nickname_from_actor(argb.posts)
                posts_domain, posts_port = get_domain_from_actor(argb.posts)
                argb.check_domains = \
                    get_full_domain(posts_nickname + '@' + posts_domain,
                                    posts_port)
            else:
                print('Syntax: --check_domains nickname@domain')
                sys.exit()
        if not argb.http:
            argb.port = 443
        nickname = argb.check_domains.split('@')[0]
        domain = argb.check_domains.split('@')[1]
        proxy_type = None
        if argb.tor or domain.endswith('.onion'):
            proxy_type = 'tor'
            if domain.endswith('.onion'):
                argb.port = 80
        elif argb.i2p or domain.endswith('.i2p'):
            proxy_type = 'i2p'
            if domain.endswith('.i2p'):
                argb.port = 80
        elif argb.gnunet:
            proxy_type = 'gnunet'
        max_blocked_domains = 0
        if not argb.language:
            argb.language = 'en'
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        check_domains(None,
                      base_dir, nickname, domain,
                      proxy_type, argb.port,
                      http_prefix, debug,
                      __version__,
                      max_blocked_domains, False, argb.language,
                      signing_priv_key_pem)
        sys.exit()

    if argb.socnet:
        if ',' not in argb.socnet:
            print('Syntax: '
                  '--socnet nick1@domain1,nick2@domain2,nick3@domain3')
            sys.exit()

        if not argb.http:
            argb.port = 443
        proxy_type = 'tor'
        if not argb.language:
            argb.language = 'en'
        if not argb.domain:
            argb.domain = get_config_param(base_dir, 'domain')
        domain = ''
        if argb.domain:
            domain = argb.domain
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        dot_graph = instances_graph(base_dir, argb.socnet,
                                    proxy_type, argb.port,
                                    http_prefix, debug,
                                    __version__, argb.language,
                                    signing_priv_key_pem)
        try:
            with open('socnet.dot', 'w+', encoding='utf-8') as fp_soc:
                fp_soc.write(dot_graph)
                print('Saved to socnet.dot')
        except OSError:
            print('EX: commandline unable to write socnet.dot')
        sys.exit()

    if argb.postsraw:
        if not argb.domain:
            origin_domain = get_config_param(base_dir, 'domain')
        else:
            origin_domain = argb.domain
        if debug:
            print('origin_domain: ' + str(origin_domain))
        if '@' not in argb.postsraw:
            print('Syntax: --postsraw nickname@domain')
            sys.exit()
        if not argb.http:
            argb.port = 443
        nickname = argb.postsraw.split('@')[0]
        domain = argb.postsraw.split('@')[1]
        proxy_type = None
        if argb.tor or domain.endswith('.onion'):
            proxy_type = 'tor'
        elif argb.i2p or domain.endswith('.i2p'):
            proxy_type = 'i2p'
        elif argb.gnunet:
            proxy_type = 'gnunet'
        if not argb.language:
            argb.language = 'en'
        signing_priv_key_pem = get_instance_actor_key(base_dir, origin_domain)
        get_public_posts_of_person(base_dir, nickname, domain, False, False,
                                   proxy_type, argb.port, http_prefix, debug,
                                   __version__, argb.language,
                                   signing_priv_key_pem, origin_domain)
        sys.exit()

    if argb.json:
        session = create_session(None)
        profile_str = 'https://www.w3.org/ns/activitystreams'
        as_header = {
            'Accept': 'application/ld+json; profile="' + profile_str + '"'
        }
        if not argb.domain:
            argb.domain = get_config_param(base_dir, 'domain')
        domain = ''
        if argb.domain:
            domain = argb.domain
        signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        if debug:
            print('base_dir: ' + str(base_dir))
            if signing_priv_key_pem:
                print('Obtained instance actor signing key')
            else:
                print('Did not obtain instance actor key for ' + domain)
        test_json = get_json(signing_priv_key_pem, session, argb.json,
                             as_header, None, debug, __version__,
                             http_prefix, domain)
        if test_json:
            pprint(test_json)
        sys.exit()

    if argb.ssml:
        session = create_session(None)
        profile_str = 'https://www.w3.org/ns/activitystreams'
        as_header = {
            'Accept': 'application/ssml+xml; profile="' + profile_str + '"'
        }
        if not argb.domain:
            argb.domain = get_config_param(base_dir, 'domain')
        domain = ''
        if argb.domain:
            domain = argb.domain
        signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        if debug:
            print('base_dir: ' + str(base_dir))
            if signing_priv_key_pem:
                print('Obtained instance actor signing key')
            else:
                print('Did not obtain instance actor key for ' + domain)
        test_ssml = download_ssml(signing_priv_key_pem, session, argb.ssml,
                                  as_header, None, debug, __version__,
                                  http_prefix, domain)
        if test_ssml:
            print(str(test_ssml))
        sys.exit()

    if argb.vcard:
        session = create_session(None)
        if not argb.domain:
            argb.domain = get_config_param(base_dir, 'domain')
        domain = ''
        if argb.domain:
            domain = argb.domain
        test_vcard = get_vcard(False, session, argb.vcard,
                               None, debug, __version__, http_prefix, domain)
        if test_vcard:
            print(test_vcard)
        sys.exit()

    if argb.xmlvcard:
        session = create_session(None)
        if not argb.domain:
            argb.domain = get_config_param(base_dir, 'domain')
        domain = ''
        if argb.domain:
            domain = argb.domain
        test_vcard = get_vcard(True, session, argb.xmlvcard,
                               None, debug, __version__, http_prefix, domain)
        if test_vcard:
            print(test_vcard)
        sys.exit()

    if argb.htmlpost:
        session = create_session(None)
        profile_str = 'https://www.w3.org/ns/activitystreams'
        as_header = {
            'Accept': 'text/html; profile="' + profile_str + '"'
        }
        if not argb.domain:
            argb.domain = get_config_param(base_dir, 'domain')
        domain = ''
        if argb.domain:
            domain = argb.domain
        signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        if debug:
            print('base_dir: ' + str(base_dir))
            if signing_priv_key_pem:
                print('Obtained instance actor signing key')
            else:
                print('Did not obtain instance actor key for ' + domain)
        test_html = download_html(signing_priv_key_pem, session, argb.htmlpost,
                                  as_header, None, debug, __version__,
                                  http_prefix, domain)
        if test_html:
            print(test_html)
        sys.exit()

    if argb.verifyurl:
        if not argb.nickname:
            print('You must specify a nickname for the handle ' +
                  'to be verified nickname@domain using the ' +
                  '--nickname option')
            sys.exit()
        profile_str = 'https://www.w3.org/ns/activitystreams'
        as_header = {
            'Accept': 'text/html; profile="' + profile_str + '"'
        }
        if not argb.domain:
            argb.domain = get_config_param(base_dir, 'domain')
        domain = ''
        if argb.domain:
            domain = argb.domain
        if not domain:
            print('You must specify a domain for the handle ' +
                  'to be verified nickname@domain using the ' +
                  '--domain option')
            sys.exit()
        session = create_session(None)
        verified = \
            verify_html(session, argb.verifyurl, debug, __version__,
                        http_prefix, argb.nickname, domain)
        if verified:
            print('Verified')
            sys.exit()
        print('Verification failed')
        sys.exit()

    # create cache for actors
    if not os.path.isdir(base_dir + '/cache'):
        os.mkdir(base_dir + '/cache')
    if not os.path.isdir(base_dir + '/cache/actors'):
        print('Creating actors cache')
        os.mkdir(base_dir + '/cache/actors')
    if not os.path.isdir(base_dir + '/cache/announce'):
        print('Creating announce cache')
        os.mkdir(base_dir + '/cache/announce')

    # set the theme in config.json
    theme_name = get_config_param(base_dir, 'theme')
    if not theme_name:
        set_config_param(base_dir, 'theme', 'default')
        theme_name = 'default'

    if not argb.mediainstance:
        media_instance = get_config_param(base_dir, 'mediaInstance')
        if media_instance is not None:
            argb.mediainstance = media_instance
            if argb.mediainstance:
                argb.blogsinstance = False
                argb.newsinstance = False

    if not argb.newsinstance:
        news_instance = get_config_param(base_dir, 'newsInstance')
        if news_instance is not None:
            argb.newsinstance = news_instance
            if argb.newsinstance:
                argb.blogsinstance = False
                argb.mediainstance = False

    if not argb.blogsinstance:
        blogs_instance = get_config_param(base_dir, 'blogsInstance')
        if blogs_instance is not None:
            argb.blogsinstance = blogs_instance
            if argb.blogsinstance:
                argb.mediainstance = False
                argb.newsinstance = False

    # set the instance title in config.json
    title = get_config_param(base_dir, 'instanceTitle')
    if not title:
        set_config_param(base_dir, 'instanceTitle', 'Epicyon')

    # set the instance description in config.json
    desc_full = get_config_param(base_dir, 'instanceDescription')
    if not desc_full:
        set_config_param(base_dir, 'instanceDescription',
                         'Just another ActivityPub server')

    # set the short instance description in config.json
    desc_short = get_config_param(base_dir, 'instanceDescriptionShort')
    if not desc_short:
        set_config_param(base_dir, 'instanceDescriptionShort',
                         'Just another ActivityPub server')

    if argb.domain:
        domain = argb.domain
        set_config_param(base_dir, 'domain', domain)

    # comma separated list of preferred audio formats. eg. "opus", "mp3", "spx"
    # in order of preference
    preferred_podcast_formats = ['ogg', 'mpeg', 'opus', 'spx', 'wav']
    if argb.podcast_formats:
        podcast_formats_str = argb.podcast_formats
    else:
        podcast_formats_str = \
            get_config_param(base_dir, 'preferredPodcastFormats')
    if podcast_formats_str:
        podcast_formats = podcast_formats_str.split(',')
        preferred_podcast_formats = []
        for pod_format in podcast_formats:
            pod_format = pod_format.lower().strip()
            if '/' not in pod_format:
                pod_format = 'audio/' + pod_format
            if pod_format in preferred_podcast_formats:
                continue
            preferred_podcast_formats.append(pod_format)

    if argb.rss:
        timeout_sec = 20
        session = create_session(None)
        if not argb.language:
            argb.language = 'en'
        test_rss = get_rss(base_dir, domain, session, argb.rss,
                           False, False, 1000, 1000, 1000, 1000, debug,
                           preferred_podcast_formats, timeout_sec,
                           argb.language)
        pprint(test_rss)
        sys.exit()

    if argb.onion:
        if not argb.onion.endswith('.onion'):
            print(argb.onion + ' does not look like an onion domain')
            sys.exit()
        if '://' in argb.onion:
            argb.onion = argb.onion.split('://')[1]
        onion_domain = argb.onion
        set_config_param(base_dir, 'onion', onion_domain)

    i2p_domain = None
    if argb.i2p_domain:
        if not argb.i2p_domain.endswith('.i2p'):
            print(argb.i2p_domain + ' does not look like an i2p domain')
            sys.exit()
        if '://' in argb.i2p_domain:
            argb.onion = argb.onion.split('://')[1]
        i2p_domain = argb.i2p_domain
        set_config_param(base_dir, 'i2pDomain', i2p_domain)

    if not argb.language:
        language_code = get_config_param(base_dir, 'language')
        if language_code:
            argb.language = language_code
        else:
            argb.language = 'en'

    # maximum number of new registrations
    if not argb.maxRegistrations:
        max_registrations = get_config_param(base_dir, 'maxRegistrations')
        if not max_registrations:
            max_registrations = 10
            set_config_param(base_dir, 'maxRegistrations',
                             str(max_registrations))
        else:
            max_registrations = int(max_registrations)
    else:
        max_registrations = argb.maxRegistrations
        set_config_param(base_dir, 'maxRegistrations', str(max_registrations))

    # if this is the initial run then allow new registrations
    if not get_config_param(base_dir, 'registration'):
        if argb.registration.lower() == 'open':
            set_config_param(base_dir, 'registration', 'open')
            set_config_param(base_dir, 'maxRegistrations',
                             str(max_registrations))
            set_config_param(base_dir, 'registrationsRemaining',
                             str(max_registrations))

    if argb.resetregistrations:
        set_config_param(base_dir, 'registrationsRemaining',
                         str(max_registrations))
        print('Number of new registrations reset to ' + str(max_registrations))

    # unique ID for the instance
    instance_id = get_config_param(base_dir, 'instanceId')
    if not instance_id:
        instance_id = create_password(32)
        set_config_param(base_dir, 'instanceId', instance_id)
        print('Instance ID: ' + instance_id)

    # get domain name from configuration
    config_domain = get_config_param(base_dir, 'domain')
    if config_domain:
        domain = config_domain
    else:
        domain = 'localhost'

    # get onion domain name from configuration
    config_onion_domain = get_config_param(base_dir, 'onion')
    if config_onion_domain:
        onion_domain = config_onion_domain
    else:
        onion_domain = None

    # get i2p domain name from configuration
    configi2p_domain = get_config_param(base_dir, 'i2pDomain')
    if configi2p_domain:
        i2p_domain = configi2p_domain
    else:
        i2p_domain = None

    # get port number from configuration
    config_port = get_config_param(base_dir, 'port')
    if config_port:
        port = config_port
    else:
        if domain.endswith('.onion') or \
           domain.endswith('.i2p'):
            port = 80
        else:
            port = 443

    config_proxy_port = get_config_param(base_dir, 'proxyPort')
    if config_proxy_port:
        proxy_port = config_proxy_port
    else:
        proxy_port = port

    nickname = None
    if argb.nickname:
        nickname = argb.nickname

    federation_list = []
    if argb.federation_list:
        if len(argb.federation_list) == 1:
            if not (argb.federation_list[0].lower() == 'any' or
                    argb.federation_list[0].lower() == 'all' or
                    argb.federation_list[0].lower() == '*'):
                for federation_domain in argb.federation_list:
                    if '@' in federation_domain:
                        print(federation_domain +
                              ': Federate with domains, not individual ' +
                              'accounts')
                        sys.exit()
                federation_list = argb.federation_list.copy()
            set_config_param(base_dir, 'federationList', federation_list)
    else:
        config_federation_list = get_config_param(base_dir, 'federationList')
        if config_federation_list:
            federation_list = config_federation_list

    proxy_type = None
    if argb.tor or domain.endswith('.onion'):
        proxy_type = 'tor'
    elif argb.i2p or domain.endswith('.i2p'):
        proxy_type = 'i2p'
    elif argb.gnunet:
        proxy_type = 'gnunet'

    if argb.approve:
        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()
        if '@' not in argb.approve:
            print('syntax: --approve nick@domain')
            sys.exit()
        session_onion = None
        session_i2p = None
        session = create_session(proxy_type)
        send_threads = []
        post_log = []
        cached_webfingers = {}
        person_cache = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        onion_domain = get_config_param(base_dir, 'onionDomain')
        if argb.onion:
            onion_domain = argb.onion
        if onion_domain:
            session_onion = create_session('tor')
        i2p_domain = get_config_param(base_dir, 'i2pDomain')
        if argb.i2p_domain:
            i2p_domain = argb.i2p_domain
        if i2p_domain:
            session_i2p = create_session('i2p')
        manual_approve_follow_request(session, session_onion, session_i2p,
                                      onion_domain, i2p_domain,
                                      base_dir, http_prefix,
                                      argb.nickname, domain, port,
                                      argb.approve,
                                      federation_list,
                                      send_threads, post_log,
                                      cached_webfingers, person_cache,
                                      debug, __version__,
                                      signing_priv_key_pem, proxy_type)
        sys.exit()

    if argb.deny:
        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()
        if '@' not in argb.deny:
            print('syntax: --deny nick@domain')
            sys.exit()
        session_onion = None
        session_i2p = None
        session = create_session(proxy_type)
        send_threads = []
        post_log = []
        cached_webfingers = {}
        person_cache = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        onion_domain = get_config_param(base_dir, 'onionDomain')
        if argb.onion:
            onion_domain = argb.onion
        if onion_domain:
            session_onion = create_session('tor')
        i2p_domain = get_config_param(base_dir, 'i2pDomain')
        if argb.i2p_domain:
            i2p_domain = argb.i2p_domain
        if i2p_domain:
            session_i2p = create_session('i2p')
        manual_deny_follow_request(session, session_onion, session_i2p,
                                   onion_domain, i2p_domain,
                                   base_dir, http_prefix,
                                   argb.nickname, domain, port,
                                   argb.deny,
                                   federation_list,
                                   send_threads, post_log,
                                   cached_webfingers, person_cache,
                                   debug, __version__,
                                   signing_priv_key_pem)
        sys.exit()

    if argb.followerspending:
        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        accounts_dir = acct_dir(base_dir, argb.nickname, domain)
        approve_follows_filename = accounts_dir + '/followrequests.txt'
        approve_ctr = 0
        if os.path.isfile(approve_follows_filename):
            with open(approve_follows_filename, 'r',
                      encoding='utf-8') as approvefile:
                for approve in approvefile:
                    approve1 = remove_eol(approve)
                    print(approve1)
                    approve_ctr += 1
        if approve_ctr == 0:
            print('There are no follow requests pending approval.')
        sys.exit()

    if argb.message:
        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if argb.eventDate:
            if '-' not in argb.eventDate or len(argb.eventDate) != 10:
                print('Event date format should be YYYY-MM-DD')
                sys.exit()

        if argb.eventTime:
            if ':' not in argb.eventTime or len(argb.eventTime) != 5:
                print('Event start time format should be HH:MM')
                sys.exit()

        if argb.eventEndTime:
            if ':' not in argb.eventEndTime or len(argb.eventEndTime) != 5:
                print('Event end time format should be HH:MM')
                sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        if not argb.sendto:
            print('Specify an account to sent to: --sendto [nickname@domain]')
            sys.exit()
        if '@' not in argb.sendto and \
           not argb.sendto.lower().endswith('public') and \
           not argb.sendto.lower().endswith('followers'):
            print('syntax: --sendto [nickname@domain]')
            print('        --sendto public')
            print('        --sendto followers')
            sys.exit()
        if '@' in argb.sendto:
            to_nickname = argb.sendto.split('@')[0]
            to_domain = argb.sendto.split('@')[1]
            to_domain = remove_eol(to_domain)
            to_port = 443
            if ':' in to_domain:
                to_port = get_port_from_domain(to_domain)
                to_domain = remove_domain_port(to_domain)
        else:
            if argb.sendto.endswith('followers'):
                to_nickname = None
                to_domain = 'followers'
                to_port = port
            else:
                to_nickname = None
                to_domain = 'public'
                to_port = port

        cc_url = None
        send_message = argb.message
        # client_to_server = argb.client
        attached_image_description = argb.imageDescription
        city = 'London, England'
        send_threads = []
        post_log = []
        person_cache = {}
        cached_webfingers = {}
        subject = argb.subject
        attach = argb.attach
        media_type = None
        if attach:
            media_type = get_attachment_media_type(attach)
        reply_to = argb.replyto
        is_article = False
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        languages_understood = [argb.language]
        if argb.languages_understood:
            languages_understood = [argb.languages_understood]
        translate = {}

        print('Sending post to ' + argb.sendto)
        send_post_via_server(signing_priv_key_pem, __version__,
                             base_dir, session, argb.nickname, argb.password,
                             domain, port,
                             to_nickname, to_domain, to_port, cc_url,
                             http_prefix, send_message,
                             argb.commentsEnabled, attach, media_type,
                             attached_image_description, city,
                             cached_webfingers, person_cache, is_article,
                             argb.language, languages_understood,
                             argb.low_bandwidth,
                             argb.content_license_url,
                             argb.eventDate, argb.eventTime, argb.eventEndTime,
                             argb.eventLocation, translate,
                             argb.debug,
                             reply_to, reply_to, argb.conversationId, subject)
        for _ in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.expiryDays is not None and argb.nickname and argb.domain:
        set_post_expiry_days(base_dir, argb.nickname, argb.domain,
                             argb.expiryDays)
        print('Post expiry for ' + argb.nickname + ' set to ' +
              str(argb.expiryDays))
        sys.exit()

    if argb.dav:
        if not argb.nickname:
            print('Please specify a nickname with --nickname')
            sys.exit()
        if not argb.domain:
            print('Please specify a domain with --domain')
            sys.exit()
        if not argb.year:
            print('Please specify a year with --year')
            sys.exit()
        if not argb.month:
            print('Please specify a month with --month')
            sys.exit()
        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)
        proxy_type = None
        if argb.tor or domain.endswith('.onion'):
            proxy_type = 'tor'
            if domain.endswith('.onion'):
                argb.port = 80
        elif argb.i2p or domain.endswith('.i2p'):
            proxy_type = 'i2p'
            if domain.endswith('.i2p'):
                argb.port = 80
        elif argb.gnunet:
            proxy_type = 'gnunet'
        session = create_session(proxy_type)
        if argb.day:
            result = \
                dav_day_via_server(session, http_prefix,
                                   argb.nickname, argb.domain, argb.port,
                                   argb.debug,
                                   argb.year, argb.month, argb.day,
                                   argb.password)
        else:
            result = \
                dav_month_via_server(session, http_prefix,
                                     argb.nickname, argb.domain, argb.port,
                                     argb.debug,
                                     argb.year, argb.month,
                                     argb.password)
        if result:
            print(str(result))
        sys.exit()

    if argb.announce:
        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending announce/repeat of ' + argb.announce)

        send_announce_via_server(base_dir, session,
                                 argb.nickname, argb.password,
                                 domain, port,
                                 http_prefix, argb.announce,
                                 cached_webfingers, person_cache,
                                 True, __version__, signing_priv_key_pem)
        for _ in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.box:
        if not domain:
            print('Specify a domain with the --domain option')
            sys.exit()

        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        proxy_type = None
        if argb.tor or domain.endswith('.onion'):
            proxy_type = 'tor'
            if domain.endswith('.onion'):
                argb.port = 80
        elif argb.i2p or domain.endswith('.i2p'):
            proxy_type = 'i2p'
            if domain.endswith('.i2p'):
                argb.port = 80
        elif argb.gnunet:
            proxy_type = 'gnunet'
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)

        session = create_session(proxy_type)
        box_json = c2s_box_json(session, argb.nickname, argb.password,
                                domain, port, http_prefix,
                                argb.box, argb.pageNumber,
                                argb.debug, signing_priv_key_pem)
        if box_json:
            pprint(box_json)
        else:
            print('Box not found: ' + argb.box)
        sys.exit()

    if argb.itemName:
        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.summary:
            print('Specify a description for your shared item ' +
                  'with the --summary option')
            sys.exit()

        if not argb.itemQty:
            print('Specify a quantity of shared items with the ' +
                  '--itemQty option')
            sys.exit()

        if not argb.itemType:
            print('Specify a type of shared item with the --itemType option')
            sys.exit()

        if not argb.itemCategory:
            print('Specify a category of shared item ' +
                  'with the --itemCategory option')
            sys.exit()

        if not argb.location:
            print('Specify a location or city where the shared ' +
                  'item resides with the --location option')
            sys.exit()

        if not argb.duration:
            print('Specify a duration to share the object ' +
                  'with the --duration option')
            sys.exit()

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending shared item: ' + argb.itemName)

        send_share_via_server(base_dir, session,
                              argb.nickname, argb.password,
                              domain, port,
                              http_prefix,
                              argb.itemName,
                              argb.summary,
                              argb.itemImage,
                              argb.itemQty,
                              argb.itemType,
                              argb.itemCategory,
                              argb.location,
                              argb.duration,
                              cached_webfingers, person_cache,
                              debug, __version__,
                              argb.itemPrice, argb.itemCurrency,
                              signing_priv_key_pem)
        for _ in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.undoItemName:
        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending undo of shared item: ' + argb.undoItemName)

        send_undo_share_via_server(base_dir, session,
                                   argb.nickname, argb.password,
                                   domain, port,
                                   http_prefix,
                                   argb.undoItemName,
                                   cached_webfingers, person_cache,
                                   debug, __version__, signing_priv_key_pem)
        for _ in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.wantedItemName:
        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.summary:
            print('Specify a description for your shared item ' +
                  'with the --summary option')
            sys.exit()

        if not argb.itemQty:
            print('Specify a quantity of shared items with the ' +
                  '--itemQty option')
            sys.exit()

        if not argb.itemType:
            print('Specify a type of shared item with the --itemType option')
            sys.exit()

        if not argb.itemCategory:
            print('Specify a category of shared item ' +
                  'with the --itemCategory option')
            sys.exit()

        if not argb.location:
            print('Specify a location or city where the wanted ' +
                  'item resides with the --location option')
            sys.exit()

        if not argb.duration:
            print('Specify a duration to share the object ' +
                  'with the --duration option')
            sys.exit()

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending wanted item: ' + argb.wantedItemName)

        send_wanted_via_server(base_dir, session,
                               argb.nickname, argb.password,
                               domain, port,
                               http_prefix,
                               argb.wantedItemName,
                               argb.summary,
                               argb.itemImage,
                               argb.itemQty,
                               argb.itemType,
                               argb.itemCategory,
                               argb.location,
                               argb.duration,
                               cached_webfingers, person_cache,
                               debug, __version__,
                               argb.itemPrice, argb.itemCurrency,
                               signing_priv_key_pem)
        for _ in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.undoWantedItemName:
        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending undo of wanted item: ' + argb.undoWantedItemName)

        send_undo_wanted_via_server(base_dir, session,
                                    argb.nickname, argb.password,
                                    domain, port,
                                    http_prefix,
                                    argb.undoWantedItemName,
                                    cached_webfingers, person_cache,
                                    debug, __version__, signing_priv_key_pem)
        for _ in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.like:
        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending like of ' + argb.like)

        send_like_via_server(base_dir, session,
                             argb.nickname, argb.password,
                             domain, port,
                             http_prefix, argb.like,
                             cached_webfingers, person_cache,
                             True, __version__, signing_priv_key_pem)
        for _ in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.react:
        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()
        if not argb.emoji:
            print('Specify a reaction emoji with the --emoji option')
            sys.exit()
        if not valid_emoji_content(argb.emoji):
            print('This is not a valid emoji')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending emoji reaction ' + argb.emoji + ' to ' + argb.react)

        send_reaction_via_server(base_dir, session,
                                 argb.nickname, argb.password,
                                 domain, port,
                                 http_prefix, argb.react, argb.emoji,
                                 cached_webfingers, person_cache,
                                 True, __version__, signing_priv_key_pem)
        for _ in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.undolike:
        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending undo like of ' + argb.undolike)

        send_undo_like_via_server(base_dir, session,
                                  argb.nickname, argb.password,
                                  domain, port,
                                  http_prefix, argb.undolike,
                                  cached_webfingers, person_cache,
                                  True, __version__,
                                  signing_priv_key_pem)
        for _ in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.undoreact:
        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()
        if not argb.emoji:
            print('Specify a reaction emoji with the --emoji option')
            sys.exit()
        if not valid_emoji_content(argb.emoji):
            print('This is not a valid emoji')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending undo emoji reaction ' +
              argb.emoji + ' to ' + argb.react)

        send_undo_reaction_via_server(base_dir, session,
                                      argb.nickname, argb.password,
                                      domain, port,
                                      http_prefix, argb.undoreact, argb.emoji,
                                      cached_webfingers, person_cache,
                                      True, __version__,
                                      signing_priv_key_pem)
        for _ in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.bookmark:
        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending bookmark of ' + argb.bookmark)

        send_bookmark_via_server(base_dir, session,
                                 argb.nickname, argb.password,
                                 domain, port,
                                 http_prefix, argb.bookmark,
                                 cached_webfingers, person_cache,
                                 True, __version__,
                                 signing_priv_key_pem)
        for _ in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.unbookmark:
        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending undo bookmark of ' + argb.unbookmark)

        send_undo_bookmark_via_server(base_dir, session,
                                      argb.nickname, argb.password,
                                      domain, port,
                                      http_prefix, argb.unbookmark,
                                      cached_webfingers, person_cache,
                                      True, __version__, signing_priv_key_pem)
        for _ in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.delete:
        if not argb.nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending delete request of ' + argb.delete)

        send_delete_via_server(base_dir, session,
                               argb.nickname, argb.password,
                               domain, port,
                               http_prefix, argb.delete,
                               cached_webfingers, person_cache,
                               True, __version__, signing_priv_key_pem)
        for _ in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.follow:
        # follow via c2s protocol
        if '.' not in argb.follow:
            print("This doesn't look like a fediverse handle")
            sys.exit()
        if not argb.nickname:
            print('Please specify the nickname for the account ' +
                  'with --nickname')
            sys.exit()
        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        follow_nickname = get_nickname_from_actor(argb.follow)
        if not follow_nickname:
            print('Unable to find nickname in ' + argb.follow)
            sys.exit()
        follow_domain, follow_port = get_domain_from_actor(argb.follow)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        follow_http_prefix = http_prefix
        if argb.follow.startswith('https'):
            follow_http_prefix = 'https'
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)

        send_follow_request_via_server(base_dir, session,
                                       argb.nickname, argb.password,
                                       domain, port,
                                       follow_nickname, follow_domain,
                                       follow_port, follow_http_prefix,
                                       cached_webfingers, person_cache,
                                       debug, __version__,
                                       signing_priv_key_pem)
        for _ in range(20):
            time.sleep(1)
            # TODO some method to know if it worked
        print('Ok')
        sys.exit()

    if argb.unfollow:
        # unfollow via c2s protocol
        if '.' not in argb.follow:
            print("This doesn't look like a fediverse handle")
            sys.exit()
        if not argb.nickname:
            print('Please specify the nickname for the account ' +
                  'with --nickname')
            sys.exit()
        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        follow_nickname = get_nickname_from_actor(argb.unfollow)
        if not follow_nickname:
            print('WARN: unable to find nickname in ' + argb.unfollow)
            sys.exit()
        follow_domain, follow_port = get_domain_from_actor(argb.unfollow)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        follow_http_prefix = http_prefix
        if argb.follow.startswith('https'):
            follow_http_prefix = 'https'
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)

        send_unfollow_request_via_server(base_dir, session,
                                         argb.nickname, argb.password,
                                         domain, port,
                                         follow_nickname, follow_domain,
                                         follow_port, follow_http_prefix,
                                         cached_webfingers, person_cache,
                                         debug, __version__,
                                         signing_priv_key_pem)
        for _ in range(20):
            time.sleep(1)
            # TODO some method to know if it worked
        print('Ok')
        sys.exit()

    if argb.followingList:
        # following list via c2s protocol
        if not argb.nickname:
            print('Please specify the nickname for the account ' +
                  'with --nickname')
            sys.exit()
        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        follow_http_prefix = http_prefix
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)

        following_json = \
            get_following_via_server(session,
                                     argb.nickname, argb.password,
                                     domain, port,
                                     follow_http_prefix, argb.pageNumber,
                                     debug, __version__, signing_priv_key_pem)
        if following_json:
            pprint(following_json)
        sys.exit()

    if argb.followersList:
        # following list via c2s protocol
        if not argb.nickname:
            print('Please specify the nickname for the account ' +
                  'with --nickname')
            sys.exit()
        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        follow_http_prefix = http_prefix
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)

        followers_json = \
            get_followers_via_server(session,
                                     argb.nickname, argb.password,
                                     domain, port,
                                     follow_http_prefix, argb.pageNumber,
                                     debug, __version__,
                                     signing_priv_key_pem)
        if followers_json:
            pprint(followers_json)
        sys.exit()

    if argb.followRequestsList:
        # follow requests list via c2s protocol
        if not argb.nickname:
            print('Please specify the nickname for the account ' +
                  'with --nickname')
            sys.exit()
        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        follow_http_prefix = http_prefix
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)

        follow_requests_json = \
            get_follow_requests_via_server(session,
                                           argb.nickname, argb.password,
                                           domain, port,
                                           follow_http_prefix, argb.pageNumber,
                                           debug, __version__,
                                           signing_priv_key_pem)
        if follow_requests_json:
            pprint(follow_requests_json)
        sys.exit()

    nickname = 'admin'
    if argb.domain:
        domain = argb.domain
        set_config_param(base_dir, 'domain', domain)
    if argb.port:
        port = argb.port
        set_config_param(base_dir, 'port', port)
    if argb.proxy_port:
        proxy_port = argb.proxy_port
        set_config_param(base_dir, 'proxyPort', proxy_port)
    if argb.gnunet:
        http_prefix = 'gnunet'
    if argb.dat or argb.hyper:
        http_prefix = 'hyper'
    if argb.ipfs:
        http_prefix = 'ipfs'
    if argb.ipns:
        http_prefix = 'ipns'
    if argb.i2p:
        http_prefix = 'http'

    if argb.migrations:
        cached_webfingers = {}
        if argb.http or domain.endswith('.onion'):
            http_prefix = 'http'
            port = 80
            proxy_type = 'tor'
        elif domain.endswith('.i2p'):
            http_prefix = 'http'
            port = 80
            proxy_type = 'i2p'
        elif argb.ipfs:
            http_prefix = 'ipfs'
            port = 80
            proxy_type = 'ipfs'
        elif argb.ipns:
            http_prefix = 'ipns'
            port = 80
            proxy_type = 'ipfs'
        elif argb.gnunet:
            http_prefix = 'gnunet'
            port = 80
            proxy_type = 'gnunet'
        else:
            http_prefix = 'https'
            port = 443
        session = create_session(proxy_type)
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        ctr = migrate_accounts(base_dir, session,
                               http_prefix, cached_webfingers,
                               True, signing_priv_key_pem)
        if ctr == 0:
            print('No followed accounts have moved')
        else:
            print(str(ctr) + ' followed accounts were migrated')
        sys.exit()

    if argb.actor:
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        if debug:
            print('base_dir: ' + str(base_dir))
            if signing_priv_key_pem:
                print('Obtained instance actor signing key')
            else:
                print('Did not obtain instance actor key for ' + domain)
        get_actor_json(domain, argb.actor, argb.http, argb.gnunet,
                       argb.ipfs, argb.ipns,
                       debug, False, signing_priv_key_pem, None)
        sys.exit()

    if argb.followers:
        original_actor = argb.followers
        if '/@' in argb.followers or \
           '/users/' in argb.followers or \
           argb.followers.startswith('http') or \
           argb.followers.startswith('ipfs') or \
           argb.followers.startswith('ipns') or \
           argb.followers.startswith('hyper'):
            # format: https://domain/@nick
            prefixes = get_protocol_prefixes()
            for prefix in prefixes:
                argb.followers = argb.followers.replace(prefix, '')
            argb.followers = argb.followers.replace('/@', '/users/')
            if not has_users_path(argb.followers):
                print('Expected actor format: ' +
                      'https://domain/@nick or https://domain/users/nick')
                sys.exit()
            if '/users/' in argb.followers:
                nickname = argb.followers.split('/users/')[1]
                nickname = remove_eol(nickname)
                domain = argb.followers.split('/users/')[0]
            elif '/profile/' in argb.followers:
                nickname = argb.followers.split('/profile/')[1]
                nickname = remove_eol(nickname)
                domain = argb.followers.split('/profile/')[0]
            elif '/author/' in argb.followers:
                nickname = argb.followers.split('/author/')[1]
                nickname = remove_eol(nickname)
                domain = argb.followers.split('/author/')[0]
            elif '/channel/' in argb.followers:
                nickname = argb.followers.split('/channel/')[1]
                nickname = remove_eol(nickname)
                domain = argb.followers.split('/channel/')[0]
            elif '/accounts/' in argb.followers:
                nickname = argb.followers.split('/accounts/')[1]
                nickname = remove_eol(nickname)
                domain = argb.followers.split('/accounts/')[0]
            elif '/u/' in argb.followers:
                nickname = argb.followers.split('/u/')[1]
                nickname = remove_eol(nickname)
                domain = argb.followers.split('/u/')[0]
            elif '/c/' in argb.followers:
                nickname = argb.followers.split('/c/')[1]
                nickname = remove_eol(nickname)
                domain = argb.followers.split('/c/')[0]
        else:
            # format: @nick@domain
            if '@' not in argb.followers:
                print('Syntax: --actor nickname@domain')
                sys.exit()
            if argb.followers.startswith('@'):
                argb.followers = argb.followers[1:]
            if '@' not in argb.followers:
                print('Syntax: --actor nickname@domain')
                sys.exit()
            nickname = argb.followers.split('@')[0]
            domain = argb.followers.split('@')[1]
            domain = remove_eol(domain)
        cached_webfingers = {}
        if argb.http or domain.endswith('.onion'):
            http_prefix = 'http'
            port = 80
            proxy_type = 'tor'
        elif domain.endswith('.i2p'):
            http_prefix = 'http'
            port = 80
            proxy_type = 'i2p'
        elif argb.gnunet:
            http_prefix = 'gnunet'
            port = 80
            proxy_type = 'gnunet'
        elif argb.ipfs:
            http_prefix = 'ipfs'
            port = 80
            proxy_type = 'ipfs'
        elif argb.ipns:
            http_prefix = 'ipns'
            port = 80
            proxy_type = 'ipfs'
        else:
            http_prefix = 'https'
            port = 443
        session = create_session(proxy_type)
        if nickname == 'inbox':
            nickname = domain

        host_domain = None
        if argb.domain:
            host_domain = argb.domain
        handle = nickname + '@' + domain
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        wf_request = webfinger_handle(session, handle,
                                      http_prefix, cached_webfingers,
                                      host_domain, __version__, debug, False,
                                      signing_priv_key_pem)
        if not wf_request:
            print('Unable to webfinger ' + handle)
            sys.exit()
        if not isinstance(wf_request, dict):
            print('Webfinger for ' + handle + ' did not return a dict. ' +
                  str(wf_request))
            sys.exit()

        person_url = None
        if wf_request.get('errors'):
            print('wf_request error: ' + str(wf_request['errors']))
            if has_users_path(argb.followers):
                person_url = original_actor
            else:
                sys.exit()

        profile_str = 'https://www.w3.org/ns/activitystreams'
        accept_str = \
            'application/activity+json; profile="' + profile_str + '"'
        as_header = {
            'Accept': accept_str
        }
        if not person_url:
            person_url = get_user_url(wf_request, 0, argb.debug)
        if nickname == domain:
            person_url = person_url.replace('/users/', '/actor/')
            person_url = person_url.replace('/accounts/', '/actor/')
            person_url = person_url.replace('/channel/', '/actor/')
            person_url = person_url.replace('/profile/', '/actor/')
            person_url = person_url.replace('/author/', '/actor/')
            person_url = person_url.replace('/u/', '/actor/')
            person_url = person_url.replace('/c/', '/actor/')
        if not person_url:
            # try single user instance
            person_url = http_prefix + '://' + domain
            profile_str = 'https://www.w3.org/ns/activitystreams'
            as_header = {
                'Accept': 'application/ld+json; profile="' + profile_str + '"'
            }
        if '/channel/' in person_url or '/accounts/' in person_url:
            profile_str = 'https://www.w3.org/ns/activitystreams'
            as_header = {
                'Accept': 'application/ld+json; profile="' + profile_str + '"'
            }
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        followers_list = \
            download_follow_collection(signing_priv_key_pem,
                                       'followers', session,
                                       http_prefix, person_url, 1, 3,
                                       argb.debug)
        if followers_list:
            for actor in followers_list:
                print(actor)
        sys.exit()

    if argb.addaccount:
        if '@' in argb.addaccount:
            nickname = argb.addaccount.split('@')[0]
            domain = argb.addaccount.split('@')[1]
        else:
            nickname = argb.addaccount
            if not argb.domain or not get_config_param(base_dir, 'domain'):
                print('Use the --domain option to set the domain name')
                sys.exit()

        configured_domain = get_config_param(base_dir, 'domain')
        if configured_domain:
            if domain != configured_domain:
                print('The account domain is expected to be ' +
                      configured_domain)
                sys.exit()

        if not valid_nickname(domain, nickname):
            print(nickname + ' is a reserved name. Use something different.')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)
        if len(argb.password.strip()) < 8:
            print('Password should be at least 8 characters')
            sys.exit()
        account_dir = acct_dir(base_dir, nickname, domain)
        if os.path.isdir(account_dir):
            print('Account already exists')
            sys.exit()
        if os.path.isdir(base_dir + '/deactivated/' + nickname + '@' + domain):
            print('Account is deactivated')
            sys.exit()
        if domain.endswith('.onion') or \
           domain.endswith('.i2p'):
            port = 80
            http_prefix = 'http'
        if domain.endswith('.ipfs'):
            port = 80
            http_prefix = 'ipfs'
        if domain.endswith('.ipns'):
            port = 80
            http_prefix = 'ipns'
        create_person(base_dir, nickname, domain, port, http_prefix,
                      True, not argb.noapproval, argb.password.strip())
        if os.path.isdir(account_dir):
            print('Account created for ' + nickname + '@' + domain)
        else:
            print('Account creation failed')
        sys.exit()

    if argb.addgroup:
        if '@' in argb.addgroup:
            nickname = argb.addgroup.split('@')[0]
            domain = argb.addgroup.split('@')[1]
        else:
            nickname = argb.addgroup
            if not argb.domain or not get_config_param(base_dir, 'domain'):
                print('Use the --domain option to set the domain name')
                sys.exit()
        if nickname.startswith('!'):
            # remove preceding group indicator
            nickname = nickname[1:]
        if not valid_nickname(domain, nickname):
            print(nickname + ' is a reserved name. Use something different.')
            sys.exit()
        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)
        if len(argb.password.strip()) < 8:
            print('Password should be at least 8 characters')
            sys.exit()
        account_dir = acct_dir(base_dir, nickname, domain)
        if os.path.isdir(account_dir):
            print('Group already exists')
            sys.exit()
        create_group(base_dir, nickname, domain, port, http_prefix,
                     True, argb.password.strip())
        if os.path.isdir(account_dir):
            print('Group created for ' + nickname + '@' + domain)
        else:
            print('Group creation failed')
        sys.exit()

    if argb.rmgroup:
        argb.rmaccount = argb.rmgroup

    if argb.deactivate:
        argb.rmaccount = argb.deactivate

    if argb.rmaccount:
        if '@' in argb.rmaccount:
            nickname = argb.rmaccount.split('@')[0]
            domain = argb.rmaccount.split('@')[1]
        else:
            nickname = argb.rmaccount
            if not argb.domain or not get_config_param(base_dir, 'domain'):
                print('Use the --domain option to set the domain name')
                sys.exit()
            if argb.domain:
                domain = argb.domain
            else:
                domain = get_config_param(base_dir, 'domain')

        configured_domain = get_config_param(base_dir, 'domain')
        if configured_domain:
            if domain != configured_domain:
                print('The account domain is expected to be ' +
                      configured_domain)
                sys.exit()

        if argb.deactivate:
            if deactivate_account(base_dir, nickname, domain):
                print('Account for ' + nickname + '@' + domain +
                      ' was deactivated')
            else:
                print('Account for ' + nickname + '@' + domain +
                      ' was not found')
            sys.exit()
        if remove_account(base_dir, nickname, domain, port):
            if not argb.rmgroup:
                print('Account for ' + nickname + '@' + domain +
                      ' was removed')
            else:
                print('Group ' + nickname + '@' + domain + ' was removed')
            sys.exit()

    if argb.activate:
        if '@' in argb.activate:
            nickname = argb.activate.split('@')[0]
            domain = argb.activate.split('@')[1]
        else:
            nickname = argb.activate
            if not argb.domain or not get_config_param(base_dir, 'domain'):
                print('Use the --domain option to set the domain name')
                sys.exit()
        if activate_account(base_dir, nickname, domain):
            print('Account for ' + nickname + '@' + domain + ' was activated')
        else:
            print('Deactivated account for ' + nickname + '@' + domain +
                  ' was not found')
        sys.exit()

    if argb.changepassword:
        if len(argb.changepassword) != 2:
            print('--changepassword [nickname] [new password]')
            sys.exit()
        if '@' in argb.changepassword[0]:
            nickname = argb.changepassword[0].split('@')[0]
            domain = argb.changepassword[0].split('@')[1]
        else:
            nickname = argb.changepassword[0]
            if not argb.domain or not get_config_param(base_dir, 'domain'):
                print('Use the --domain option to set the domain name')
                sys.exit()
        new_password = argb.changepassword[1]
        if len(new_password) < 8:
            print('Password should be at least 8 characters')
            sys.exit()
        account_dir = acct_dir(base_dir, nickname, domain)
        if not os.path.isdir(account_dir):
            print('Account ' + nickname + '@' + domain + ' not found')
            sys.exit()
        password_file = base_dir + '/accounts/passwords'
        if os.path.isfile(password_file):
            if text_in_file(nickname + ':', password_file):
                store_basic_credentials(base_dir, nickname, new_password)
                print('Password for ' + nickname + ' was changed')
            else:
                print(nickname + ' is not in the passwords file')
        else:
            print('Passwords file not found')
        sys.exit()

    if argb.archive:
        if argb.archive.lower().endswith('null') or \
           argb.archive.lower().endswith('delete') or \
           argb.archive.lower().endswith('none'):
            argb.archive = None
            print('Archiving with deletion of old posts...')
        else:
            print('Archiving to ' + argb.archive + '...')
        # archiving is for non-instance posts
        archive_media(base_dir, argb.archive, argb.archiveWeeks)
        archive_posts(base_dir, http_prefix, argb.archive, {},
                      argb.archiveMaxPosts,
                      argb.maxCacheAgeDays)
        print('Archiving complete')
        # expiry is for instance posts, where an expiry period
        # has been set within profile settings
        expired_count = expire_posts(base_dir, http_prefix, {},
                                     argb.debug)
        if expired_count > 0:
            print(str(expired_count) + ' posts expired')
        sys.exit()

    if not argb.domain and not domain:
        print('Specify a domain with --domain [name]')
        sys.exit()

    if argb.avatar:
        if not os.path.isfile(argb.avatar):
            print(argb.avatar + ' is not an image filename')
            sys.exit()
        if not argb.nickname:
            print('Specify a nickname with --nickname [name]')
            sys.exit()
        city = 'London, England'
        if set_profile_image(base_dir, http_prefix, argb.nickname, domain,
                             port, argb.avatar, 'avatar', '128x128', city,
                             argb.content_license_url):
            print('Avatar added for ' + argb.nickname)
        else:
            print('Avatar was not added for ' + argb.nickname)
        sys.exit()

    if argb.backgroundImage:
        if not os.path.isfile(argb.backgroundImage):
            print(argb.backgroundImage + ' is not an image filename')
            sys.exit()
        if not argb.nickname:
            print('Specify a nickname with --nickname [name]')
            sys.exit()
        city = 'London, England'
        if set_profile_image(base_dir, http_prefix, argb.nickname, domain,
                             port, argb.backgroundImage, 'background',
                             '256x256', city, argb.content_license_url):
            print('Background image added for ' + argb.nickname)
        else:
            print('Background image was not added for ' + argb.nickname)
        sys.exit()

    if argb.skill:
        if not nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        if not argb.skillLevelPercent:
            print('Specify a skill level in the range 0-100')
            sys.exit()

        if int(argb.skillLevelPercent) < 0 or \
           int(argb.skillLevelPercent) > 100:
            print('Skill level should be a percentage in the range 0-100')
            sys.exit()

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending ' + argb.skill + ' skill level ' +
              str(argb.skillLevelPercent) + ' for ' + nickname)

        send_skill_via_server(base_dir, session,
                              nickname, argb.password,
                              domain, port,
                              http_prefix,
                              argb.skill, argb.skillLevelPercent,
                              cached_webfingers, person_cache,
                              True, __version__, signing_priv_key_pem)
        for i in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.availability:
        if not nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending availability status of ' + nickname +
              ' as ' + argb.availability)

        send_availability_via_server(base_dir, session,
                                     nickname, argb.password,
                                     domain, port, http_prefix,
                                     argb.availability,
                                     cached_webfingers, person_cache,
                                     True, __version__, signing_priv_key_pem)
        for i in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.desktop:
        # Announce posts as they arrive in your inbox using text-to-speech
        if argb.desktop.startswith('@'):
            argb.desktop = argb.desktop[1:]
        if '@' not in argb.desktop:
            print('Specify the handle to notify: nickname@domain')
            sys.exit()
        nickname = argb.desktop.split('@')[0]
        domain = argb.desktop.split('@')[1]

        if not nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()

        argb.password = remove_eol(argb.password)

        proxy_type = None
        if argb.tor or domain.endswith('.onion'):
            proxy_type = 'tor'
            if domain.endswith('.onion'):
                argb.port = 80
        elif argb.i2p or domain.endswith('.i2p'):
            proxy_type = 'i2p'
            if domain.endswith('.i2p'):
                argb.port = 80
        elif argb.gnunet:
            proxy_type = 'gnunet'

        # only store inbox posts if we are not running as a daemon
        store_inbox_posts = not argb.noKeyPress

        run_desktop_client(base_dir, proxy_type, http_prefix,
                           nickname, domain, port, argb.password,
                           argb.screenreader, argb.language,
                           argb.notificationSounds,
                           argb.notificationType,
                           argb.noKeyPress,
                           store_inbox_posts,
                           argb.notifyShowNewPosts,
                           argb.language,
                           argb.debug, argb.low_bandwidth)
        sys.exit()

    if federation_list:
        print('Federating with: ' + str(federation_list))
    if argb.shared_items_federated_domains:
        print('Federating shared items with: ' +
              argb.shared_items_federated_domains)

    shared_items_federated_domains = []
    if argb.shared_items_federated_domains:
        fed_domains_str = argb.shared_items_federated_domains
        set_config_param(base_dir, 'sharedItemsFederatedDomains',
                         fed_domains_str)
    else:
        fed_domains_str = \
            get_config_param(base_dir, 'sharedItemsFederatedDomains')
    if fed_domains_str:
        fed_domains_list = fed_domains_str.split(',')
        for shared_federated_domain in fed_domains_list:
            federated_domain = shared_federated_domain.strip()
            shared_items_federated_domains.append(federated_domain)

    if argb.block:
        if not nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        if '@' in argb.block:
            blocked_domain = argb.block.split('@')[1]
            blocked_domain = remove_eol(blocked_domain)
            blocked_nickname = argb.block.split('@')[0]
            blocked_actor = http_prefix + '://' + blocked_domain + \
                '/users/' + blocked_nickname
            argb.block = blocked_actor
        else:
            if '/users/' not in argb.block:
                print(argb.block + ' does not look like an actor url')
                sys.exit()

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending block of ' + argb.block)

        send_block_via_server(base_dir, session, nickname, argb.password,
                              domain, port,
                              http_prefix, argb.block,
                              cached_webfingers, person_cache,
                              True, __version__, signing_priv_key_pem)
        for i in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.mute:
        if not nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending mute of ' + argb.mute)

        send_mute_via_server(base_dir, session, nickname, argb.password,
                             domain, port,
                             http_prefix, argb.mute,
                             cached_webfingers, person_cache,
                             True, __version__, signing_priv_key_pem)
        for i in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.unmute:
        if not nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending undo mute of ' + argb.unmute)

        send_undo_mute_via_server(base_dir, session, nickname, argb.password,
                                  domain, port,
                                  http_prefix, argb.unmute,
                                  cached_webfingers, person_cache,
                                  True, __version__, signing_priv_key_pem)
        for i in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.unblock:
        if not nickname:
            print('Specify a nickname with the --nickname option')
            sys.exit()

        if not argb.password:
            argb.password = getpass.getpass('Password: ')
            if not argb.password:
                print('Specify a password with the --password option')
                sys.exit()
        argb.password = remove_eol(argb.password)

        if '@' in argb.unblock:
            blocked_domain = argb.unblock.split('@')[1]
            blocked_domain = remove_eol(blocked_domain)
            blocked_nickname = argb.unblock.split('@')[0]
            blocked_actor = http_prefix + '://' + blocked_domain + \
                '/users/' + blocked_nickname
            argb.unblock = blocked_actor
        else:
            if '/users/' not in argb.unblock:
                print(argb.unblock + ' does not look like an actor url')
                sys.exit()

        session = create_session(proxy_type)
        person_cache = {}
        cached_webfingers = {}
        if not domain:
            domain = get_config_param(base_dir, 'domain')
        signing_priv_key_pem = None
        if argb.secure_mode:
            signing_priv_key_pem = get_instance_actor_key(base_dir, domain)
        print('Sending undo block of ' + argb.unblock)

        send_undo_block_via_server(base_dir, session, nickname, argb.password,
                                   domain, port,
                                   http_prefix, argb.unblock,
                                   cached_webfingers, person_cache,
                                   True, __version__, signing_priv_key_pem)
        for i in range(10):
            # TODO detect send success/fail
            time.sleep(1)
        sys.exit()

    if argb.filterStr:
        if not argb.nickname:
            print('Please specify a nickname')
            sys.exit()
        if add_filter(base_dir, argb.nickname, domain, argb.filterStr):
            print('Filter added to ' + argb.nickname + ': ' + argb.filterStr)
        sys.exit()

    if argb.unfilterStr:
        if not argb.nickname:
            print('Please specify a nickname')
            sys.exit()
        if remove_filter(base_dir, argb.nickname, domain, argb.unfilterStr):
            print('Filter removed from ' + argb.nickname + ': ' +
                  argb.unfilterStr)
        sys.exit()

    if argb.testdata:
        argb.language = 'en'
        city = 'London, England'
        nickname = 'testuser567'
        password = 'boringpassword'
        print('Generating some test data for user: ' + nickname)

        if os.path.isdir(base_dir + '/tags'):
            shutil.rmtree(base_dir + '/tags',
                          ignore_errors=False, onerror=None)
        if os.path.isdir(base_dir + '/accounts'):
            shutil.rmtree(base_dir + '/accounts',
                          ignore_errors=False, onerror=None)
        if os.path.isdir(base_dir + '/keys'):
            shutil.rmtree(base_dir + '/keys',
                          ignore_errors=False, onerror=None)
        if os.path.isdir(base_dir + '/media'):
            shutil.rmtree(base_dir + '/media',
                          ignore_errors=False, onerror=None)
        if os.path.isdir(base_dir + '/sharefiles'):
            shutil.rmtree(base_dir + '/sharefiles',
                          ignore_errors=False, onerror=None)
        if os.path.isdir(base_dir + '/wfendpoints'):
            shutil.rmtree(base_dir + '/wfendpoints',
                          ignore_errors=False, onerror=None)

        set_config_param(base_dir, 'registrationsRemaining',
                         str(max_registrations))

        create_person(base_dir, 'maxboardroom', domain, port, http_prefix,
                      True, False, password)
        create_person(base_dir, 'ultrapancake', domain, port, http_prefix,
                      True, False, password)
        create_person(base_dir, 'drokk', domain, port, http_prefix,
                      True, False, password)
        create_person(base_dir, 'sausagedog', domain, port, http_prefix,
                      True, False, password)

        create_person(base_dir, nickname, domain, port, http_prefix,
                      True, False, 'likewhateveryouwantscoob')
        set_skill_level(base_dir, nickname, domain, 'testing', 60)
        set_skill_level(base_dir, nickname, domain, 'typing', 50)
        set_role(base_dir, nickname, domain, 'admin')
        set_availability(base_dir, nickname, domain, 'busy')

        add_share(base_dir,
                  http_prefix, nickname, domain, port,
                  "spanner",
                  "It's a spanner",
                  "img/shares1.png",
                  1, "tool",
                  "mechanical",
                  "City", "0", "GBP",
                  "2 months",
                  debug, city, argb.language, {}, 'shares', argb.low_bandwidth,
                  argb.content_license_url)
        add_share(base_dir,
                  http_prefix, nickname, domain, port,
                  "witch hat",
                  "Spooky",
                  "img/shares2.png",
                  1, "hat",
                  "clothing",
                  "City", "0", "GBP",
                  "3 months",
                  debug, city, argb.language, {}, 'shares', argb.low_bandwidth,
                  argb.content_license_url)

        delete_all_posts(base_dir, nickname, domain, 'inbox')
        delete_all_posts(base_dir, nickname, domain, 'outbox')

        test_save_to_file = True
        test_c2s = False
        test_comments_enabled = True
        test_attach_image_filename = None
        test_media_type = None
        test_image_description = None
        test_city = 'London, England'
        test_in_reply_to = None
        test_in_reply_to_atom_uri = None
        test_subject = None
        test_schedule_post = False
        test_event_date = None
        test_event_time = None
        test_event_end_time = None
        test_location = None
        test_is_article = False
        conversation_id = None
        low_bandwidth = False
        languages_understood = [argb.language]
        translate = {}

        create_public_post(base_dir, nickname, domain, port, http_prefix,
                           "like this is totally just a #test man",
                           test_save_to_file,
                           test_c2s,
                           test_comments_enabled,
                           test_attach_image_filename,
                           test_media_type, test_image_description, test_city,
                           test_in_reply_to, test_in_reply_to_atom_uri,
                           test_subject, test_schedule_post,
                           test_event_date, test_event_time,
                           test_event_end_time, test_location,
                           test_is_article, argb.language, conversation_id,
                           low_bandwidth, argb.content_license_url,
                           languages_understood, translate)
        create_public_post(base_dir, nickname, domain, port, http_prefix,
                           "Zoiks!!!",
                           test_save_to_file,
                           test_c2s,
                           test_comments_enabled,
                           test_attach_image_filename,
                           test_media_type, test_image_description, test_city,
                           test_in_reply_to, test_in_reply_to_atom_uri,
                           test_subject, test_schedule_post,
                           test_event_date, test_event_time,
                           test_event_end_time, test_location,
                           test_is_article, argb.language, conversation_id,
                           low_bandwidth, argb.content_license_url,
                           languages_understood, translate)
        create_public_post(base_dir, nickname, domain, port, http_prefix,
                           "Hey scoob we need like a hundred more #milkshakes",
                           test_save_to_file,
                           test_c2s,
                           test_comments_enabled,
                           test_attach_image_filename,
                           test_media_type, test_image_description, test_city,
                           test_in_reply_to, test_in_reply_to_atom_uri,
                           test_subject, test_schedule_post,
                           test_event_date, test_event_time,
                           test_event_end_time, test_location,
                           test_is_article, argb.language, conversation_id,
                           low_bandwidth, argb.content_license_url,
                           languages_understood, translate)
        create_public_post(base_dir, nickname, domain, port, http_prefix,
                           "Getting kinda spooky around here",
                           test_save_to_file,
                           test_c2s,
                           test_comments_enabled,
                           test_attach_image_filename,
                           test_media_type, test_image_description, test_city,
                           'someone', test_in_reply_to_atom_uri,
                           test_subject, test_schedule_post,
                           test_event_date, test_event_time,
                           test_event_end_time, test_location,
                           test_is_article, argb.language, conversation_id,
                           low_bandwidth, argb.content_license_url,
                           languages_understood, translate)
        create_public_post(base_dir, nickname, domain, port, http_prefix,
                           "And they would have gotten away with it too" +
                           "if it wasn't for those pesky hackers",
                           test_save_to_file,
                           test_c2s,
                           test_comments_enabled,
                           'img/logo.png', 'image/png',
                           'Description of image', test_city,
                           test_in_reply_to, test_in_reply_to_atom_uri,
                           test_subject, test_schedule_post,
                           test_event_date, test_event_time,
                           test_event_end_time, test_location,
                           test_is_article, argb.language, conversation_id,
                           low_bandwidth, argb.content_license_url,
                           languages_understood, translate)
        create_public_post(base_dir, nickname, domain, port, http_prefix,
                           "man these centralized sites are like the worst!",
                           test_save_to_file,
                           test_c2s,
                           test_comments_enabled,
                           test_attach_image_filename,
                           test_media_type, test_image_description, test_city,
                           test_in_reply_to, test_in_reply_to_atom_uri,
                           test_subject, test_schedule_post,
                           test_event_date, test_event_time,
                           test_event_end_time, test_location,
                           test_is_article, argb.language, conversation_id,
                           low_bandwidth, argb.content_license_url,
                           languages_understood, translate)
        create_public_post(base_dir, nickname, domain, port, http_prefix,
                           "another mystery solved #test",
                           test_save_to_file,
                           test_c2s,
                           test_comments_enabled,
                           test_attach_image_filename,
                           test_media_type, test_image_description, test_city,
                           test_in_reply_to, test_in_reply_to_atom_uri,
                           test_subject, test_schedule_post,
                           test_event_date, test_event_time,
                           test_event_end_time, test_location,
                           test_is_article, argb.language, conversation_id,
                           low_bandwidth, argb.content_license_url,
                           languages_understood, translate)
        create_public_post(base_dir, nickname, domain, port, http_prefix,
                           "let's go bowling",
                           test_save_to_file,
                           test_c2s,
                           test_comments_enabled,
                           test_attach_image_filename,
                           test_media_type, test_image_description, test_city,
                           test_in_reply_to, test_in_reply_to_atom_uri,
                           test_subject, test_schedule_post,
                           test_event_date, test_event_time,
                           test_event_end_time, test_location,
                           test_is_article, argb.language, conversation_id,
                           low_bandwidth, argb.content_license_url,
                           languages_understood, translate)
        domain_full = domain + ':' + str(port)
        clear_follows(base_dir, nickname, domain)
        follow_person(base_dir, nickname, domain, 'maxboardroom', domain_full,
                      federation_list, False, False)
        follow_person(base_dir, nickname, domain, 'ultrapancake', domain_full,
                      federation_list, False, False)
        follow_person(base_dir, nickname, domain, 'sausagedog', domain_full,
                      federation_list, False, False)
        follow_person(base_dir, nickname, domain, 'drokk', domain_full,
                      federation_list, False, False)
        add_follower_of_person(base_dir, nickname, domain, 'drokk',
                               domain_full, federation_list, False, False)
        add_follower_of_person(base_dir, nickname, domain, 'maxboardroom',
                               domain_full, federation_list, False, False)
        set_config_param(base_dir, 'admin', nickname)

    # set a lower bound to the maximum mentions
    # so that it can't be accidentally set to zero and disable replies
    argb.max_mentions = max(argb.max_mentions, 4)

    registration = get_config_param(base_dir, 'registration')
    if not registration:
        registration = False

    map_format = get_config_param(base_dir, 'mapFormat')
    if map_format:
        argb.mapFormat = map_format
    else:
        set_config_param(base_dir, 'mapFormat', argb.mapFormat)

    minimumvotes = get_config_param(base_dir, 'minvotes')
    if minimumvotes:
        argb.minimumvotes = int(minimumvotes)

    content_license_url = ''
    if argb.content_license_url:
        content_license_url = argb.content_license_url
        set_config_param(base_dir, 'contentLicenseUrl', content_license_url)
    else:
        content_license_url = get_config_param(base_dir, 'contentLicenseUrl')

    votingtime = get_config_param(base_dir, 'votingtime')
    if votingtime:
        argb.votingtime = votingtime

    # only show the date at the bottom of posts
    dateonly = get_config_param(base_dir, 'dateonly')
    if dateonly:
        argb.dateonly = dateonly

    # set the maximum number of newswire posts per account or rss feed
    max_newswire_posts_per_source = \
        get_config_param(base_dir, 'maxNewswirePostsPerSource')
    if max_newswire_posts_per_source:
        argb.max_newswire_posts_per_source = \
            int(max_newswire_posts_per_source)

    # set the maximum number of newswire posts appearing in the right column
    max_newswire_posts = \
        get_config_param(base_dir, 'maxNewswirePosts')
    if max_newswire_posts:
        argb.max_newswire_posts = int(max_newswire_posts)

    # set the maximum size of a newswire rss/atom feed in Kilobytes
    max_newswire_feed_size_kb = \
        get_config_param(base_dir, 'maxNewswireFeedSizeKb')
    if max_newswire_feed_size_kb:
        argb.max_newswire_feed_size_kb = int(max_newswire_feed_size_kb)

    max_mirrored_articles = \
        get_config_param(base_dir, 'maxMirroredArticles')
    if max_mirrored_articles is not None:
        argb.max_mirrored_articles = int(max_mirrored_articles)

    max_news_posts = \
        get_config_param(base_dir, 'maxNewsPosts')
    if max_news_posts is not None:
        argb.max_news_posts = int(max_news_posts)

    max_followers = \
        get_config_param(base_dir, 'maxFollowers')
    if max_followers is not None:
        argb.max_followers = int(max_followers)

    max_feed_item_size_kb = \
        get_config_param(base_dir, 'maxFeedItemSizeKb')
    if max_feed_item_size_kb is not None:
        argb.max_feed_item_size_kb = int(max_feed_item_size_kb)

    dormant_months = \
        get_config_param(base_dir, 'dormantMonths')
    if dormant_months is not None:
        argb.dormant_months = int(dormant_months)

    send_threads_timeout_mins = \
        get_config_param(base_dir, 'sendThreadsTimeoutMins')
    if send_threads_timeout_mins is not None:
        argb.send_threads_timeout_mins = int(send_threads_timeout_mins)

    max_like_count = \
        get_config_param(base_dir, 'maxLikeCount')
    if max_like_count is not None:
        argb.max_like_count = int(max_like_count)

    show_publish_as_icon = \
        get_config_param(base_dir, 'showPublishAsIcon')
    if show_publish_as_icon is not None:
        argb.show_publish_as_icon = bool(show_publish_as_icon)

    icons_as_buttons = \
        get_config_param(base_dir, 'iconsAsButtons')
    if icons_as_buttons is not None:
        argb.icons_as_buttons = bool(icons_as_buttons)

    rss_icon_at_top = \
        get_config_param(base_dir, 'rssIconAtTop')
    if rss_icon_at_top is not None:
        argb.rss_icon_at_top = bool(rss_icon_at_top)

    publish_button_at_top = \
        get_config_param(base_dir, 'publishButtonAtTop')
    if publish_button_at_top is not None:
        argb.publish_button_at_top = bool(publish_button_at_top)

    full_width_tl_button_header = \
        get_config_param(base_dir, 'fullWidthTlButtonHeader')
    if full_width_tl_button_header is not None:
        argb.full_width_tl_button_header = bool(full_width_tl_button_header)

    allow_local_network_access = \
        get_config_param(base_dir, 'allowLocalNetworkAccess')
    if allow_local_network_access is not None:
        argb.allow_local_network_access = bool(allow_local_network_access)

    verify_all_signatures = \
        get_config_param(base_dir, 'verifyAllSignatures')
    if verify_all_signatures is not None:
        argb.verify_all_signatures = bool(verify_all_signatures)

    broch_mode = get_config_param(base_dir, 'brochMode')
    if broch_mode is not None:
        argb.broch_mode = bool(broch_mode)

    dyslexic_font = get_config_param(base_dir, 'dyslexicFont')
    if dyslexic_font is not None:
        argb.dyslexic_font = bool(dyslexic_font)

    log_login_failures = \
        get_config_param(base_dir, 'logLoginFailures')
    if log_login_failures is not None:
        argb.log_login_failures = bool(log_login_failures)

    show_node_info_accounts = \
        get_config_param(base_dir, 'showNodeInfoAccounts')
    if show_node_info_accounts is not None:
        argb.show_node_info_accounts = bool(show_node_info_accounts)

    show_node_info_version = \
        get_config_param(base_dir, 'showNodeInfoVersion')
    if show_node_info_version is not None:
        argb.show_node_info_version = bool(show_node_info_version)

    low_bandwidth = \
        get_config_param(base_dir, 'lowBandwidth')
    if low_bandwidth is not None:
        argb.low_bandwidth = bool(low_bandwidth)

    user_agents_blocked = []
    if argb.userAgentBlocks:
        user_agents_blocked_str = argb.userAgentBlocks
        set_config_param(base_dir, 'userAgentsBlocked',
                         user_agents_blocked_str)
    else:
        user_agents_blocked_str = \
            get_config_param(base_dir, 'userAgentsBlocked')
    if user_agents_blocked_str:
        agent_blocks_list = user_agents_blocked_str.split(',')
        for user_agents_blocked_str2 in agent_blocks_list:
            user_agents_blocked.append(user_agents_blocked_str2.strip())

    crawlers_allowed = []
    if argb.crawlersAllowed:
        crawlers_allowed_str = argb.crawlersAllowed
        set_config_param(base_dir, 'crawlersAllowed', crawlers_allowed_str)
    else:
        crawlers_allowed_str = \
            get_config_param(base_dir, 'crawlersAllowed')
    if crawlers_allowed_str:
        crawlers_allowed_list = crawlers_allowed_str.split(',')
        for crawlers_allowed_str2 in crawlers_allowed_list:
            crawlers_allowed.append(crawlers_allowed_str2.strip())

    lists_enabled = ''
    if argb.lists_enabled:
        lists_enabled = argb.lists_enabled
        set_config_param(base_dir, 'listsEnabled', lists_enabled)
    else:
        lists_enabled = get_config_param(base_dir, 'listsEnabled')

    city = \
        get_config_param(base_dir, 'city')
    if city is not None:
        argb.city = city

    yt_domain = get_config_param(base_dir, 'youtubedomain')
    if yt_domain:
        if '://' in yt_domain:
            yt_domain = yt_domain.split('://')[1]
        if '/' in yt_domain:
            yt_domain = yt_domain.split('/')[0]
        if '.' in yt_domain:
            argb.yt_replace_domain = yt_domain

    twitter_domain = get_config_param(base_dir, 'twitterdomain')
    if twitter_domain:
        if '://' in twitter_domain:
            twitter_domain = twitter_domain.split('://')[1]
        if '/' in twitter_domain:
            twitter_domain = twitter_domain.split('/')[0]
        if '.' in twitter_domain:
            argb.twitter_replacement_domain = twitter_domain

    if set_theme(base_dir, theme_name, domain,
                 argb.allow_local_network_access, argb.language,
                 argb.dyslexic_font, False):
        print('Theme set to ' + theme_name)

    # whether new registrations are open or closed
    if argb.registration:
        if argb.registration.lower() == 'open':
            registration = get_config_param(base_dir, 'registration')
            if not registration:
                set_config_param(base_dir, 'registrationsRemaining',
                                 str(max_registrations))
            else:
                if registration != 'open':
                    set_config_param(base_dir, 'registrationsRemaining',
                                     str(max_registrations))
            set_config_param(base_dir, 'registration', 'open')
            print('New registrations open')
        else:
            set_config_param(base_dir, 'registration', 'closed')
            print('New registrations closed')

    default_currency = get_config_param(base_dir, 'defaultCurrency')
    if not default_currency:
        set_config_param(base_dir, 'defaultCurrency', 'EUR')
    if argb.defaultCurrency:
        if argb.defaultCurrency == argb.defaultCurrency.upper():
            set_config_param(base_dir, 'defaultCurrency', argb.defaultCurrency)
            print('Default currency set to ' + argb.defaultCurrency)

    opt['preferred_podcast_formats'] = preferred_podcast_formats
    opt['crawlers_allowed'] = crawlers_allowed
    opt['content_license_url'] = content_license_url
    opt['lists_enabled'] = lists_enabled
    opt['shared_items_federated_domains'] = shared_items_federated_domains
    opt['user_agents_blocked'] = user_agents_blocked
    opt['registration'] = registration
    opt['instance_id'] = instance_id
    opt['base_dir'] = base_dir
    opt['domain'] = domain
    opt['onion_domain'] = onion_domain
    opt['i2p_domain'] = i2p_domain
    opt['port'] = port
    opt['proxy_port'] = proxy_port
    opt['http_prefix'] = http_prefix
    opt['federation_list'] = federation_list
    opt['proxy_type'] = proxy_type
    opt['debug'] = debug
    return argb, opt


if __name__ == "__main__":
    argb2, opt2 = _command_options()
    print('allowdeletion: ' + str(argb2.allowdeletion))
    run_daemon(argb2.max_hashtags,
               argb2.mapFormat,
               argb2.clacks,
               opt2['preferred_podcast_formats'],
               argb2.check_actor_timeout,
               opt2['crawlers_allowed'],
               argb2.dyslexic_font,
               opt2['content_license_url'],
               opt2['lists_enabled'],
               argb2.default_reply_interval_hrs,
               argb2.low_bandwidth, argb2.max_like_count,
               opt2['shared_items_federated_domains'],
               opt2['user_agents_blocked'],
               argb2.log_login_failures,
               argb2.city,
               argb2.show_node_info_accounts,
               argb2.show_node_info_version,
               argb2.broch_mode,
               argb2.verify_all_signatures,
               argb2.send_threads_timeout_mins,
               argb2.dormant_months,
               argb2.max_newswire_posts,
               argb2.allow_local_network_access,
               argb2.max_feed_item_size_kb,
               argb2.publish_button_at_top,
               argb2.rss_icon_at_top,
               argb2.icons_as_buttons,
               argb2.full_width_tl_button_header,
               argb2.show_publish_as_icon,
               argb2.max_followers,
               argb2.max_news_posts,
               argb2.max_mirrored_articles,
               argb2.max_newswire_feed_size_kb,
               argb2.max_newswire_posts_per_source,
               argb2.dateonly,
               argb2.votingtime,
               argb2.positivevoting,
               argb2.minimumvotes,
               argb2.newsinstance,
               argb2.blogsinstance, argb2.mediainstance,
               argb2.max_recent_posts,
               not argb2.nosharedinbox,
               opt2['registration'], argb2.language, __version__,
               opt2['instance_id'], argb2.client, opt2['base_dir'],
               opt2['domain'], opt2['onion_domain'], opt2['i2p_domain'],
               argb2.yt_replace_domain,
               argb2.twitter_replacement_domain,
               opt2['port'], opt2['proxy_port'], opt2['http_prefix'],
               opt2['federation_list'], argb2.max_mentions,
               argb2.max_emoji, argb2.secure_mode,
               opt2['proxy_type'], argb2.max_replies,
               argb2.domain_max_posts_per_day,
               argb2.account_max_posts_per_day,
               argb2.allowdeletion, opt2['debug'], False,
               argb2.instance_only_skills_search, [],
               not argb2.noapproval)
