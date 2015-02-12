#!/usr/bin/python2

""" 
A loopback bot example using LibTeletap
    The following code waits for users to send messages.
    Upon receiving them, the program will send the same text message back to the sender.
    In case of group messages, the message is sent to the original sender and to the group. 
    
    http://github.com/rohit-h/teletap
"""

from teletap import libteletap
import time

def user_responder(action, user, message):
    print ' >>> Incoming message from {0} : {1}'.format(user.user_name, message)
    print ' <<< Outgoing message for  {0} : {1}'.format(user.user_name, message)
    action.send_typing(user); time.sleep(2)
    action.send_message(user, message)


def group_responder(action, group, user, message):
    print ' >>> Incoming message from {0} on {1} : {2}'.format(user.user_name, group.group_id, message)
    action.send_message(user, message)    # Send to user
    #action.send_message(group, message)  # Send to group [Use responsibly!]


if __name__ == '__main__':
    CLIENT = libteletap.Teletap(binary='/usr/bin/telegram-cli', keyfile='/etc/telegram-cli/server.pub', logs='pingbot.log', quiet=False)
    CLIENT.attach_user_responder(user_responder)   # Attach message handler for user chats
    CLIENT.attach_group_responder(group_responder) # Attach message handler for group chats
    try:
        CLIENT.begin()        # Connect & start main event loop
    except KeyboardInterrupt:
        CLIENT.shutdown()     # Gracefully terminate client and daemon
