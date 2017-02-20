#!/usr/bin/env python3

import argparse
import io
from urllib.parse import quote, unquote, urljoin

from flask import Flask, request, Response
import lxml.etree as etree
from lxml.builder import E
from datetime import datetime, timezone

from session import Session
app = Flask(__name__)
session = Session()


def xmltv_time(epoch):
    return (
        datetime.fromtimestamp(int(epoch), tz=timezone.utc)
        .astimezone().strftime('%Y%m%d%H%M%S %z'))


@app.route('/')
def root():
    return 'Hello, world!'


@app.route('/channels')
def channels():
    out = io.StringIO()
    out.write('#EXTM3U\n')
    channels = session.fetch(action='qtnow')['payload']
    print('Got', len(channels), 'channels')
    hls_root = urljoin(request.url_root, '/hls/')
    for channel in channels:
        out.write('#EXTINF:-1 tvg-name="%s" tvg-chno="%s",%s\n' % (
            channel['channame'].strip().replace(' ', '_'),
            channel['channum'].strip(),
            channel['channame'].strip()
        ))
        out.write(urljoin(hls_root, quote(channel['hlsurl'], safe='')))
        out.write('\n')
    return Response(out.getvalue(), mimetype='application/x-mpegurl')


@app.route('/hls/<path:url>')
def hls(url):
    url = unquote(url)
    print('Accessing HLS', url)
    hls = session.get(url)
    return Response(
        hls.text.replace('/video/', 'https://tv.byu.edu/video/'),
        mimetype='application/x-mpegurl')


@app.route('/epg')
def epg():
    tv = E.tv({
        'source-info-url': 'https://tv.byu.edu/',
        'source-info-name': 'BYU Campus IPTV',
        'generator-info-name': 'kodi-byu-iptv',
        'generator-info-url': 'https://github.com/kupiakos/kodi-byu-iptv',
    })

    channels = session.fetch(action='qtnow')['payload']
    print('Generating EPG for', len(channels), 'channels')

    for channel in channels:
        ce = E.channel(
            E('display-name',
              channel['channame'].strip()),
            E.icon(src='https://tvpilot.byu.edu/logos/%s.png' % channel['guideid']),
            id=channel['channame'].strip().replace(' ', '_'),
            # id=channel['guideid'],
        )
        tv.append(ce)

    for channel in channels:
        pe = E.programme(
            E.title(channel['title']),
            E.desc(channel.get('longDescription').strip() or channel['description']),
            E.category(channel['category']),
            # TODO: Investigate the alternative icons on the site
            E.icon(src='https://tv.byu.edu/cgi-bin/epgicon-tms2.cgi?s=' + channel['epgid']),
            start=xmltv_time(channel['gmtepochstart']),
            stop=xmltv_time(channel['gmtepochend']),
            channel=channel['channame'].strip().replace(' ', '_'),
            # channel=channel['guideid'],
        )
        if channel['subtitle']:
            pe.append(E('sub-title', channel['subtitle']))
        if channel['firstrun'].lower() == 'true':
            pe.append(E.premiere())
        if channel['rating']:
            pe.append(E.rating(
                E.value('TV-' + channel['rating'][2:]),
                E.icon(src='https://tv.byu.edu/ratings/ratingspng/%s.png' % channel['rating']),
                system='VCHIP'))
        if channel['mpaa']:
            pe.append(E.rating(
                E.value(channel['mpaa']),
                E.icon(src='https://tv.byu.edu/ratings/ratingspng/%s.png' % channel['rating']),
                system='MPAA'))
        tv.append(pe)

    return Response(etree.tostring(
        etree.ElementTree(tv),
        xml_declaration=True, encoding='utf-8',
        # encoding='unicode', pretty_print=True,
        # doctype='<!DOCTYPE tv SYSTEM "xmltv.dtd">',
    ), mimetype='application/xml')


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
