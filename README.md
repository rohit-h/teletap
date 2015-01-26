# Teletap - Telegram wrapper library for telegram-cli
 An easy to use Python wrapper library for Telegram (telegram-cli v1.1.1) daemon over network sockets

----

## Prerequisites

It is assumed that you already have `telegram-cli` up and running and that you able to login.
If you haven't, visit https://github.com/vysheng/tg, run the program and sign-in with your existing account or register for a new one.

## Usage

There are five basic elements/object references you will need to pay attention to in this design:

1. **Client**: Teletap object used to initialize the telegram-cli daemon, listen for unread messages and attaching message response handlers.
2. **User**: Class-type that contains user information. Currently accessible instance fields are : user_id, user_name, user_phone, user_handle, user_last_seen
3. **Group**: Class-type to store group ID for now. More methods to be added as we find more useful things to do with it.
4. **Action**: Client interactions within a message handler are done through the Action instance. Currently supported methods are : `send_message(User, message)` and `send_typing(User)` with more to be added in the near future.
5. **Handlers**: These are user-defined methods that can be used to process incoming messages. The method signature is

		def message_handler(action, user, message, group=None):
			# This function can be attached to both user/group responders in the client
			# since it contains the group argument. The function needs to take care of 
			# knowing where the message is coming from depending on group == None being
			# True or False
	


----

## Examples

### Loopback test

The following code waits for users to send messages. Upon receiving them, the program will send the same text message back to the sender. In case of group messages, the message is sent to the original sender and to the group

	#!/usr/bin/python2
	from libteletap import *
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
	    CLIENT = Teletap(binary='/usr/bin/telegram-cli', keyfile='/etc/telegram-cli/tg-server.pub', logs='/var/log/telegram.log', quiet=False)
	    CLIENT.attach_user_responder(user_responder)   # Attach message handler for user chats
	    CLIENT.attach_group_responder(group_responder) # Attach message handler for group chats
	    try:
	        CLIENT.begin()        # Connect & start main event loop
	    except KeyboardInterrupt:
	        CLIENT.shutdown()			# Gracefully terminate client and daemon

### Turing test / Rise of the chatbots

Using cleverbot to (cleverly?) respond to user texts. Do be careful and monitor this if you want to avoid awkward situations.

You might need to install cleverbot if you haven't already:

	sudo pip2 install cleverbot

Code:

	#!/usr/bin/python2
	from libteletap import *
	import cleverbot
	
	cbot = cleverbot.Cleverbot()
	
	def say_something_clever(action, user, message):
	    print ' >>> Incoming message from {0} : {1}'.format(user.user_name, message)
	    action.send_typing(user)     # 'typing' or rather, thinking!
	    response = cbot.ask(message)
	    print ' <<< Outgoing message for  {0} : {1}'.format(user.user_name, response)
	    action.send_message(user, response)
	
	if __name__ == '__main__':
	    CLIENT = Teletap(binary='/usr/bin/telegram-cli', keyfile='/etc/telegram-cli/tg-server.pub', logs='/var/log/telegram.log', quiet=False)
	    CLIENT.attach_user_responder(say_something_clever)  # Attach message handler for user chats
	    try:
	        CLIENT.begin()        # Connect & start main event loop
	    except KeyboardInterrupt:
	        CLIENT.shutdown()			# Gracefully terminate client and daemon
