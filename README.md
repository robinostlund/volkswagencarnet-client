# Python3 Volkswagen CarNet Client
## Information
This is a python client that connects to Volkswagen Carnet. It allows you to retreive information about your vehicle and also allows you to start charging etc.

## Requirements
It requires volkswagencarnet library that can be installed from pip: 
```sh 
pip3 install volkswagencarent
```

## Help
```sh
$ carnet.py -h
usage: carnet.py [-h] -u CARNET_USERNAME -p CARNET_PASSWORD -t
                 {info,start-charge,stop-charge,start-climat,stop-climat,start-window-heating,stop-window-heating}
                 [-w] [-r CARNET_RETRY]

optional arguments:
  -h, --help            show this help message and exit
  -w                    Specify -w if you want to wait for response on your
                        actions
  -r CARNET_RETRY       Specify -r <number of retries> if you want to retry
                        action if it fails

required arguments:
  -u CARNET_USERNAME    Specify your carnet username here
  -p CARNET_PASSWORD    Specify your carnet password here
  -t {info,start-charge,stop-charge,start-climat,stop-climat,start-window-heating,stop-window-heating}
```

## Usage
```sh
export CARNET_USERNAME='my volkswagen carnet username'
export CARNET_PASSWORD="my volkswagen carnet password'

# Get carnet information
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t info
# Get carnet information and wait for confirmation from vehicle
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t info -w
# Get carnet information and wait for confirmation from vehicle and try it for 5 times
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t info -r 5

# Start charging
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t start-charge
# Start charging and wait for confirmation from vehicle
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t start-charge -w 
# Start charging and wait for confirmation from vehicle and try it for 5 times
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t start-charge -r 5

# Stop charging
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t stop-charge
# Stop charging and wait for confirmation from vehicle
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t stop-charge -w 
# Stop charging and wait for confirmation from vehicle and try it for 5 times
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t stop-charge -r 5

# Start climat
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t start-climat
# Start climat and wait for confirmation from vehicle
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t start-climat -w
# Start climat and wait for confirmation from vehicle and try it for 5 times
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t start-climat -r 5

# Stop climat
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t stop-climat
# Stop climat and wait for confirmation from vehicle
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t stop-climat -w
# Stop climat and wait for confirmation from vehicle and try it for 5 times
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t stop-climat -r 5

# Start window heating
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t start-window-heating
# Start window heating and wait for confirmation from vehicle
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t start-window-heating -w
# Start window heating and wait for confirmation from vehicle and try it for 5 times
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t start-window-heating -r 5

# Stop window heating
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t stop-window-heating
# Stop window heating and wait for confirmation from vehicle
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t stop-window-heating -w
# Stop window heating and wait for confirmation from vehicle and try it for 5 times
$ carnet.py -u $CARNET_USERNAME -p $CARNET_PASSWORD -t stop-window-heating -r 5
```

## Thanks to
https://github.com/wez3/volkswagen-carnet-client

https://github.com/reneboer/python-carnet-client
