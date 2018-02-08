#!/usr/bin/env python3
import requests
import json
import sys
import time
import argparse

try:
    from volkswagencarnet import Connection
except ImportError:
    print('Cannot find volkswagencarnet library, pip3 install volkswagencarnet')
    sys.exit(1)

class VWCarnet(object):
    def __init__(self, args):
        self.carnet_username = args.carnet_username
        self.carnet_password = args.carnet_password
        self.carnet_retry = args.carnet_retry
        self.carnet_wait = args.carnet_wait
        self.carnet_task = args.carnet_task
        if self.carnet_retry:
            self.carnet_wait = True

        # create carnet connection
        vw = Connection(self.carnet_username, self.carnet_password)

        # login to carnet
        if not vw._login():
            print('Failed to login with user %s, check your credentials.' % self.carnet_username)
            sys.exit(1)

        # fetch vehicles
        vw.update()

        # we only support 1 vehicle at this time
        self.vehicle = list(vw.vehicles)[0]


    def _carnet_print_carnet_info(self):
        # status
        output = '-- Status --'
        if self.vehicle.model_supported and self.vehicle.model_year_supported:
            output += '\n Model: %s/ %s' % (self.vehicle.model, self.vehicle.model_year)
        if self.vehicle.service_inspection_supported:
            output += '\n Next service inspection: %s' % self.vehicle.service_inspection
        if self.vehicle.oil_inspection_supported:
            output += '\n Next oil inspection: %s' % self.vehicle.oil_inspection
        if self.vehicle.distance_supported:
            output += '\n Distance: %s km' % self.vehicle.distance
        if self.vehicle.last_connected_supported:
            output += '\n Last connected: %s' % self.vehicle.last_connected

        if self.vehicle.door_locked_supported:
            if self.vehicle.door_locked:
                output += '\n Doors locked: yes'
            else:
                output += '\n Doors locked: no'

        if self.vehicle.parking_light_supported:
            if self.vehicle.is_parking_lights_on:
                output += '\n Parking lights: off'
            else:
                output += '\n Parking lights: on'

        # location
        if self.vehicle.position_supported:
            output += '\n-- Location --'

            output += '\n Latitude: %s' % self.vehicle.position['lat']
            output += '\n Longitude: %s' % self.vehicle.position['lng']
            vehicle_located, vehicle_located_link = self._google_get_location(str(self.vehicle.position['lng']),str(self.vehicle.position['lat']))
            if vehicle_located:
                output += '\n Located: %s' % (vehicle_located)
            if vehicle_located_link:
                output += '\n Link: %s' % (vehicle_located_link)

        # emanager
        output += '\n-- eManager --'
        if self.vehicle.battery_level_supported:
            output += '\n Battery left: %s%%' % self.vehicle.battery_level
        if self.vehicle.charge_max_ampere_supported:
            output += '\n Charger max ampere: %sa' % self.vehicle.charge_max_ampere

        if self.vehicle.charging_supported:
            if self.vehicle.is_charging_on:
                output += '\n Charging: on'
                output += '\n Charging time left: %sm' % self.vehicle.charging_time_left
            else:
                output += '\n Charging: off'

        if self.vehicle.electric_range_supported:
            output += '\n Electric range left: %s km' % self.vehicle.electric_range

        if self.vehicle.combustion_range_supported:
            output += '\n Combustion range left: %s km' % self.vehicle.combustion_range

        if self.vehicle.combined_range_supported:
            output += '\n Combined range left: %s km' % self.vehicle.combined_range

        if self.vehicle.external_power_supported:
            if self.vehicle.external_power:
                status = 'yes'
            else:
                status = 'no'
            output += '\n External power connected: %s' % status

        if self.vehicle.climatisation_supported:
            if self.vehicle.is_climatisation_on:
                output += '\n Climatisation: on'
            else:
                output += '\n Climatisation: off'
            output += '\n Climatisation target temperature: %sc' % self.vehicle.climatisation_target_temperature

        if self.vehicle.window_heater_supported:
            if self.vehicle.is_window_heater_on:
                output += '\n Window heater: on'
            else:
                output += '\n Window heater: off'

        # print output
        print(output)

    def _carnet_print_action(self, resp):
        print('-- Information --')
        print(' Task: %s' % (self.carnet_task))
        if resp:
            data = resp.get('actionNotification', {})
            if data:
                print(' Status: %s' % resp['actionNotification']['actionState'])
                return True
            else:
                print(' Status: FAILED, %s' % resp)
        else:
            print(' Status: FAILED')

    def _carnet_print_action_notification_status(self):
        if self.carnet_wait:
            resp = self.vehicle.get_status(timeout = 30)
            if resp:
                print('-- Information --')
                for notification in resp:
                    print(' Task: %s' % (self.carnet_task))
                    print(' Status: %s' % notification['actionState'])
                    if notification['actionState'] == 'FAILED':
                        print(' Message: %s, %s' % (notification['errorTitle'], notification['errorMessage']))
                        return False
                    if notification['actionState'] == 'SUCCEEDED':
                            return True
            else:
                print('-- Information --')
                print(' Task: %s' % (self.carnet_task))
                print(' Status: ERROR, request timed out')
                return False

    def _carnet_do_action(self):
        if self.carnet_task == 'info':
            self._carnet_print_carnet_info()
            return True
        elif self.carnet_task == 'start-charge':
            resp = self.vehicle.start_charging()

        elif self.carnet_task == 'stop-charge':
            resp = self.vehicle.stop_charging()

        elif self.carnet_task == 'start-climat':
            resp = self.vehicle.start_climatisation()

        elif self.carnet_task == 'stop-climat':
            resp = self.vehicle.stop_climatisation()

        elif self.carnet_task == 'start-window-heating':
            resp = self.vehicle.start_window_heater()

        elif self.carnet_task == 'stop-window-heating':
            resp = self.vehicle.stop_window_heater()

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
