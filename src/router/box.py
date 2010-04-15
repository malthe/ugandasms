from urllib import urlencode

class SendSMS(object):
    def __init__(self, connection, username, password,
                 path="/cgi-bin/sendsms", dlr_url=None):
        self.connection = connection
        self.username = username
        self.password = password
        self.path = path

    def request(self, sender, receiver, text):
        parameters = {
            'username': self.username,
            'password': self.password,
            'from': sender,
            'to': receiver,
            'text': text,
            }

        if self.dlr_url is not None:
            parameters.update({
                'dlr-url': self.dlr_url,
                'dlr-mask': 1 | 2,
                })

        self.connection.request(
            "GET", "%s?%s" % (self.path, urlencode(parameters)))

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
