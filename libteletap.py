"""
LibTeletap - Tap into Telegram CLI daemon
    Useful library for building clients, automated or otherwise

    http://github.com/rohit-h/teletap
"""

import os, sys
import time, re
import socket, thread
from datetime import datetime

class User(object):

    user_id, user_name, user_phone = None, None, None
    user_handle, user_last_seen = None, None
    tg_instance = None

    def get_peer_id(self):
        return self.user_id

    def __fetch_field(self, field, index):
        print field.split()
        try:
            value = field.split()[index]
        except:
            value = ''
        return value

    def update_info(self):
        response = self.tg_instance.sock_request('user_info {0}'.format(self.user_id))
        for line in response:
            print line
            line = line.strip()
            if line.startswith('User'):
                self.user_handle = self.__fetch_field(line, 2)
            if line.startswith('phone'):
                self.user_phone = self.__fetch_field(line, 1)
            if line.startswith('real name'):
                self.user_name = str.join(' ', line.split()[2:])
            if line.startswith('online'):
                self.user_last_seen = datetime.today()
            if line.startswith('offline'):
                try:
                    timestamp = str.join(' ', line.split()[3:4])
                    self.user_last_seen = datetime.strptime(timestamp, '[%Y/%m/%d %H:%M:%S]')
                except (IndexError, ValueError):
                    self.user_last_seen = datetime(1970, 1, 1)

    def __init__(self, instance, peer_id):
        self.tg_instance = instance
        self.user_id = peer_id
        self.update_info()


class Group(object):

    group_id, tg_instance = None, None

    def __init__(self, instance, peer_id):
        self.tg_instance = instance
        self.group_id = peer_id

    def get_peer_id(self):
        return self.group_id


class Roster(object):

    USERS, GROUPS = {}, {}
    tg_instance = None

    def __init__(self, instance):
        self.tg_instance = instance

    def peer(self, peer_id):
        instance = None
        if peer_id.startswith('user'):
            instance = self.USERS[peer_id] if self.USERS.has_key(peer_id) else None
            if not instance:
                instance = User(peer_id=peer_id, instance=self.tg_instance)
                self.USERS[peer_id] = instance

        elif peer_id.startswith('chat'):
            instance = self.GROUPS[peer_id] if self.GROUPS.has_key(peer_id) else None
            if not instance:
                instance = Group(peer_id=peer_id, instance=self.tg_instance)
                self.GROUPS[peer_id] = instance

        return instance


class Action(object):

    tg_tap = None

    def __init__(self, instance):
        self.tg_tap = instance

    def send_message(self, peer, text):
        self.tg_tap.sock_command('msg {0} {1}'.format(peer.get_peer_id(), text))

    def send_typing(self, peer):
        self.tg_tap.sock_command('send_typing {0}'.format(peer.get_peer_id()))


class Teletap(object):

    PORT, HOST, BIN, PKEY = None, None, None, None
    LOGS, MSGS, BUFF_SIZE = None, True, 8192
    sock, roster, invoker, retries = None, None, None, 0

    # Message handler function references
    USERCHAT, GROUPCHAT = None, None

    def __init__(self, binary, keyfile, quiet=False, logs='teletap.log',
                 hostname='localhost', port=6666):
        self.BIN = binary
        self.PORT = port
        self.PKEY = keyfile
        self.HOST = hostname
        self.MSGS = not quiet
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.roster = Roster(instance=self)
        self.invoker = Action(instance=self)
        if logs:
            self.LOGS = open(logs, 'a')


    def attach_user_responder(self, method):
        self.USERCHAT = method


    def attach_group_responder(self, method):
        self.GROUPCHAT = method


    def start_daemon(self):
        self.log('Starting Telegram-CLI daemon on port {0}'.format(self.PORT))
        os.system('{0} -dDIN -P {1} -k {2}'.format(self.BIN, self.PORT, self.PKEY))


    def stop_daemon(self):
        try:
            self.sock_command('quit')
            time.sleep(1)
            self.log('Closing socket')
            self.sock.shutdown(1)
            self.sock.close()
            self.log(' !! Daemon has not quit. You should double-check this')
            self.sock = None
        except socket.error:
            self.log('Daemon closed the connection')


    def log(self, string):
        logstr = '[{0}] {1}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), string)
        if self.LOGS:
            self.LOGS.write(logstr)
        if self.MSGS:
            print logstr.strip()


    def connect(self):
        self.retries = self.retries + 1
        if self.retries > 5:
            self.log('Maximum number of retries reached. Stopping')
            sys.exit(1)

        try:
            self.log('Connecting to {0}:{1}'.format(self.HOST, self.PORT))
            self.sock.connect((self.HOST, self.PORT))
            self.log('Connected')
        except socket.error as ex:
            self.log('Failed to connect : {0}'.format(ex))
            thread.start_new_thread(self.start_daemon, ())
            time.sleep(2)
            self.connect()


    def sock_command(self, command):
        if '\n' in command:
            command = str.join(' ', command.strip('\n'))
        self.sock.sendall(command + '\n')
        time.sleep(0.5)


    def sock_request(self, command):
        self.sock_command(command)
        sockdata = self.sock.recv(self.BUFF_SIZE)
        response = sockdata.strip().split('\n')[1:]
        return response


    def shutdown(self):
        self.log('Trying to quit gracefully (5 seconds). Press ^C again to force')
        try:
            self.sock_command('safe_quit')
            time.sleep(3)
            self.stop_daemon()
        except KeyboardInterrupt:
            self.stop_daemon()
        self.LOGS.close()
        sys.exit(0)


    def get_dialog_list(self):
        dialogs = []
        filter_regex = r'(User|Chat) (user|chat)#[0-9]+: [0-9]+ unread'
        input_filter = re.compile(filter_regex)
        response = self.sock_request('dialog_list')
        if not response:
            return []

        for row in response:
            if not input_filter.match(row):
                continue

            tokens = row.split()
            if int(tokens[2]) == 0:    # Skip '0 unread' chats
                continue

            peer_id = tokens[1][:-1]   # For the pesky trailing ':' character
            peer_ref = self.roster.peer(peer_id)

            if peer_ref:
                dialogs.append({'peer':  peer_ref, 'count': int(tokens[2])})
        return dialogs


    def get_messages(self, dialog):
        buf = []
        count = dialog['count']
        peer = dialog['peer']

        peer_idx, msg_idx = None, None
        if isinstance(peer, User):
            header = re.compile(r'[0-9]+ \[.....\]  user')
            peer_idx = 2
            msg_idx = 4
        elif isinstance(peer, Group):
            header = re.compile(r'[0-9]+ \[.....\]  chat')
            peer_idx = 3
            msg_idx = 5
        else:
            return []

        peer_id = peer.get_peer_id()
        response = self.sock_request('history {0} {1}'.format(peer_id, count))

        # Multiline message parsing/collating
        peer_ref = self.roster.peer(response[0].split()[peer_idx])
        message = str.join(' ', response[0].split()[msg_idx:])
        for line in response[1:]:
            if header.match(line):
                if peer:
                    buf.append({'peer': peer_ref, 'message':message})
                peer_ref = self.roster.peer(response[0].split()[peer_idx])
                try:
                    message = str.join(' ', line.split()[msg_idx:])
                    print message
                except IndexError:
                    message = ''
            else:
                message += ' ' + line

        if peer:
            buf.append({'peer': peer_ref, 'message': message})
        return buf


    def loop(self):
        while True:
            dialog_list = self.get_dialog_list()
            if not dialog_list:
                time.sleep(5)
                continue

            for dialog in dialog_list:
                message_list = self.get_messages(dialog)
                peer = dialog['peer']

                if isinstance(peer, User) and self.USERCHAT:
                    for message in message_list:
                        self.USERCHAT(action=self.invoker,
                                      user=message['peer'],
                                      message=message['message'])

                elif isinstance(peer, Group) and self.GROUPCHAT:
                    for message in message_list:
                        self.GROUPCHAT(action=self.invoker,
                                       group=peer,
                                       user=message['peer'],
                                       message=message['message'])
            time.sleep(2)


    def begin(self):
        self.connect()
        self.loop()


