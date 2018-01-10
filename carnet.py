#!/usr/bin/env python
#
# Original source: https://github.com/reneboer/python-carnet-client/
#
import re
import requests
import json
import sys
import time
import pprint
import argparse


from urlparse import urlsplit

class VWCarnet(object):
    def __init__(self, args):
        self.carnet_username = args.carnet_username
        self.carnet_password = args.carnet_password
        self.carnet_retry = args.carnet_retry
        self.carnet_wait = args.carnet_wait
        self.carnet_task = args.carnet_task
        if self.carnet_retry:
            self.carnet_wait = True

        # Fake the VW CarNet mobile app headers
        self.headers = { 'Accept': 'application/json, text/plain, */*', 'Content-Type': 'application/json;charset=UTF-8', 'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0.1; D5803 Build/23.5.A.1.291; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/63.0.3239.111 Mobile Safari/537.36' }
        self.session = requests.Session()
        self.timeout_counter = 30 # seconds

        self._carnet_logon()

    def _carnet_logon(self):
        AUTHHEADERS = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0.1; D5803 Build/23.5.A.1.291; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/63.0.3239.111 Mobile Safari/537.36'}

        auth_base = "https://security.volkswagen.com"
        base = "https://www.volkswagen-car-net.com"

        # Regular expressions to extract data
        csrf_re = re.compile('<meta name="_csrf" content="([^"]*)"/>')
        redurl_re = re.compile('<redirect url="([^"]*)"></redirect>')
        viewstate_re = re.compile('name="javax.faces.ViewState" id="j_id1:javax.faces.ViewState:0" value="([^"]*)"')
        authcode_re = re.compile('code=([^"]*)&')
        authstate_re = re.compile('state=([^"]*)')

        def extract_csrf(r):
            return csrf_re.search(r.text).group(1)

        def extract_redirect_url(r):
            return redurl_re.search(r.text).group(1)

        def extract_view_state(r):
            return viewstate_re.search(r.text).group(1)

        def extract_code(r):
            return authcode_re.search(r).group(1)

        def extract_state(r):
            return authstate_re.search(r).group(1)

        # Request landing page and get CSFR:
        r = self.session.get(base + '/portal/en_GB/web/guest/home')
        if r.status_code != 200:
            return ""
        csrf = extract_csrf(r)

        # Request login page and get CSRF
        AUTHHEADERS["Referer"] = base + '/portal'
        AUTHHEADERS["X-CSRF-Token"] = csrf
        r = self.session.post(base + '/portal/web/guest/home/-/csrftokenhandling/get-login-url', headers=AUTHHEADERS)
        if r.status_code != 200:
            return ""
        responseData = json.loads(r.content)
        lg_url = responseData.get("loginURL").get("path")

        # no redirect so we can get values we look for
        r = self.session.get(lg_url, allow_redirects=False, headers = AUTHHEADERS)
        if r.status_code != 302:
            return ""
        ref_url = r.headers.get("location")

        # now get actual login page and get session id and ViewState
        r = self.session.get(ref_url, headers = AUTHHEADERS)
        if r.status_code != 200:
            return ""
        view_state = extract_view_state(r)

        # Login with user details
        AUTHHEADERS["Faces-Request"] = "partial/ajax"
        AUTHHEADERS["Referer"] = ref_url
        AUTHHEADERS["X-CSRF-Token"] = ''

        post_data = {
            'loginForm': 'loginForm',
            'loginForm:email': self.carnet_username,
            'loginForm:password': self.carnet_password,
            'loginForm:j_idt19': '',
            'javax.faces.ViewState': view_state,
            'javax.faces.source': 'loginForm:submit',
            'javax.faces.partial.event': 'click',
            'javax.faces.partial.execute': 'loginForm:submit loginForm',
            'javax.faces.partial.render': 'loginForm',
            'javax.faces.behavior.event': 'action',
            'javax.faces.partial.ajax': 'true'
        }

        r = self.session.post(auth_base + '/ap-login/jsf/login.jsf', data=post_data, headers = AUTHHEADERS)
        if r.status_code != 200:
            return ""
        ref_url = extract_redirect_url(r).replace('&amp;', '&')

        # redirect to link from login and extract state and code values
        r = self.session.get(ref_url, allow_redirects=False, headers = AUTHHEADERS)
        if r.status_code != 302:
            return ""
        ref_url2 = r.headers.get("location")

        code = extract_code(ref_url2)
        state = extract_state(ref_url2)

        # load ref page
        r = self.session.get(ref_url2, headers = AUTHHEADERS)
        if r.status_code != 200:
            return ""

        AUTHHEADERS["Faces-Request"] = ""
        AUTHHEADERS["Referer"] = ref_url2
        post_data = {
            '_33_WAR_cored5portlet_code': code,
            '_33_WAR_cored5portlet_landingPageUrl': ''
        }
        r = self.session.post(base + urlsplit(
            ref_url2).path + '?p_auth=' + state + '&p_p_id=33_WAR_cored5portlet&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view&p_p_col_id=column-1&p_p_col_count=1&_33_WAR_cored5portlet_javax.portlet.action=getLoginStatus',
                   data=post_data, allow_redirects=False, headers=AUTHHEADERS)
        if r.status_code != 302:
            return ""

        ref_url3 = r.headers.get("location")
        r = self.session.get(ref_url3, headers=AUTHHEADERS)

        # We have a new CSRF
        csrf = extract_csrf(r)

        # Update headers for requests
        self.headers["Referer"] = ref_url3
        self.headers["X-CSRF-Token"] = csrf
        self.url = ref_url3

    def _carnet_post(self, command):
        #print(command)
        r = self.session.post(self.url + command, headers = self.headers)
        return r.content

    def _carnet_post_action(self, command, data):
        #print(command)
        r = self.session.post(self.url + command, json=data, headers = self.headers)
        return r.content


    def _carnet_retrieve_carnet_info(self):
        vehicle_data = {}
        vehicle_data_messages = json.loads(self._carnet_post( '/-/msgc/get-new-messages'))
        vehicle_data_location = json.loads(self._carnet_post('/-/cf/get-location'))

        if self.carnet_wait:
            # request vehicle details, takes some time to get
            self._carnet_post('/-/vsr/request-vsr')
            vehicle_data_status = json.loads(self._carnet_post('/-/vsr/get-vsr'))
            counter = 0
            while vehicle_data_status['vehicleStatusData']['requestStatus'] == 'REQUEST_IN_PROGRESS':
                vehicle_data_status = json.loads(self._carnet_post('/-/vsr/get-vsr'))
                counter +=1
                time.sleep(1)
                if counter > self.timeout_counter:
                    break
        else:
            vehicle_data_status = json.loads(self._carnet_post('/-/vsr/get-vsr'))
        vehicle_data_details = json.loads(self._carnet_post('/-/vehicle-info/get-vehicle-details'))
        vehicle_data_emanager = json.loads(self._carnet_post('/-/emanager/get-emanager'))

        vehicle_data['messages'] = vehicle_data_messages
        vehicle_data['location'] = vehicle_data_location
        vehicle_data['status'] = vehicle_data_status
        vehicle_data['details'] = vehicle_data_details
        vehicle_data['emanager'] = vehicle_data_emanager

        return vehicle_data

    def _carnet_start_charge(self):
        post_data = {
            'triggerAction': True,
            'batteryPercent': '100'
        }
        return json.loads(self._carnet_post_action('/-/emanager/charge-battery', post_data))

    def _carnet_stop_charge(self):
        post_data = {
            'triggerAction': False,
            'batteryPercent': '99'
        }
        return json.loads(self._carnet_post_action('/-/emanager/charge-battery', post_data))


    def _carnet_start_climat(self):
        post_data = {
            'triggerAction': True,
            'electricClima': True
        }
        return json.loads(self._carnet_post_action('/-/emanager/trigger-climatisation', post_data))


    def _carnet_stop_climat(self):
        post_data = {
            'triggerAction': False,
            'electricClima': True
        }
        return json.loads(self._carnet_post_action('/-/emanager/trigger-climatisation', post_data))

    def _carnet_start_window_melt(self):
        post_data = {
            'triggerAction': True
        }
        return json.loads(self._carnet_post_action('/-/emanager/trigger-windowheating', post_data))

    def _carnet_stop_window_melt(self):
        post_data = {
            'triggerAction': False
        }
        return json.loads(self._carnet_post_action('/-/emanager/trigger-windowheating', post_data))

    def _carnet_print_carnet_info(self):
        vehicle_data = self._carnet_retrieve_carnet_info()
        vehicle_located, vehicle_located_link  = self._google_get_location(str(vehicle_data['location']['position']['lng']), str(vehicle_data['location']['position']['lat']))

        print('-- Status --')
        print(' Next service inspection: %s' % vehicle_data['details']['vehicleDetails']['serviceInspectionData'])
        print(' Distance: %s km' % vehicle_data['details']['vehicleDetails']['distanceCovered'])
        print(' Last connected: %s %s' % (vehicle_data['details']['vehicleDetails']['lastConnectionTimeStamp'][0], vehicle_data['details']['vehicleDetails']['lastConnectionTimeStamp'][1]))
        print('-- Location --')
        print(' Latitude: %s' % vehicle_data['location']['position']['lat'])
        print(' Longitude: %s' % vehicle_data['location']['position']['lng'])
        if vehicle_located:
            print(' Located: %s' % (vehicle_located))
            if vehicle_located_link:
                print(' Link: %s' % (vehicle_located_link))
        print('-- eManager --')
        print(' Charger max ampere: %sa' % vehicle_data['emanager']['EManager']['rbc']['settings']['chargerMaxCurrent'])
        print(' Battery left: %s%%' % vehicle_data['emanager']['EManager']['rbc']['status']['batteryPercentage'])
        print(' External power connected: %s' % vehicle_data['emanager']['EManager']['rbc']['status']['extPowerSupplyState'])
        print(' Electric range left: %s km' % (vehicle_data['emanager']['EManager']['rbc']['status']['electricRange'] * 10))
        print(' Charging state: %s' % vehicle_data['emanager']['EManager']['rbc']['status']['chargingState'])
        print(' Charging time left: %sh %sm' % (vehicle_data['emanager']['EManager']['rbc']['status']['chargingRemaningHour'], vehicle_data['emanager']['EManager']['rbc']['status']['chargingRemaningMinute']))
        print(' Climatisation target temperature: %sc'% vehicle_data['emanager']['EManager']['rpc']['settings']['targetTemperature'])
        print(' Climatisation state: %s' % vehicle_data['emanager']['EManager']['rpc']['status']['climatisationState'])
        print(' Windowheating state front: %s' % vehicle_data['emanager']['EManager']['rpc']['status']['windowHeatingStateFront'])
        print(' Windowheating state rear: %s' % vehicle_data['emanager']['EManager']['rpc']['status']['windowHeatingStateRear'])

    def _carnet_print_action(self, resp):
        print('-- Information --')
        print(' Task: %s' % (self.carnet_task))
        if not 'actionNotification' in resp:
            print(' Status: FAILED, %s' % resp)
        else:
            print(' Status: %s' % resp['actionNotification']['actionState'])

    def _carnet_print_action_notification_status(self):
        if self.carnet_wait:
            counter = 0
            while counter < self.timeout_counter:
                resp = json.loads(self._carnet_post('/-/emanager/get-notifications'))
                if 'actionNotificationList' in resp:
                    print('-- Information --')
                    for notification in resp['actionNotificationList']:
                        print(' Task: %s' % (self.carnet_task))
                        print(' Status: %s' % notification['actionState'])
                        if notification['actionState'] == 'FAILED':
                            print(' Message: %s, %s' % (notification['errorTitle'], notification['errorMessage']))
                            return False
                        if notification['actionState'] == 'SUCCEEDED':
                            return True
                time.sleep(1)
                counter += 1

            print('-- Information --')
            print(' Task: %s' % (self.carnet_task))
            print(' Status: ERROR, request timed out')
            return False
        return True

    def _carnet_do_action(self):
        if self.carnet_task == 'info':
            self._carnet_print_carnet_info()
            return True
        elif self.carnet_task == 'start-charge':
            resp = self._carnet_start_charge()
            self._carnet_print_action(resp)
            return self._carnet_print_action_notification_status()

        elif self.carnet_task == 'stop-charge':
            resp = self._carnet_stop_charge()
            self._carnet_print_action(resp)
            return self._carnet_print_action_notification_status()

        elif self.carnet_task == 'start-climat':
            resp = self._carnet_start_climat()
            self._carnet_print_action(resp)
            return self._carnet_print_action_notification_status()

        elif self.carnet_task == 'stop-climat':
            resp = self._carnet_stop_climat()
            self._carnet_print_action(resp)
            return self._carnet_print_action_notification_status()

        elif self.carnet_task == 'start-window-heating':
            resp = self._carnet_start_window_melt()
            self._carnet_print_action(resp)
            return self._carnet_print_action_notification_status()

        elif self.carnet_task == 'stop-window-heating':
            resp = self._carnet_stop_window_melt()
            self._carnet_print_action(resp)
            return self._carnet_print_action_notification_status()

    def _carnet_run_action(self):
        if self.carnet_retry:
            retry_counter = 0
            while True:
                retry_counter += 1
                print('-- Information --')
                print(' Task: %s' % (self.carnet_task))
                print(' Retry: %s/%s' % (retry_counter, self.carnet_retry))
                if self._carnet_do_action() or retry_counter >= int(self.carnet_retry):
                    break
        else:
            self._carnet_do_action()

    def _google_get_location(self, lng, lat):
        counter = 0
        location = False
        location_link = False
        while counter < 3:
            lat_reversed = str(lat)[::-1]
            lon_reversed = str(lng)[::-1]
            lat = lat_reversed[:6] + lat_reversed[6:]
            lon = lon_reversed[:6] + lon_reversed[6:]
            try:
                req = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=' + str(lat[::-1]) + ',' + str(lon[::-1]))
            except:
                time.sleep(2)
                continue
            data = json.loads(req.content)
            if 'status' in data and data['status'] == 'OK':
                location = data["results"][0]["formatted_address"]
                location_link = "https://maps.google.com/maps?z=12&t=m&q=loc:%s+%s" % (str(lat[::-1]), str(lon[::-1]))
                break

            time.sleep(2)
            continue

        return location, location_link


def main():
    parser = argparse.ArgumentParser()
    required_argument = parser.add_argument_group('required arguments')
    required_argument.add_argument('-u', dest='carnet_username', help='Specify your carnet username here', required=True)
    required_argument.add_argument('-p', dest='carnet_password', help='Specify your carnet password here', required=True)
    required_argument.add_argument('-t', action = 'store', dest='carnet_task', choices = ['info', 'start-charge', 'stop-charge', 'start-climat', 'stop-climat', 'start-window-heating', 'stop-window-heating'], required=True)
    parser.add_argument('-w', dest='carnet_wait', action = 'store_true', default = False, help='Specify -w if you want to wait for response on your actions from your vehicle', required=False)
    parser.add_argument('-r', dest='carnet_retry', action='store', type = int, default=False, help='Specify -r <number of retries> if you want to retry action if it fails', required=False)
    args = parser.parse_args()

    vw = VWCarnet(args)
    vw._carnet_run_action()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Aborting..')
        sys.exit(1)