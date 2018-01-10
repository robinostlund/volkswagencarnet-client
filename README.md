# Python2 Volkswagen CarNet Client
## Information
This is a python client that connects to Volkswagen Carnet. It allows you to retreive information about your vehicle and also allows you to start charging etc.

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
# Get carnet information
$ carnet.py -u mycarnetuser -p 'mycarnetpassword' -t info

# Start charging
$ carnet.py -u mycarnetuser -p 'mycarnetpassword' -t start-charge

# Stop charging
$ carnet.py -u mycarnetuser -p 'mycarnetpassword' -t stop-charge

# Start climat
$ carnet.py -u mycarnetuser -p 'mycarnetpassword' -t start-climat

# Stop climat
$ carnet.py -u mycarnetuser -p 'mycarnetpassword' -t stop-climat

# Start window heating
$ carnet.py -u mycarnetuser -p 'mycarnetpassword' -t start-window-heating

# Stop window heating
$ carnet.py -u mycarnetuser -p 'mycarnetpassword' -t stop-window-heating
```


## Thanks to
https://github.com/wez3/volkswagen-carnet-client
https://github.com/reneboer/python-carnet-client/
