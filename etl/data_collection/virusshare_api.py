import requests
import time
import pandas as pd

folder_path = 'samples/'
df = pd.read_csv('hashes.csv')

start = '3000'
end = '5000'

api_key = '<api_key>'

new_df = df.loc[start:end]

for row in new_df.itertuples():
	hash_value = row[1]
	url = "https://virusshare.com/apiv2/{}?apikey={}&hash={}"
	response = requests.get(url.format("file", api_key, hash_value))

	if response.status_code == 200:
		malware_log = response.json()
		try:
			if malware_log['size'] < 5000000 and malware_log['extension'] == "exe":
				file_name = folder_path + hash_value + ".zip"

				response2 = requests.get(url.format("download",api_key,hash_value))

			with open(file_name, 'wb') as f:
				f.write(response2.content)

			if malware_log['virustotal']['scans']['Microsoft']['result'] != None and malware_log['virustotal']['scans']['Microsoft']['result'] != "":
				ans = malware_log['virustotal']['scans']['Microsoft']['result'].split("/")[1].split(".")[0]
			
			else:
				ans = 'miscelleneous'

			with open('data.csv','a') as f:
				f.write('\n' + hash_value + "," + ans)

			time.sleep(17)
		except Exception as e:
			print(e)
	else:
		print('Error:', response.text)