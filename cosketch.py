import time
import json
from urllib import urlencode

import gevent
from gevent.queue import Queue

import requests

class CosketchSession(object):
    
    def __init__(self, nick, channel):

        self.channel = channel
        self.uid = round(time.time(),5)
        self.user_id = None
        self.lc = -1
        self._pc_base = str(int(time.time()*1000))
        self._pc = 0
        self.sc = 0

        self.action_queue = Queue()
        self.event_queue = Queue()

        self.session = requests.session()

        # set cookies and authenticate
        self.session.get('http://cosketch.com/Rooms/'+channel)
        self.session.post(self.upload_url, {'d': '["Login"]'})

        self.set_nick(nick)

    @property
    def pc(self):
        return self._pc_base + str(self._pc)

    @property
    def upload_url(self):
        return 'http://cosketch.com/Upload.aspx?'+urlencode({
            'channel': self.channel,
            'U': self.uid,
            'LC': self.lc,
            't': 'n',
        })

    @property
    def download_url(self):
        return 'http://cosketch.com/Download.aspx?'+urlencode({
            'channel': self.channel,
            'U':  self.uid,
            'LC': self.lc,
            'pc': self.pc,
            't': 'n',
        })

    def d(self, data):
        self.sc += 1
        return {'d': '{"v":71,"ul":[[%s,%s]]}' % (self.sc, data)}

    def run(self):
        gevent.spawn(self.event_dispatcher)
        gevent.spawn(self.process_action_queue)
        while True:
            response = self.session.get(self.download_url)

            if response.content == "REFRESH":
                continue

            parsed = json.loads(response.content)
            self.lc = parsed['myLast']
            self._pc += 1

            self.event_queue.put(parsed['dl'])


    def event_dispatcher(self):
        while True:
            event = self.event_queue.get()

            # older than 10 secs?
            if event[0][2]-10000 > int(time.time()*1000):
                continue

            print 'EVENT:',event

            try:
                if event[0][3][0] == 'ChangedName' and \
                   event[0][3][2] == self.nick:
                    self.user_id = event[0][3][1]

                if event[0][3][0] == 'Chat' and event[0][1] != self.user_id:
                    if event[0][3][1] == '!fortune':
                        import os
                        p = os.popen('fortune -s')
                        fortune = p.read()
                        fortune = ' '.join(fortune.split()).replace('\n',' ')
                        self.chat(fortune)
                    elif event[0][3][1].split()[0] == '!rand':
                        from random import randrange
                        for i in xrange(0, int(event[0][3][1].split()[1])):
                            x1, y1 = randrange(0,800), randrange(0,600)
                            x2, y2 = randrange(0,800), randrange(0,600)
                            width = randrange(1,5)
                            self.stroke([x1, y1, x2, y2], '#000000', width)
                    elif event[0][3][1] == '!hello':
                        self.chat('hello " world')
            except:
                pass
    
    def process_action_queue(self):
        while True:
            data = self.action_queue.get()
            response = self.session.post(self.upload_url, data)
            print response.content

    def stroke(self, points, color, width):

        if type(points[0]) is not int:
            points = [p for point in points for p in point]

        data = self.d('["Stroke",0,"%s",%s,%s,255]' % (color,width,points))
        self.stroke_queue.append(data)

    def set_nick(self, nick):
        self.nick = nick.replace('"','\\"')

        data = self.d('["RequestNameChange","%s"]' % self.nick)
        self.action_queue.put(data)

    def chat(self, message):
        data = self.d('["Chat","%s"]' % message.replace('"','\\"'))
        self.action_queue.put(data)

if __name__ == '__main__':

    c = CosketchSession('sketchr', 'udderweb2')

    points = [(303,183),(301,185),(299,187),(298,189),(295,191),(293,194),
              (291,196),(288,198),(286,200),(284,202),(281,204),(279,205),
              (276,207),(274,209),(272,211),(271,212),(270,214),(269,215),
              (268,216),(267,216),(265,217),(263,218),(262,219),(261,219),
              (260,220),(258,220),(258,221),(257,222),(256,223)]

    c.chat('hello world!')

    c.stroke(points, '#000000',3)
    c.stroke(points, '#FF0000',5)
    c.stroke(points, '#00FF00',7)
    c.stroke(points, '#0000FF',9)

    c.stroke([0,0,200,200], '#FF0000', 5)
    c.stroke([200,0,0,200], '#00FF00', 5)
    c.stroke([100,0,100,200], '#0000FF', 5)

    c.run()
