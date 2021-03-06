#!/usr/bin/env python

import sys

import json
import os
import requests
import yaml

def call(url, headers=None, iterations=1):
    got = {}

    for x in range(iterations):
        result = requests.get(url, headers=headers)
        version = 'unknown'

        if result.status_code != 200:
            version='failure %d' % result.status_code
        elif result.text.startswith('VERSION '):
            version=result.text[len('VERSION '):]
        else:
            version='unknown %s' % result.text

        got.setdefault(version, 0)
        got[version] += 1

    return got

def test_demo(base, v2_wanted):
    url = "%s/demo/" % base

    got = call(url, iterations=100)

    print(got)
    v2_seen = got.get('2.0.0', 0)
    rc = (abs(v2_seen - v2_wanted) <= 2)

    print("wanted v2_wanted %d" % v2_wanted)
    print("saw    v2_seen   %d" % v2_seen)
    print("returning %s" % rc)

    return rc

def test_from_yaml(base, yaml_path):
    spec = yaml.safe_load(open(yaml_path, "r"))

    url = spec['url'].replace('{BASE}', base)

    test_num = 0
    rc = True

    for test in spec['tests']:
        test_num += 1
        name = test.get('name', "%s.%d" % (os.path.basename(yaml_path), test_num))

        headers = test.get('headers', None)
        host = test.get('host', None)
        versions = test.get('versions', None)
        iterations = test.get('iterations', 100)

        if not versions:
            print("missing versions in %s?" % name)
            print("%s" % yaml.safe_dump(test))
            return False

        if host:
            if not headers:
                headers = {}

            headers['Host'] = host

        attempts = 3

        while attempts > 0:
            print("%s: attempts left %d" % (name, attempts))
            print("%s: headers %s" % (name, headers))

            got = call(url, headers=headers, iterations=iterations)

            print("%s: %s" % (name, json.dumps(got)))

            test_ok = True

            for version, wanted_count in versions.items():
                got_count = got.get(version, 0)
                delta = abs(got_count - wanted_count)

                print("%s %s: wanted %d, got %d (delta %d)" % 
                      (name, version, wanted_count, got_count, delta))

                if delta > 2:
                    test_ok = False

            if test_ok:
                print("%s: passed" % name)
                break
            else:
                attempts -= 1

                if attempts <= 0:
                    print("%s: FAILED" % name)
                    rc = False

    return rc

if __name__ == "__main__":
    base = sys.argv[1]

    if not base.startswith("http://"):
        base = "http://%s" % base

    v2_percent = None

    try:
        v2_percent = int(sys.argv[2])
    except ValueError:
        pass

    if v2_percent != None:
        rc = test_demo(base, v2_percent)
    else:
        rc = test_from_yaml(base, sys.argv[2])

    if rc:
        sys.exit(0)
    else:
        print("FAILED")
        sys.exit(1)
