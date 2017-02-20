# kodi-byu-iptv
A small server written in Flask to allow Kodi to access the Beehive Broadband IPTV for BYU students.
For Python 3.2+.

## Getting the server running

First, install the requirements:

    $ pip install -r requirements.txt

Next, get the server started with your BYU NetID and Student ID (the number on your ID card).

    $ ./server.py mmoss 01189998819901197253

This acts as a "transformation" server to convert Beehive Broadband's format to something Kodi can understand.

## Kodi Setup

Install and enable the [IPTV Simple PVR Package](http://kodi.wiki/view/Add-on:IPTV_Simple_Client) for Kodi.
On Debian/Ubuntu, you may need to install the `kodi-pvr-iptvsimple` package first.

In the settings for the plugin, change the M3U Play List URL to
`http://localhost:9090/channels` (or a different port if configured).
Change the EPG URL to `http://localhost:9090/epg`.
