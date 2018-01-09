# Python Volkswagen Carnet Client
## Information
This is a python client that connects to Volkswagen Carnet. It allows you to retreive information about your vehicle and also allows you to start charging etc.

## Usage
Get carnet information
```sh
carnet.py -u mycarnetuser -p 'mycarnetpassword' -t info
```

Start charging
```sh
carnet.py -u mycarnetuser -p 'mycarnetpassword' -t start-charge -w
```

Stop charging
```sh
carnet.py -u mycarnetuser -p 'mycarnetpassword' -t stop-charge -w
```

Start climat
```sh
carnet.py -u mycarnetuser -p 'mycarnetpassword' -t start-climat -w
```

Stop climat
```sh
carnet.py -u mycarnetuser -p 'mycarnetpassword' -t stop-climat -w
```

Start window heating
```sh
carnet.py -u mycarnetuser -p 'mycarnetpassword' -t start-window-heating -w
```

Stop window heating
```sh
carnet.py -u mycarnetuser -p 'mycarnetpassword' -t stop-window-heating -w
```
