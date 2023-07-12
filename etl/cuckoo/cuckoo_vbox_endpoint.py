# Arjun
'''
    1. Install Vbox Guest Additions in Cuckoo
    2. Create /home/cuckoo/Shared and add full_cuckoo_api.py
    3. Start cuckoo api
    4. Change full_cuckoo_api --> add \n to logs and fix current_task_id
    4. Take snapshot
    5. Exit with restoring to the snapshot

'''
'''
For Debug CMD

import virtualbox

vbox = virtualbox.VirtualBox()
session = virtualbox.Session()

machine = vbox.find_machine("Cuckoo Sandbox")

progress = machine.launch_vm_process(session, "gui", [])

guest_session = session.console.guest.create_session("cuckoo", "forensics")

process, stdout, stderr = guest_session.execute("/bin/ls", ["-l", "-a"])

process, stdout, stderr = guest_session.execute("/usr/local/bin/cuckoo", ["api"])

process, stdout, stderr = guest_session.execute("/usr/bin/python", ["/home/cuckoo/Shared/start_Cuckoo_api.py"])

progess = guest_session.file_copy_to_guest("D:\\VIT\\Year3Sem2\\J_AI_Antivirus\\Code\\pestudio.exe", "/home/cuckoo/Shared/malware.exe", []) 

process, stdout, stderr = guest_session.execute("/usr/bin/python", ["/home/cuckoo/Shared/full_Cuckoo.py", "--analyze", "--report"])

'''
import virtualbox
import json
import time 
from fastapi import FastAPI, File, UploadFile

def print_error(e):
    print("[ERROR] : ", end='')
    print(e)
    print("[LOG] : Waiting 10 seconds and trying again")
    time.sleep(10)



# Function to
#   1. Take input file path
#   2. Copy the file to the VM
#   3. Extract info 
#   4. Copy the extracted info out of VM
app = FastAPI()

@app.post("/testfile")
async def create_upload_file(file: UploadFile = File(...)):
    file_name = file.filename

    input_folder_path = "D:\\VIT\\Year3Sem2\\J_AI_Antivirus\\Code\\" # TODO: change to host
    input_malware_path = input_folder_path + "malware.exe"

    guest_folder_path = "/home/cuckoo/Shared/"
    guest_malware_path = guest_folder_path + "malware.exe"

    # Write the bytes file as an executable file in HOST machine
    with open(input_malware_path, 'wb') as f:
        f.write(UploadFile)

    # 2. Sending file (malware file) from HOST to GUEST VM
    guest_folder_path = "/home/cuckoo/Shared/"
    guest_malware_path = guest_folder_path + "malware.exe"

    while True:
        try:
            progess = guest_session.file_copy_to_guest(input_malware_path, guest_malware_path, [])
            progress.wait_for_completion(-1)

            if progress.result_code == 0:
                print("[LOG] Copy successful from " + input_malware_path + " to " + guest_malware_path)
                break

        except Exception as e:
            print_error(e)

    time.sleep(2)


    # Executing the python file in cuckoo
    while True:
        try:
            process, stdout, stderr = guest_session.execute("/usr/bin/python", ["/home/cuckoo/Shared/full_Cuckoo.py", "--analyze", "--report"])

            report = json.loads(stdout)

            sha256 = report['target']['file']['sha256']

            json_object = json.dumps(report, indent = 4)

            # Writing to report.json
            # with open("{}{}_report.json".format(output_destination_path, sha256), "w") as outfile:
            #    outfile.write(json_object)
            break

        except Exception as e:
            print_error(e)
    
    return {"json_output": json_object}


if __name__ == "__main__":

    machine_name = "Cuckoo Sandbox"
    username = "cuckoo"
    password = "forensics"

    # Opening the VM
    vbox = virtualbox.VirtualBox()
    session = virtualbox.Session()
    machine = vbox.find_machine(machine_name)

    # Launching VM
    print("[LOG] Starting {}".format(machine_name))
    progress = machine.launch_vm_process(session, "gui", [])
    progress.wait_for_completion(-1)
    print("[LOG] Started {}".format(machine_name))
    time.sleep(5)

    # Execute a command in the guest OS
    # Done for creating a guest_session and making sure it works
    global guest_session

    command = "/bin/ls"
    while True:
        try:
            guest_session = session.console.guest.create_session(username, password)
            process, stdout, stderr = guest_session.execute(command, ["-l", "-a"])
            print(str(stdout, 'UTF-8'))
            break

        except Exception as e:
            print_error(e)

    '''
        Inputs:
            guest_session
            malware_file_path : Path of malware in the host system
            output_destination_path : Path of folder to store the output in the host system
    '''