import os

from flask import Flask, request
from fbmessenger import BaseMessenger
from fbmessenger.templates import GenericTemplate
from fbmessenger.elements import Text, Button, Element
from fbmessenger import quick_replies
from fbmessenger.attachments import Image

global dialogue
dialogue = set()


def get_button(ratio):
    return Button(
        button_type='web_url',
        title='Ulaanbaatar Live',
        url='http://11-11.mn/live/',
        webview_height_ratio=ratio,
    )


def get_element(btn):
    return Element(
        title='Ulaanbaatar',
        item_url='http://11-11.mn',
        image_url='https://media-cdn.tripadvisor.com/media/photo-s/0e/2f/a9/86/ulaanbaatar-explorer.jpg',
        subtitle='See Ulaanbaatar live',
        buttons=[btn]
    )


class Messenger(BaseMessenger):
    def __init__(self, page_access_token):
        self.page_access_token = page_access_token
        super(Messenger, self).__init__(self.page_access_token)

    def message(self, message):
        app.logger.debug(message)
        global dialogue
        if 'text' in message['message']:
            msg = message['message']['text'].lower()
            if len(dialogue) == 6:
                dialogue = set()

            # Greetings
            if msg in ["hi", "hi there", "hello", "sain bainuu", "сайн уу", "hey", "yo"]:
                user_info = self.get_user()
                response = Image(url='https://i.ytimg.com/vi/penG2V8bMBE/maxresdefault.jpg')
                self.send(response.to_dict(), 'RESPONSE')
                response = Text(text='Hello {}! I’m SMART CITY chatbot 🤖, I can offer you municipality service everywhere at any time. You can message me about road issues. '.format(user_info['first_name']))
                self.send(response.to_dict(), 'RESPONSE')
                qr1 = quick_replies.QuickReply(title='Open issue', payload='open_issue')
                qr2 = quick_replies.QuickReply(title='Live city', payload='live_city')
                qrs = quick_replies.QuickReplies(quick_replies=[qr1, qr2])
                response = Text(text='How can I help you today?', quick_replies=qrs)
                self.send(response.to_dict(), 'RESPONSE')
                dialogue.add('Greetings')

            # Phone number
            if dialogue == {'Greetings', 'Name'}:
                response = Text(text='Please enter your phone number:')
                self.send(response.to_dict(), 'RESPONSE')
                dialogue.add('Phone')

            # Problem description
            elif dialogue == {'Greetings', 'Name', 'Phone'}:
                response = Text(text='Please describe the problem:')
                self.send(response.to_dict(), 'RESPONSE')
                dialogue.add('Problem')

            # Location
            elif dialogue == {'Greetings', 'Name', 'Phone', 'Problem'}:
                qr = quick_replies.QuickReply(title='Location', content_type='location')
                qrs = quick_replies.QuickReplies(quick_replies=[qr])
                response = Text(text='Please send the location of problem:', quick_replies=qrs)
                self.send(response.to_dict(), 'RESPONSE')

        # Name
        if message['message'].get('quick_reply'):
            if message['message']['quick_reply'].get('payload') == 'open_issue' and 'Greetings' in dialogue:
                response = Text(text='Please enter your full name:')
                self.send(response.to_dict(), 'RESPONSE')
                dialogue.add('Name')

        # Live city
        if message['message'].get('quick_reply'):
            if message['message']['quick_reply'].get('payload') == 'live_city' and 'Greetings' in dialogue:
                btn = get_button(ratio='compact')
                elem = get_element(btn)
                response = GenericTemplate(elements=[elem])
                self.send(response.to_dict(), 'RESPONSE')

        # Picture
        if message['message'].get('attachments'):
            if message['message']['attachments'][0].get('type') == 'location':
                response = Text(text='Please send a picture of a problem:')
                self.send(response.to_dict(), 'RESPONSE')
                dialogue.add('Location')
            # Final state
            elif message['message']['attachments'][0].get('type') == 'image':
                response = Text(text='Your ticket has been opened and we will get on it as fast as possible. If you '
                                     'want to add another issue, please just greet again. Thank you!. ')
                self.send(response.to_dict(), 'RESPONSE')
                dialogue.add('Image')

    def delivery(self, message):
        pass

    def read(self, message):
        pass

    def account_linking(self, message):
        pass

    def postback(self, message):
        pass

    def optin(self, message):
        pass


app = Flask(__name__)
app.debug = True
messenger = Messenger(os.environ.get('FB_PAGE_TOKEN'))


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == os.environ.get('FB_VERIFY_TOKEN'):
            if request.args.get('init') and request.args.get('init') == 'true':
                return ''
            return request.args.get('hub.challenge')
        raise ValueError('FB_VERIFY_TOKEN does not match.')
    elif request.method == 'POST':
        messenger.handle(request.get_json(force=True))
    return ''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
