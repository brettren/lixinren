#!/usr/bin/python
# -*- coding:utf8 -*-

import json


keys = "String username, String password, String activityName, String updateName, String actName, String updateName1"
values = ["mhoff", "pwd", "Auto test no update from Yaming",
                    "Auto test self add update", "Auto test one update activity for Yaming", "Auto update from cgrant"]
print dict(zip(keys.replace('String ', '').split(', '), values))



list = keys.replace('String ', '').split(', ')
for e in list:
    print 'String %s = data.get("%s");' % (e, e)