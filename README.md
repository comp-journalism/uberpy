# uberpy
This script will help you gather data from the Uber API, including estimated waiting times and price surges at specific geocoded locations

** Dependencies You Need to Install**
- https://apscheduler.readthedocs.org/en/latest/
- https://github.com/kennethreitz/grequests

** Setup **
You need to specify some things in a config file called config.conf. There is an example that you need to edit. First, add your own Uber API keys putting a comma in between each if you have more than one. Next, edit the locations where you want to collect data by adding JSON object
