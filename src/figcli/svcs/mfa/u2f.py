#!/usr/bin/env python

import json
import time

import requests
from u2flib_host import u2f, exc, appid
from u2flib_host.constants import APDU_USE_NOT_SATISFIED

"""
Taken from: https://github.com/cevoaustralia/aws-google-auth/blob/master/aws_google_auth/u2f.py
We can't use aws_google_auth b/c of issues with homebrew installations 
"""

def __appid_verifier__fetch_json(app_id):
    target = app_id
    while True:
        resp = requests.get(target, allow_redirects=False, verify=True)

        # If the server returns an HTTP redirect (status code 3xx) the
        # server must also send the header "FIDO-AppID-Redirect-Authorized:
        # true" and the client must verify the presence of such a header
        # before following the redirect. This protects against abuse of
        # open redirectors within the target domain by unauthorized
        # parties.
        if 300 <= resp.status_code < 400:
            if resp.headers.get('FIDO-AppID-Redirect-Authorized') != \
                    'true':
                raise ValueError('Redirect must set '
                                 'FIDO-AppID-Redirect-Authorized: true')
            target = resp.headers['location']
        else:
            return resp.json()


def __appid_verifier__valid_facets(app_id, facets):
    return facets


def u2f_auth(challenges, facet):
    devices = u2f.list_devices()
    for device in devices[:]:
        try:
            device.open()
        except:
            # Some U2F devices fail on the first attempt to open but
            # succeed on subsequent attempts. So retry once.
            try:
                device.open()
            except:
                devices.remove(device)

    try:
        prompted = False
        while devices:
            removed = []
            for device in devices:
                remove = True
                for challenge in challenges:
                    try:
                        return u2f.authenticate(device, json.dumps(challenge),
                                                facet)
                    except exc.APDUError as e:
                        if e.code == APDU_USE_NOT_SATISFIED:
                            remove = False
                            if not prompted:
                                print('Touch the flashing U2F device to '
                                      'authenticate...')
                                prompted = True
                        else:
                            pass
                    except exc.DeviceError:
                        pass
                if remove:
                    removed.append(device)
            devices = [d for d in devices if d not in removed]
            for d in removed:
                d.close()
            time.sleep(0.25)
    finally:
        for device in devices:
            device.close()
    raise RuntimeWarning("U2F Device Not Found")


appid.verifier.fetch_json = __appid_verifier__fetch_json
appid.verifier.valid_facets = __appid_verifier__valid_facets