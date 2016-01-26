from cipher.irc import Plugin, Events


class MyPlugin(Plugin):
    def __init__(self, irc):
        super().__init__(irc)
        Events.privmsg += self.msg

    def msg(self, user, target, message):
        if not target.startswith('#'):
            target = user

        if message == '!test':
            data = ('PRIVMSG %s Success!' % target).encode('utf-8')
            self.irc.send(data)
