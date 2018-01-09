#!/usr/bin/env python2
# Original source: https://github.com/reneboer/python-carnet-client/
import re
import requests
import json
import sys
import time
import pprint
import argparse


from urlparse import urlsplit

class VWCarnet(object):
    def __init__(self, username, password):
        self.carnet_username = username
        self.carnet_password = password

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


    def _carnet_retrieve_carnet_info(self, wait):
        vehicle_data = {}
        vehicle_data_messages = json.loads(self._carnet_post( '/-/msgc/get-new-messages'))
        vehicle_data_location = json.loads(self._carnet_post('/-/cf/get-location'))

        if wait:
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

    def _carnet_print_carnet_info(self, wait):
        vehicle_data = self._carnet_retrieve_carnet_info(wait)
        #pprint.pprint(vehicle_data)

        #try:
        #    lat_reversed = str(vehicle_data['location']['position']['lat'])[::-1]
        #    lon_reversed = str(vehicle_data['location']['position']['lng'])[::-1]
        #    lat = lat_reversed[:6] + "." + lat_reversed[6:]
        #    lon = lon_reversed[:6] + "." + lon_reversed[6:]
        #    print(lat)
        #    print(lon)
        #    floc = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=' + str(lat[::-1]) + ',' + str(lon[::-1]))
        #    print(floc.content)
        #    loc = json.loads(floc.content)["results"][0]["formatted_address"]
        #except:
        #    loc = 'unknown'

        print('-- Status --')
        print(' Next service inspection: %s' % vehicle_data['details']['vehicleDetails']['serviceInspectionData'])
        print(' Distance: %s' % vehicle_data['details']['vehicleDetails']['distanceCovered'])
        print(' Last connected: %s %s' % (vehicle_data['details']['vehicleDetails']['lastConnectionTimeStamp'][0], vehicle_data['details']['vehicleDetails']['lastConnectionTimeStamp'][1]))
        print('-- Location --')
        print(' Latitude: %s' % vehicle_data['location']['position']['lat'])
        print(' Longitude: %s' % vehicle_data['location']['position']['lng'])
        #print(' Location: %s' % (loc))
        print('-- eManager --')
        print(' Charger max ampere: %sa' % vehicle_data['emanager']['EManager']['rbc']['settings']['chargerMaxCurrent'])
        print(' Battery left: %s%%' % vehicle_data['emanager']['EManager']['rbc']['status']['batteryPercentage'])
        print(' External power connected: %s' % vehicle_data['emanager']['EManager']['rbc']['status']['extPowerSupplyState'])
        print(' Electric range left: %s miles' % vehicle_data['emanager']['EManager']['rbc']['status']['electricRange'])
        print(' Charging state: %s' % vehicle_data['emanager']['EManager']['rbc']['status']['chargingState'])
        print(' Charging time left: %sh %sm' % (vehicle_data['emanager']['EManager']['rbc']['status']['chargingRemaningHour'], vehicle_data['emanager']['EManager']['rbc']['status']['chargingRemaningMinute']))
        print(' Climatisation target temperature: %sc'% vehicle_data['emanager']['EManager']['rpc']['settings']['targetTemperature'])
        print(' Climatisation state: %s' % vehicle_data['emanager']['EManager']['rpc']['status']['climatisationState'])
        print(' Windowheating state front: %s' % vehicle_data['emanager']['EManager']['rpc']['status']['windowHeatingStateFront'])
        print(' Windowheating state rear: %s' % vehicle_data['emanager']['EManager']['rpc']['status']['windowHeatingStateRear'])

    def _carnet_print_action(self, action, resp):
        print('-- Information --')
        print(' Action: %s' % (action))
        if not 'actionNotification' in resp:
            print(' Status: FAILED, %s' % resp)
        else:
            print(' Status: %s' % resp['actionNotification']['actionState'].lower())

    def _carnet_print_action_notification_status(self, action):
        counter = 0
        while counter < self.timeout_counter:
            resp = json.loads(self._carnet_post('/-/emanager/get-notifications'))
            if 'actionNotificationList' in resp:
                print('-- Information --')
                for notification in resp['actionNotificationList']:
                    print(' Action: %s' % (action))
                    print(' Status: %s' % notification['actionState'].lower())
                    if notification['actionState'] == 'FAILED':
                        print(' Message: %s, %s' % (notification['errorTitle'], notification['errorMessage']))
                        return
                    if notification['actionState'] == 'SUCCEEDED':
                        return
            time.sleep(1)
            counter += 1

        print('-- Information --')
        print(' Action: %s' % (action))
        print(' Status: ERROR, request timed out')
        return


def main():
    parser = argparse.ArgumentParser()
    required_argument = parser.add_argument_group('required arguments')
    required_argument.add_argument('-u', dest='carnet_username', help='Specify your carnet username here', required=True)
    required_argument.add_argument('-p', dest='carnet_password', help='Specify your carnet password here', required=True)
    required_argument.add_argument('-t', action = 'store', dest='carnet_task', choices = ['info', 'start-charge', 'stop-charge', 'start-climat', 'stop-climat', 'start-window-heating', 'stop-window-heating'], help = 'info shows carnet information (takes long time to generate)', required=True)
    parser.add_argument('-w', dest='carnet_wait', action = 'store_true', default = False, help='Specify -w if you want to wait for response on your actions', required=False)
    args = parser.parse_args()

    vw = VWCarnet(args.carnet_username, args.carnet_password)
    if args.carnet_task == 'info':
        vw._carnet_print_carnet_info(args.carnet_wait)

    elif args.carnet_task == 'start-charge':
        resp = vw._carnet_start_charge()
        vw._carnet_print_action('start charging', resp)
        if args.carnet_wait:
            vw._carnet_print_action_notification_status('start charging')

    elif args.carnet_task == 'stop-charge':
        resp = vw._carnet_stop_charge()
        vw._carnet_print_action('stop charging', resp)
        if args.carnet_wait:
            vw._carnet_print_action_notification_status('stop charging')

    elif args.carnet_task == 'start-climat':
        resp = vw._carnet_start_climat()
        vw._carnet_print_action('start climat', resp)
        if args.carnet_wait:
            vw._carnet_print_action_notification_status('start climat')

    elif args.carnet_task == 'stop-climat':
        resp = vw._carnet_stop_climat()
        vw._carnet_print_action('stop climat', resp)
        if args.carnet_wait:
            vw._carnet_print_action_notification_status('stop climat')

    elif args.carnet_task == 'start-window-heating':
        resp = vw._carnet_start_window_melt()
        vw._carnet_print_action('start window heating', resp)
        if args.carnet_wait:
            vw._carnet_print_action_notification_status('start window heating')

    elif args.carnet_task == 'stop-window-heating':
        resp = vw._carnet_stop_window_melt()
        vw._carnet_print_action('stop window heating', resp)
        if args.carnet_wait:
            vw._carnet_print_action_notification_status('stop window heating')
    else:
        sys.exit(1)





    #print(vw._carnet_post('/-/msgc/get-new-messages'))
    #print()
    #print(vw._carnet_post('/-/emanager/get-notifications'))
    #print()
    #print(vw._carnet_post('/-/msgc/get-new-messages'))
    #print()
    #print(vw._carnet_post('/-/emanager/get-emanager'))


if __name__ == '__main__':
    main()