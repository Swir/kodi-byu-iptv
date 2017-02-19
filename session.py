
import random
import hashlib
import requests
from cachecontrol import CacheControl


class Session:
    uid = None
    token = None
    organization = None
    session = None
    netid = None
    _init = False
    _logged_in = False
    _BASE_URL = 'https://tv.byu.edu/'

    def __init__(self):
        self.session = CacheControl(requests.Session())
        self.session.headers.update({
            'Host': 'tv.byu.edu',
            'Origin': 'https://tv.byu.edu',
            'Referer': 'https://tv.byu.edu/',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 IPTV/1.0',
        })

    def genAuth(self):
        if self.uid is None:
            self.uid = str(random.randint(1, 10000000000))
            digest = hashlib.md5(
                b''.join(str(i).encode() for i in (
                    self.uid, self.netid, self.studentid))
            ).hexdigest()
        return {
            'ds': digest,
            'sid': self.netid,
            'uid': self.uid,
        }

    def getHeaders(self, asJson=True):
        headers = {}
        if asJson:
            headers.update({
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-JSON': 'true',
            })
        if self.token is None:
            headers.update(self.genAuth())
        else:
            headers['X-BEEAUTH'] = self.token
        return headers

    def fetch(self, action=None, method='POST', asJson=True, headers=None, login=True, **kwargs):
        if login and not self._logged_in:
            self.login()
        if action is not None:
            kwargs.setdefault('json', {}).update({'act': action})
        h = self.getHeaders(asJson=asJson)
        if headers is not None:
            h.update(headers)
        r = self.session.request(
            method, self._BASE_URL + 'cgi-bin/remote.cgi',
            headers=h, **kwargs)
        if not r.ok:
            r.raise_for_status()
        return r

    def get(self, url, **kwargs):
        return self.session.get(url, **kwargs)

    def set_login(self, netid, studentid):
        self.netid = netid
        self.studentid = studentid
        self._logged_in = False

    def login(self):
        print('Logging in as', self.netid)
        if not self._init:
            self.get(self._BASE_URL)
            self._init = True
        self.token = None
        self.organization = None
        response = self.fetch(action='verifycreds', login=False).json()
        assert response['result'] == 'OK'
        self.organization = response['orgName']
        self.token = response['token']
        self._logged_in = True
        print('Logged in as', self.netid)
