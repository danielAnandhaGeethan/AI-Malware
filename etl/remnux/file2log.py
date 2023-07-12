# Static Malware Analysis - Data collection

import multiprocessing
import subprocess

def run_command(command, filename):
    """ A function to run a Linux CLI command and print its output to a file"""
    result = subprocess.run(command, stdout=subprocess.PIPE, shell=True)
    print('Command processed : ', command)
    
    with open(filename, 'w') as f:
        f.write(result.stdout.decode('utf-8'))

if __name__ == '__main__':

    input_file_path = " ~/Downloads/pestudio/pestudio.exe"

    # Define the Linux CLI commands to run
    commands = [
        'flarestrings -n 8 {filepath} | rank_strings --scores',
        'peframe --json {filepath}',
        'diec --info --json {filepath}',
        'manalyze --dump all --output json {filepath}'
        
    ]

    output_filenames = [
        'Strings.txt',
        'PEframe.json',
        'DIE.json',
        'Manalyze.json'
    ]

    # Create a process for each command
    processes = []
    for command, out_filename in zip(commands, output_filenames):
        p = multiprocessing.Process(target=run_command, args=(command.format(filepath = input_file_path), out_filename))
        processes.append(p)
        p.start()

    # Wait for all processes to complete
    for p in processes:
        p.join()
        