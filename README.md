chargestop
==========

Save money by stopping ChargePoint sessions if it appears that your car is done charging

Huge credit to Mohamed Mansour for reverse-engineering the API used by the mobile app (see https://github.com/mohamedmansour/MyElectricCar). I wouldn't have been able to figure this out myself.

Installation
------------

```
git clone git@github.com:alexblanck/chargestop.git
cd chargestop
python3 setup.py install
```

Creating the Configuration File
-------------------------------

To access your data from ChargePoint, this program requires you username and password. We reccomended you supply this using a configuration file with this format:

```
username=alexblanck
password=hunter1
```

Later instructions assume you placed this file at `~/chargestop.cfg`

Trying it Out
-------------

Once you have your configuration file, just run the script

```
./bin/main.py -c ~/chargestop.cfg
```

If things are working, you should see a message like this:
```
2019-02-03 20:50:38,067 [INFO] chargestop.client : Successfully logged in as alexblanck
```

The program will start monitoring periodically for charging sessions to stop. To exit, use `Ctrl+C`

More Details
------------

* The program will only stop charging sessions that are marked as "paid" in the ChargePoint API
* Charging is stopped if the car is drawing less than 100 watts for more than 6 minutes
* Charging is also stopped if the session is marked as 'charging complete' in the ChargePoint API

Advanced Options
----------------

### Company Name Whitelist

If you only want the script to stop charging at specific charging locations, you can use the `company-name-whitelist` and the script will only stop charging sessions if the charger is associated with company you specify.

Example configuration file which only pays attention to charging occuring at 'ACME' or 'IKEA'

```
username=alexblanck
password=hunter1
company-name-whitelist=[ACME, IKEA]
```

### More

```
./bin/main.py --help
```

Will give a list of all command-line and config-file options. All options can be specified either in a config file or on the command line.


Known Limitations
-----------------

The `main.py` script will currently exit with an error if there is a temporary issue talking to the ChargePoint API. If you want to keep this program running, I reccomend using a process manager of some sort like [Supervisor](http://supervisord.org/) to keep it alive.

Example supervisor configuration:

```
[program:chargestop]
command=/usr/local/bin/python3 /usr/local/chargestop/bin/main.py -c /usr/local/chargestop.cfg -v
redirect_stderr=true
stdout_logfile=/var/log/chargestop.log
startsecs=0
```

Running Unit Tests
------------------

```
python3 ./setup.py test
```

To show log entries while running tests
```
python3 ./setup.py test --addopts "-o log_cli=true --log-cli-level=DEBUG"
```
