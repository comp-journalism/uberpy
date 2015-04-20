# uberpy
This script will help you gather data from the Uber API, including estimated waiting times and price surges at specific geocoded locations

Dependencies You Need to Install
--------------
- https://apscheduler.readthedocs.org/en/latest/
- https://github.com/kennethreitz/grequests

Setup
--------------
You need to specify some things in a config file called config.conf. There is an example called config-example.conf that you can edit and save as config.conf. 
- First, add your own Uber API keys putting a comma in between each if you have more than one. 
- Next, edit the locations where you want to collect data by adding JSON objects of the form `{"location_id": <int>, "latitute": <float>, "longitude": <float>}`. You can put them in a list structure. 
- Specify the name of the output data file.
- Set the interval in seconds to collect data. (Note: You need to do some math to figure out how often you can hit the APIs given the number of API keys you have. Each interval uses 2 API calls, one for price and one for estimated wait. 

Run
---------------
Set it up to run indefinitely by using a command like: `nohup python -u gatherUberData.py > nohup.txt &`
