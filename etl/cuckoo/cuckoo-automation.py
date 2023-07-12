'@author: Arjun VK'
"File : inside cuckoo called from automation code"
try:
	import requests
except Exception as e:
	import requests

import time 
import json
import argparse
import sys

def print_to_stderr(a):
	sys.stderr.write(a)
	

def sendFileToCuckoo():
    '''
        Send the malware.exe stored to cuckoo for analysis
        Returns the task_id
    '''
    SAMPLE_FILE = "/home/cuckoo/Shared/malware.exe"
    REST_URL = "http://localhost:8090/tasks/create/file"
    HEADERS = {"Authorization": "Bearer 1YlQZ0xrWN1yN6_TfEqgng"}

    with open(SAMPLE_FILE, "rb") as sample:
        files = {"file": ("temp_file_name", sample)}
        r = requests.post(REST_URL, headers=HEADERS, files=files)

    if r.status_code == 200:
        task_id = r.json()["task_id"]
        print_to_stderr("[LOG {}] Analysis started for Task ID : {}".format(r.status_code, task_id))
        return task_id
    else:
        print_to_stderr("[LOG {}] Fail : http://localhost:8090/tasks/create/file ".format (r.status_code))
        return -1


def getReport(task_id):
	'''
		Outputs the report of the task_id to stdout
	'''

	HEADERS = {"Authorization": "Bearer 1YlQZ0xrWN1yN6_TfEqgng"}
	report_url = "http://localhost:8090/tasks/report/{}".format(task_id)

	r = requests.get(report_url, headers=HEADERS)
	
	if r.status_code == 200:
		report = r.json()
		sha256 = report['target']['file']['sha256']
		json_object = json.dumps(report, indent = 4)
		print(json_object)
		'''
		with open("{}_report.json".format(sha256), "w") as outfile:
    			outfile.write(json_object)
		'''
		print_to_stderr("[LOG {}] Report saved {}".format(r.status_code, sha256))
		

	else:
		print_to_stderr("[LOG {}] Failed to get report ".format(r.status_code))


def getSummary(task_id):
	'''
		Outputs the summary of the task_id to stdout
	'''

	HEADERS = {"Authorization": "Bearer 1YlQZ0xrWN1yN6_TfEqgng"}
	report_url = "http://localhost:8090/tasks/summary/{}".format(task_id)
	
	r = requests.get(report_url, headers=HEADERS)
	
	if r.status_code == 200:
		report = r.json()
		sha256 = report['target']['file']['sha256']
		json_object = json.dumps(report, indent = 4)
		print(json_object)
		'''
		with open("{}_summary.json".format(sha256), "w") as outfile:
    			outfile.write(json_object)
		'''
		print_to_stderr("[LOG {}] Summary saved {}".format(r.status_code, sha256))
		
	else:
		print_to_stderr("[LOG {}] Failed to get summary ".format(r.status_code))
		

if __name__ == '__main__':
	
	parser = argparse.ArgumentParser()
	 
	parser.add_argument("-a", "--analyze", help = "Sends the malware.exe file to cuckoo for analysis", action='store_true')
	parser.add_argument("-s", "--summary", help = "Outputs the summary file to the console", action='store_true')
	parser.add_argument("-r", "--report", help = "Outputs the report file to the console", action='store_true')

	args = parser.parse_args()

	current_task_id = -1
	
	if args.analyze:
		current_task_id = sendFileToCuckoo()
		time.sleep(5)
		# TODO time.sleep(60)
	# Remove this when running so it returns the actual report
	current_task_id = 1

	if args.summary:
		getSummary(current_task_id)
	if args.report:
		getReport(current_task_id)


