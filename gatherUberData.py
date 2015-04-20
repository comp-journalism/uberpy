import ConfigParser
import json
import time
import datetime
import grequests
import sys
import os
import csv
import urllib
import logging
from apscheduler.schedulers.background import BackgroundScheduler

# The API end points 
price_url = "https://api.uber.com/v1/estimates/price"
product_url = "https://api.uber.com/v1/products"
time_url = "https://api.uber.com/v1/estimates/time"

# Parse in the configuration information to get uber server tokens
config = ConfigParser.ConfigParser()
config.read(os.path.dirname(os.path.abspath(__file__)) + "/config.conf")
uber_server_tokens = (config.get("MainConfig", "uber_server_tokens")).split(",")

# Parse in the locations and output file name
locations = json.loads(config.get("MainConfig", "locations"))
output_file_name = config.get("MainConfig", "output_file_name")
time_interval = int(config.get("MainConfig", "time_interval"))

# Create a file to store data
fileWriter = csv.writer(open(output_file_name, "w+"),delimiter=",")
fileWriter.writerow(["timestamp", "surge_multiplier", "expected_wait_time", "product_type", "low_estimate", "high_estimate", "start_location_id", "end_location_id"])

# These api param objects are used to send requests to the API, we create api_param objects for each location and endpoint we want to gather
api_params = []
for l in locations:
	location_id = l["location_id"]
	price_parameters = {
		'start_latitude': l["latitude"],
		'end_latitude': l["latitude"],
		'start_longitude': l["longitude"],
		'end_longitude': l["longitude"]
	}

	time_parameters = {
		'start_latitude': l["latitude"],
		'start_longitude': l["longitude"],		
	}
	
	api_params.append({"url": price_url, "location_id": location_id, "type": "price", "parameters": price_parameters})
	api_params.append({"url": time_url, "location_id": location_id, "type": "time", "parameters": time_parameters})


tokennum = 0
def gather_loop():
	global tokennum
	# A list to hold our things to do via async
	async_action_items = []
	common_data_dict = {}
	for i, api_param in enumerate(api_params):		
		# Get the current time
		api_param["datetime"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		api_param["data"] = common_data_dict
		api_param["parameters"]["server_token"] = uber_server_tokens[tokennum % len(uber_server_tokens)]
		# From here: http://stackoverflow.com/questions/25115151/how-to-pass-parameters-to-hooks-in-python-grequests			
		action_item = grequests.get(api_param["url"]+"?"+urllib.urlencode(api_param["parameters"]), hooks={'response': [hook_factory(api_param)]})
		async_action_items.append(action_item)
		# increment the token num so that we use the next server key next time
		tokennum = tokennum + 1

	# Initiate both requests in parallel
	grequests.map(async_action_items)


def hook_factory(*factory_args, **factory_kwargs):
	def it_responded(res, **kwargs):		
		call_type = factory_args[0]["type"]
		location_id = factory_args[0]["location_id"]
		current_time = factory_args[0]["datetime"]		
		data_dict = factory_args[0]["data"]
		print data_dict
		try:
			json_response = json.loads(res.content)
			#print json_response
			# Parse the data differently depending on the type of call it was
			try:
				if call_type == "time":
					for t in json_response["times"]:	
						if t["display_name"] not in data_dict:
							data_dict[t["display_name"]] = {}
						data_dict[t["display_name"]]["expected_wait_time"] = t["estimate"]
				elif call_type == "price":
					for p in json_response["prices"]:
						if p["display_name"] not in data_dict:
							data_dict[p["display_name"]] = {}
						
						data_dict[p["display_name"]]["surge_multiplier"] = p["surge_multiplier"]
						data_dict[p["display_name"]]["product_type"] = p["display_name"]
						data_dict[p["display_name"]]["low_estimate"] = p["low_estimate"]
						if data_dict[p["display_name"]]["low_estimate"] != None:
							data_dict[p["display_name"]]["low_estimate"] = int(data_dict[p["display_name"]]["low_estimate"])

						data_dict[p["display_name"]]["high_estimate"] = p["high_estimate"]
						if data_dict[p["display_name"]]["high_estimate"] != None:
							data_dict[p["display_name"]]["high_estimate"] = int(data_dict[p["display_name"]]["high_estimate"])

				#print data_dict
				# For each product in the data dict write out a row
				for p in data_dict:
					data_dict[p]["timestamp"] = current_time
					data_dict[p]["start_location_id"] = location_id
					data_dict[p]["end_location_id"] = location_id

					#print data_dict[p]
					#if it has time and price then store it
					if "expected_wait_time" in data_dict[p] and "surge_multiplier" in data_dict[p]:
						#print data_dict[p]
						fileWriter.writerow([data_dict[p]["timestamp"], data_dict[p]["surge_multiplier"], data_dict[p]["expected_wait_time"], data_dict[p]["product_type"], data_dict[p]["low_estimate"], data_dict[p]["high_estimate"], data_dict[p]["start_location_id"], data_dict[p]["end_location_id"]])
			except TypeError as e:
				print e

		except Exception as e:
			print "The response at " + str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + " was: "
			print json_response
			print res.content
			print e
		
	return it_responded


# Create a scheduler to trigger every N seconds
# http://apscheduler.readthedocs.org/en/3.0/userguide.html#code-examples
logging.basicConfig()
scheduler = BackgroundScheduler()
scheduler.add_job(gather_loop, 'interval', seconds = time_interval)
scheduler.start()

while True:
	time.sleep(1)


# nohup python -u gatherUberData.py > nohup.txt &

