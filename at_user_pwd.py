#!/usr/bin/python
# -*- coding:utf8 -*-

import json
import os

# assign directory
directory = '/Users/i336543/Documents/SuccessFactors_App/androidrepo/uiautomator/src/uiautomator/assets/json'
secretSet = set()


def parse_case(case, server):
    try:
        if 'serverName' in case:
            # secret = "%s.%s.%s.%s" % (case['serverName'], case['feature'], case['username'], case['password'])
            secret = "%s.%s.%s" % (case['serverName'], case['feature'], case['username'])
        else:
            # secret = "%s.%s.%s.%s" % (server, case['feature'], case['username'], case['password'])
            if server == '':
                server = 'dc'
            secret = "%s.%s.%s" % (server, case['feature'], case['username'])
        if secret not in secretSet:
            print('- secret:')
            secretSet.add(secret)
            print('    name: ' + secret)
    except:
        print case


def json_to_python_from_file(f):
    f = open(f, 'r')
    s = f.read()
    rest = json.loads(s)
    serverName = ['qacand', 'qapatchpreview']
    if isinstance(rest, list):
        for case in rest:
            parse_case(case, "")
    else:
        for server in serverName:
            if server in rest:
                cases = rest[server]
                for case in cases:
                    parse_case(case, server)
    f.close()


# iterate over files in that directory
for root, dirs, files in os.walk(directory):
    for filename in files:
        # print(os.path.join(root, filename))
        json_to_python_from_file(os.path.join(root, filename))
