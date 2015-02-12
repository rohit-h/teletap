#!/usr/bin/python2

""" 
A bot written using LibTeletap
    Using cleverbot to (cleverly?) respond to user texts.
    requires cleverbot.py (https://github.com/folz/cleverbot.py)   
    
    http://github.com/rohit-h/teletap
"""
from teletap import libteletap
import cleverbot

cbot = cleverbot.Cleverbot()

def say_something_clever(action, user, message):
    print ' >>> Incoming message from {0} : {1}'.format(user.user_name, message)
    action.send_typing(user)     # 'typing' or rather, thinking!
    response = cbot.ask(message)
    print ' <<< Outgoing message for  {0} : {1}'.format(user.user_name, response)
    action.send_message(user, response)

if __name__ == '__main__':
    CLIENT = libteletap.Teletap(binary='/usr/bin/telegram-cli', keyfile='/etc/telegram-cli/tg-server.pub', logs='clevertelbot.log', quiet=False)
    CLIENT.attach_user_responder(say_something_clever)  # Attach message handler for user chats
    try:
        CLIENT.begin()        # Connect & start main event loop
    except KeyboardInterrupt:
        CLIENT.shutdown()           # Gracefully terminate client and daemon
