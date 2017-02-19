#!/usr/bin/env python3

import argparse
import io
from urllib.parse import quote, unquote, urljoin

from flask import Flask, request
from session import Session
app = Flask(__name__)
session = Session()


@app.route('/')
def root():
    return 'Hello, world!'


@app.route('/channels')
def channels():
    out = io.StringIO()
    out.write('#EXTM3U\n')
    data = session.fetch(action='qtnow').json()
    assert data['result'] == 'OK'
    print('Got', len(data['payload']), 'channels')
    hls_root = urljoin(request.url_root, '/hls/')
    for channel in data['payload']:
        out.write('#EXTINF:-1 tvg-id="%s" tvg-name="%s",%s\n' % (
            channel['guideid'], channel['channame'].strip().replace(' ', '_'),
            channel['channame'].strip()
        ))
        out.write(urljoin(hls_root, quote(channel['hlsurl'], safe='')))
        out.write('\n')
    return out.getvalue()


@app.route('/hls/<path:url>')
def hls(url):
    url = unquote(url)
    print('Accessing HLS', url)
    hls = session.get(url)
    return hls.text.replace('/video/', 'https://tv.byu.edu/video/')


def main():
    parser = argparse.ArgumentParser(
        description='Create a wrapper server to allow BYU IPTV to'
        'work with the IPTV Simple PVR Client on Kodi')
    parser.add_argument('netid', help='Your BYU Net ID')
    parser.add_argument('studentid', help='Your BYU Numeric Student ID')
    parser.add_argument(
        '-p', '--port', type=int, default=9090,
        help='The port to run the server on')
    parser.add_argument(
        '-d', '--debug', action='store_true',
        help='Run Flask in Debug mode')
    args = parser.parse_args()
    session.set_login(args.netid, args.studentid)
    app.run(port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
