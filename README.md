# Python Volkswagen Carnet Client
## Information
This is a python client that connects to Volkswagen Carnet. It allows you to retreive information about your vehicle and also allows you to start charging etc.

## Help
```sh
$ carnet.py -h
usage: carnet.py [-h] -u CARNET_USERNAME -p CARNET_PASSWORD -t
                 {info,start-charge,stop-charge,start-climat,stop-climat,start-window-heating,stop-window-heating}
                 [-w]

optional arguments:
  -h, --help            show this help message and exit
  -w                    Specify -w if you want to wait for response on your
                        actions

required arguments:
  -u CARNET_USERNAME    Specify your carnet username here
  -p CARNET_PASSWORD    Specify your carnet password here
  -t {info,start-charge,stop-charge,start-climat,stop-climat,start-window-heating,stop-window-heating}
                        info shows carnet information (takes long time to
                        generate)
```

## Usage
Get carnet information
```sh
$ carnet.py -u mycarnetuser -p 'mycarnetpassword' -t info
```

Start charging
```sh
$ carnet.py -u mycarnetuser -p 'mycarnetpassword' -t start-charge -w
```

Stop charging
```sh
$ carnet.py -u mycarnetuser -p 'mycarnetpassword' -t stop-charge -w
```

Start climat
```sh
$ carnet.py -u mycarnetuser -p 'mycarnetpassword' -t start-climat -w
```

Stop climat
```sh
$ carnet.py -u mycarnetuser -p 'mycarnetpassword' -t stop-climat -w
```

Start window heating
```sh
$ carnet.py -u mycarnetuser -p 'mycarnetpassword' -t start-window-heating -w
```

Stop window heating
```sh
$ carnet.py -u mycarnetuser -p 'mycarnetpassword' -t stop-window-heating -w
```


## Thanks to
https://github.com/wez3/volkswagen-carnet-client
https://github.com/reneboer/python-carnet-client/
