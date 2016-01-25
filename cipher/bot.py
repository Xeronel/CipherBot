import ssl
from plugins import plugins
from .event import Events
from .irc import IRC


class Bot(IRC):
    def __init__(self, host: str, port: int, nicks: list, pwd: str,
                 use_ssl: bool=False, ssl_options: ssl.SSLContext=None,
                 encoding: str='utf-8'):
        super().__init__(host, port, nicks, pwd, use_ssl, ssl_options, encoding)
        self.plugins = []
        self.__load_plugins()

    def motd(self, message):
        print(message)

    def ping(self, server1, server2):
        print('PONG %s' % server1)

    def notice(self, prefix, params, message):
        print('%s: %s' % (prefix, message))

    def privmsg(self, source, target, message):
        user = source.split('!')[0]
        print('%s | %s | %s' % (target, user, message))
        Events.privmsg.notify(user, target, message)

    def logged_in(self):
        print('Logged in!')

    def user_count(self, users, services, servers):
        print('There are %s users and %s services on %s servers' % (users, services, servers))

    def op_count(self, ops):
        print('%s operator(s) online' % ops)

    def user_parted(self, user, channel, message):
        print('%s left %s (%s)' % (user, channel, message))
        Events.part.notify(user, channel, message)

    def user_joined(self, user, channel):
        print('%s joined %s' % (user, channel))
        Events.join.notify(user, channel)

    def channel_mode(self, source, channel, mode, target):
        print('Mode %s [%s %s] by %s' % (channel, ''.join(mode), target, source))

    def user_mode(self, source, target, mode):
        print('Mode [%s %s] by %s' % (''.join(mode), target, source))

    def __load_plugins(self):
        for name, plugin in plugins:
            self.plugins.append(plugin(self))
            print('Loaded Plugin: %s' % name)
