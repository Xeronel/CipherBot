import tornado
import tornado.iostream
import socket
import ssl
import inspect


class IRC(object):
    def __init__(self, host: str, port: int, nicks: list, pwd: str,
                 use_ssl: bool=False, ssl_options: ssl.SSLContext=None,
                 encoding: str='utf-8'):
        """
        Asynchronous IRC client
        :param host: Server address
        :param port: IRC Port
        :param nicks: List of nicknames to try
        :param pwd: NickServ password
        :param use_ssl: Enable/Disable SSL
        :param ssl_options: SSLContext object
        :param encoding: Character encoding to use
        """
        self.host = host
        self.port = port
        self.nicks = nicks
        self.pwd = pwd
        self.ssl = use_ssl
        self.encoding = encoding
        self.__lines = [b'']
        self.__nickidx = 0
        self.__handlers = {
            b'PING': self.__ping,
            b'433': self.__nick_in_use,
            b'372': self.__motd
        }

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)

        if use_ssl:
            if not ssl_options:
                ssl_options = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                # IRC often has unsigned certs, by default do not verify
                ssl_options.verify_mode = ssl.CERT_NONE
            sock = ssl.wrap_socket(sock, do_handshake_on_connect=False)
            self.__stream = tornado.iostream.SSLIOStream(sock, ssl_options=ssl_options)
        else:
            self.__stream = tornado.iostream.IOStream(sock)

        self.__stream.connect((self.host, self.port),
                              self.__initial_auth,
                              server_hostname=self.host)

    def __initial_auth(self):
        """
        Attempt to authenticate and start listening for data
        """
        self.__auth()
        self.__stream.read_until_close(self.closed, self.__route)

    def send(self, data: str):
        """
        Write to stream
        :param data: String to send
        """
        if type(data) is str:
            data = data.encode(self.encoding)

        if type(data) is bytes:
            self.__stream.write(data + b'\r\n')
        else:
            raise TypeError('Data must be a byte or string')

    def __recv(self, data):
        """
        Split received data into lines
        :param data: Bytes received
        """
        # Inspircd resends lines that came through incomplete
        # other ircd's have not been tested.
        self.__lines = []

        data = data.split(b'\r\n')
        prefix = b''
        command = b''
        params = b''
        message = b''
        idx = 0

        for line in data:
            if line:
                # Get prefix
                if line.startswith(b':'):
                    idx = line.find(b' ')
                    prefix = line[1:idx]

                line = line[idx+1:].split(b' :')
                message = b''.join(line[1:])
                line = line[0].split(b' ')
                command = line[0]
                params = line[1:]

                self.__lines.append((prefix, command, params, message))

    def __route(self, data):
        """
        Monitor incoming data and dispatch it to the proper methods
        :param data: Raw byte array
        """
        data = data.split(b'\r\n')
        prefix = b''
        command = b''
        params = b''
        message = b''
        idx = 0

        for line in data:
            if line:
                if line.startswith(b':'):
                    idx = line.find(b' ')
                    prefix = line[1:idx]

                line = line[idx+1 if idx > 0 else idx:].split(b' :')
                message = b''.join(line[1:])
                line = line[0].split(b' ')
                command = line[0]
                params = line[1:]

                try:
                    handler = self.__handlers[command]
                    kwargs = inspect.signature(handler).parameters.keys()
                    if len(inspect.signature(handler).parameters) > 0:
                        irc_args = {'prefix': prefix,
                                    'command': command,
                                    'params': params,
                                    'message': message}
                        kwargs = {k: irc_args[k] for k in irc_args if k in kwargs}
                        handler(**kwargs)
                    else:
                        handler()
                except KeyError:
                    print('(Unhandled) Pfx: %s,Cmd: %s,Param: %s, Msg: %s' % (prefix, command, params, message))

    def motd(self, message):
        """
        MOTD received event
        :param message: Line of MOTD
        """
        pass

    def ping(self, server1, server2):
        """
        PING received event
        :param server1: Originating server
        :param server2: Forwarding server
        """
        pass

    def __auth(self):
        """
        Send auth data
        """
        if self.__nickidx < len(self.nicks):
            nick = self.nicks[self.__nickidx]
        else:
            nick = self.nicks[0] + str(self.__nickidx - len(self.nicks))
        self.send('NICK %s' % nick)
        self.send('USER %s 0 * :%s' % (self.nicks[0], 'realname'))

    def __nick_in_use(self):
        """
        Try another nick
        """
        self.__nickidx += 1
        self.__auth()

    def __ping(self, command, message):
        """
        Ping event handler
        :param data:
        """
        ping = message.split(b' ')
        server1 = ping[0].decode(self.encoding)
        server2 = ping[1].decode(self.encoding) if len(ping) == 2 else ''

        if server2:
            self.send('PONG %s %s' % (server1, server2))
        else:
            self.send('PONG %s' % server1)
        self.ping(server1, server2)

    def __motd(self, message):
        """
        MOTD hanlder
        :param data: MOTD line
        """
        self.motd(message)

    def closed(self, data):
        pass

