from httplib import HTTPConnection
from urllib import urlencode

class Connection(object):
    def __init__(self, host, port, username, password, path="/cgi-bin/sendsms"):
        self.connection = HTTPConnection(host, port)
        self.username = username
        self.password = password
        self.path = path

    def request(self, sender, receiver, text):
        self.connection.request(
            "GET", "%s?%s" % urlencode({
                'username': self.username,
                'password': self.password,
                'from': sender,
                'to': receiver,
                'text': text}), self.path)

    def getresponse(self):
        return self.connection.getresponse()

    def send(self, sender, receiver, text):
        self.request(sender, receiver, text)
        response = self.connection.getresponse()
        if response.status == 202:
            body = response.read()
            try:
                return int(body.split(':')[0])
            except TypeError:
                return -1
        return -2
