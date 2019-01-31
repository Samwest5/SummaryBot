import secretKeys
from summarize import get_summary, get_hits
import time
from slackclient import SlackClient
from wikipedia.exceptions import DisambiguationError

TOKEN = secretKeys.SLACK_API_TOKEN
NAME = secretKeys.SLACK_BOT_NAME
ID = secretKeys.SlACK_BOT_ID
DELAY = .1
BOT_MENTION = f"<@{ID}>"

slack_client = SlackClient(TOKEN)


def is_bot_command(event):
    event_type = event.get('type')
    print(event)
    if event_type == 'message' and not event.get('user') == ID:
        text = event.get('text')
        if text.strip().startswith(BOT_MENTION):
            return True
    return False


def get_options(topic):
    return get_hits(topic)


def check_argument(message):
    return len(message.split(' ', 1)) == 2


def handle_command(message, channel, user):
    if check_argument(message):
        topic = message.split(' ', 1)[1]
    else:
        return

    options = get_options(topic)

    if len(options) == 0:
        message = "_Sorry, I couldn't find any matches to that topic :(_"
        post_message(message, channel)

    elif len(options) == 1:
        message = get_summary(topic)
        post_message(message, channel)

    # If more than one option is available
    # bot will ask user for which one to summarize
    # bot only accepts input from original user
    else:
        post_options(options, channel)
        counter = 20
        while counter != 0:
            events = slack_client.rtm_read()
            for event in events:
                if is_bot_command(event) and user == event.get('user') and channel == event.get('channel'):

                    text = event.get('text')
                    if check_argument(text):
                        choice = text.split(' ', 1)[1]
                    else:
                        return

                    if choice.isdigit() and 1 <= int(choice) <= (len(options)):
                        try:
                            summary = get_summary(options[int(choice) - 1])
                            post_message(summary, channel)
                            return
                        except DisambiguationError:
                            post_message("Something went wrong :(", channel)
                            return

                    else:
                        message = "Input not recognized. You will have to restart summary request"
                        post_message(message, channel)
                        return
            time.sleep(1)
            counter -= 1

        post_option_timeout(channel)





def post_option_timeout(channel):
    message = "smmryme timed out. You will have to restart the summary request"
    slack_client.api_call('chat.postMessage',
                          channel=channel,
                          text=message,
                          as_user=True)

def post_message(message, channel):
    slack_client.api_call('chat.postMessage',
                          channel=channel,
                          text=message,
                          as_user=True)


def post_options(options, channel):

    notice = "Which topic did you mean?"
    for i in range(len(options)):
        line = f'\n{i+1}. {options[i]}'
        notice += line
    notice += "\nType @smmryme {number} to choose"

    slack_client.api_call('chat.postMessage',
                          channel=channel,
                          text=notice,
                          as_user=True)


def run():
    if slack_client.rtm_connect():
        while True:
            events = slack_client.rtm_read()
            for event in events:
                if is_bot_command(event):
                    handle_command(message=event.get('text'),
                                   channel=event.get('channel'),
                                   user=event.get('user'))
            time.sleep(.1)


if __name__ == '__main__':
    run()
