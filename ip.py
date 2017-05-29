import sys
import os
import subprocess
from subprocess import check_output
from subprocess import call


dev_null = open(os.devnull, 'w')
raw_output = check_output('ls -l', shell=True)
output_list = raw_output.strip().splitlines()[1:]

all_ips = []
all_ip_filenames = []

for i in range(len(output_list)):
    line_string = output_list[i]
    file_name = line_string.split()[-1]
    if file_name == str(sys.argv[0]):
        continue
    else:
        all_ip_filenames.append(file_name)
    ip = file_name.split('-')[0]
    if ip in all_ips:
        continue
    else:
        all_ips.append(ip)

temp = open(all_ip_filenames[0], 'r')
header = temp.read().splitlines()[0]
temp.close()

for ip in all_ips:
    command = 'rm ' + ip
    call(command, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('touch ' + ip, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    output_file = open(ip, 'a')
    output_file.write(header + '\n')
    for ip_filename in all_ip_filenames:
        if ip in ip_filename:
            temp_file = open(ip_filename, 'r')
            to_write = temp_file.read().strip().splitlines()[1:]
            for line in to_write:
                output_file.write(line + '\n')
            temp_file.close()
    output_file.close()

