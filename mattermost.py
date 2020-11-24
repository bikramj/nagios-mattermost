# !/usr/bin/env python

# Copyright (c) 2015 NDrive SA
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import argparse
import json
import urllib.parse
import urllib.request

VERSION = "0.3.3"


def parse():
    parser = argparse.ArgumentParser(description='Sends alerts to Mattermost')
    parser.add_argument('--url', help='Incoming Webhook URL', required=True)
    parser.add_argument('--channel', help='Channel to notify')
    parser.add_argument('--username', help='Username to notify as',
                        default='Nagios')
    parser.add_argument('--iconurl', help='URL of icon to use for username',
                        default='https://slack.global.ssl.fastly.net/7bf4/img/services/nagios_128.png')  # noqa
    parser.add_argument('--notificationtype', help='Notification Type',
                        required=True)
    parser.add_argument('--hostalias', help='Host Alias', required=True)
    parser.add_argument('--hostaddress', help='Host Address', required=True)
    parser.add_argument('--hoststate', help='Host State')
    parser.add_argument('--hostoutput', help='Host Output')
    parser.add_argument('--servicedesc', help='Service Description')
    parser.add_argument('--servicestate', help='Service State')
    parser.add_argument('--serviceoutput', help='Service Output')
    parser.add_argument('--cgiurl', help='Link to extinfo.cgi on your Nagios instance', required=True)
    parser.add_argument('--version', action='version',
                        version='% (prog)s {version}'.format(version=VERSION))
    args = parser.parse_args()
    return args


def encode_special_characters(text):
    text = text.replace("%", "%25")
    text = text.replace("&", "%26")
    return text


def getcolor(type, state):
    color = ''
    if type == "RECOVERY":
        color = "good"
    elif type == "ACKNOWLEDGEMENT":
        color = "#3366ff"
    elif type == "PROBLEM" and state == "WARNING":
        color = "#FF8000"
    elif type == "PROBLEM":
        color = "danger"
    return color


def payload(args):
    nagios_link = ''
    acknowledge_link = ''
    if args.hoststate is not None:
        nagios_link = "{}extinfo.cgi?type=2&host={}".format(args.cgiurl, args.hostalias)
        if args.notificationtype == "PROBLEM":
            acknowledge_link = "[(Acknowledge)]({}cmd.cgi?cmd_typ=34&host={})".format(args.cgiurl, args.hostalias)
    elif args.servicestate is not None:
        nagios_link = "{}extinfo.cgi?type=2&host={}&service={}".format(args.cgiurl, args.hostalias,
                                                                       args.servicedesc)
        if args.notificationtype == "PROBLEM":
            acknowledge_link = "[(Acknowledge)]({}cmd.cgi?cmd_typ=34&host={}&service={})".format(args.cgiurl,
                                                                                                 args.hostalias,
                                                                                                 args.servicedesc)
    template_service = [
        {
            "fallback": "{} in {} at {}".format(args.notificationtype, args.hostalias, args.servicedesc),
            "title": "{} -> {} at {}".format(args.notificationtype, args.hostalias, args.hostaddress),
            "title_link": nagios_link,
            "color": getcolor(args.notificationtype, args.servicestate),
            "fields": [
                {
                    "title": str(args.servicedesc) + " is " + str(args.servicestate),
                    "short": False,
                    "value": str(args.serviceoutput) + " " + acknowledge_link
                }
            ],
        }
    ]

    template_host = [
        {
            "fallback": "{} in {} is {}".format(args.notificationtype, args.hostalias, args.hoststate),
            "title": "{} -> {} at {}".format(args.notificationtype, args.hostalias, args.hostaddress),
            "title_link": nagios_link,
            "color": getcolor(args.notificationtype, args.servicestate),
            "fields": [
                {
                    "title": "Host {}".format(args.hoststate),
                    "short": False,
                    "value": str(args.hostoutput) + " " + acknowledge_link
                }
            ],
        }
    ]

    attachment = template_service if args.servicestate else template_host
    payload = {
        "username": args.username,
        "icon_url": args.iconurl,
        "attachments": attachment
    }

    if args.channel:
        payload["channel"] = args.channel

    data = "payload= " + json.dumps(payload)
    return encode_special_characters(data)


def request(url, values):
    print(values)
    data = values.encode('ascii') # data should be bytes
    req = urllib.request.Request(url, data)
    with urllib.request.urlopen(req) as response:
        return response.read()

if __name__ == "__main__":
    args = parse()
    response = request(args.url, payload(args))
    print(response)
