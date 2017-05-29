import sys
import os
from subprocess import call
from subprocess import Popen
from subprocess import check_output
import subprocess


# use 4 space indentation


''' Global variables '''


first_arg = None
second_arg = None
dev_null = open(os.devnull, 'w')


''' Functions '''


def parse_arguments():
    global first_arg, second_arg
    if not (len(sys.argv) == 3):
        print '\nUsage: python2.7 cmd.py <filename>\n'
        sys.exit()
    else:
        first_arg = str(sys.argv[1])
        second_arg = str(sys.argv[2])


''' Program '''


# BASH: EXECUTING COMMANDS
# start in foreground
call('<command>', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
##
raw_output = check_output('ls -l', shell=True)
output_list = raw_output.strip().splitlines()[1:]
for i in range(len(output_list)):
    line = output_list[i]
    print line
    for j in range(len(line)):
        # iterates over all line elements
        a = 0
# start in background
proc = Popen('<command>', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
proc.terminate()
##


# FILES: WRITING/READING
call('touch file.txt', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
##
append_file = open('file.txt', 'a')
append_file.write(raw_output)
append_file.write('random_string\n')
append_file.close()
##
read_file = open('file.txt', 'r')
line_list = read_file.read().splitlines()
read_file.close()
##


# ARCHIVING
# compressing (with -z option, to get .tar.gz instead of only .tar)
call('tar -czf archived_files.tar.gz henk gerard', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
call('tar -czf archived_dir.tar.gz testdir', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
# uncompressing (unpacked dir needs to already exist)
call('tar -xzf archived_files.tar.gz', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
call('tar -xzf archived_dir.tar.gz', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
call('tar -xzf archived_files.tar.gz -C ./unpacked', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)


# PRINTING with %d, %f, and %s
index_of_a = ord('a')
index_of_z = ord('z')
print '\nASCII indexes of a, z: %s - %s\n' % (index_of_a, index_of_z)
print 'Float: %.3f' % 0.3333333

