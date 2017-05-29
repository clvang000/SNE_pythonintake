from subprocess import call
from subprocess import Popen
import subprocess
import signal
import sys
import time
import os


''' Global variables'''

# input arguments
lf_bin = None
afl_bin = None
seed_corp = None
out_corp = None
dicty = None
dict_specified = False
# run commands
afl_firstrun_cmd = None
afl_run_cmd = None
lf_run_cmd = None
# minimization commands
rename_current_corpus_dir = None
make_lfmin_corpus_dir = None
make_aflmin_corpus_dir = None
afl_minimize_cmd = None
lf_minimize_cmd = None
remove_lfmin_corpus_dir = None
remove_old_corpus_dir = None
# runtime
dev_null = None
running_process_pids = []
NR_OF_THREADS = 4
FUZZER_RUNTIME = 30


''' Functions '''


def parse_arguments():
    global lf_bin, afl_bin, seed_corp, out_corp, dicty, dict_specified
    if not (len(sys.argv) == 5 or len(sys.argv) == 6):
        print '\nUsage: python2.7 fuzz.py <lf_binary> <afl_binary> <seed_corp_dir> ' \
              '<out_corp_dir> <dictionary(optional)> '
        print 'Make sure all the test cases are in the root directory of the (afl-cmin minimized) seed corpus.\n'
        sys.exit()
    else:
        lf_bin = str(sys.argv[1])
        afl_bin = str(sys.argv[2])
        seed_corp = str(sys.argv[3])
        out_corp = str(sys.argv[4])
        if len(sys.argv) == 6:
            dict_specified = True
            dicty = str(sys.argv[5])


def generate_run_commands():
    global lf_run_cmd, afl_run_cmd, afl_firstrun_cmd, out_corp, seed_corp, lf_bin, afl_bin, dicty
    lf_run_options = ' -jobs=1000 -workers=' + str(NR_OF_THREADS) + ' -print_final_stats=1 -rss_limit_mb=0'
    if dict_specified:
        afl_firstrun_cmd = 'afl-fuzz -i ' + seed_corp + ' -o ' + out_corp + ' -m none ' + '-x ' + dicty
        afl_run_cmd = 'afl-fuzz -i- -o ' + out_corp + ' -m none ' + '-x ' + dicty
        lf_run_cmd = './' + lf_bin + ' ' + out_corp + '/1/queue' + lf_run_options + ' -dict=' + dicty
    else:
        afl_firstrun_cmd = 'afl-fuzz -i ' + seed_corp + ' -o ' + out_corp + ' -m none'
        afl_run_cmd = 'afl-fuzz -i- -o ' + out_corp + ' -m none'
        lf_run_cmd = './' + lf_bin + ' ' + out_corp + '/1/queue' + lf_run_options


def generate_corpus_minimization_commands():
    global afl_minimize_cmd, lf_minimize_cmd, rename_current_corpus_dir, make_lfmin_corpus_dir, \
        make_aflmin_corpus_dir, remove_lfmin_corpus_dir, remove_old_corpus_dir, out_corp, lf_bin, afl_bin
    rename_current_corpus_dir = 'mv ./' + out_corp + '/1/queue ./' + out_corp + '/1/old'
    make_lfmin_corpus_dir = 'mkdir ./' + out_corp + '/1/lfmin'
    make_aflmin_corpus_dir = 'mkdir ./' + out_corp + '/1/queue'
    afl_minimize_cmd = 'afl-cmin -i ./' + out_corp + '/1/lfmin -o ./' + out_corp + '/1/queue -m none -- ./' + afl_bin
    lf_minimize_cmd = './' + lf_bin + ' -merge=1 ' + './' + out_corp + '/1/lfmin ./' + out_corp + '/1/old'
    remove_lfmin_corpus_dir = 'rm -rf ./' + out_corp + '/1/lfmin'
    remove_old_corpus_dir = 'rm -rf ./' + out_corp + '/1/old'


def run_double_fuzzing():
    global dev_null
    dev_null = open(os.devnull, 'w')
    counter = 1
    print '\n>> Fuzz testing with libFuzzer and AFL:'
    print '>> Number of threads is set to ' + str(NR_OF_THREADS) + '.'
    print '>> Runtime per iteration is set to ' + str(FUZZER_RUNTIME) + ' seconds.\n'
    call('echo core >/proc/sys/kernel/core_pattern', stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor', stdout=dev_null,
         stderr=subprocess.STDOUT, shell=True)
    while True:
        try:
            exec_afl_iteration(counter)
            minimize_corpus()
            exec_lf_iteration(counter)
            minimize_corpus()
            print ''
            counter += 1
        except KeyboardInterrupt:
            print '\nReceived interrupt...stopping.\n'
            close_current_fuzz_job()
            dev_null.close()
            sys.exit()


def exec_afl_iteration(counter):
    global afl_firstrun_cmd, afl_run_cmd, dev_null
    print 'AFL: currently fuzzing...'
    if counter == 1:
        afl_run_multi_threaded(afl_firstrun_cmd)
    else:
        afl_run_multi_threaded(afl_run_cmd)
    time.sleep(FUZZER_RUNTIME)
    close_current_fuzz_job()
    print 'AFL: finished iteration ' + str(counter) + '.'


def afl_run_multi_threaded(run_cmd):
    global dev_null, out_corp, afl_bin, running_process_pids
    fuzzer_id = 1
    main_run_cmd = run_cmd + str(' -M ' + str(fuzzer_id) + ' ./' + afl_bin)
    if run_cmd == afl_run_cmd:
        call(main_run_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
        clean_up_resume_dir = 'rm ./' + out_corp + '/1/_resume/*'
        call(clean_up_resume_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
        proc = Popen(main_run_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True, preexec_fn=os.setsid)
        running_process_pids.append(proc.pid)
    else:
        proc = Popen(main_run_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True, preexec_fn=os.setsid)
        running_process_pids.append(proc.pid)
    for i in range(NR_OF_THREADS - 1):
        fuzzer_id += 1
        secondary_run_cmd = run_cmd + str(' -S ' + str(fuzzer_id) + ' ./' + afl_bin)
        proc = Popen(secondary_run_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True, preexec_fn=os.setsid)
        running_process_pids.append(proc.pid)


def exec_lf_iteration(counter):
    global dev_null, lf_run_cmd, running_process_pids
    print 'libFuzzer: currently fuzzing...'
    proc = Popen(lf_run_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True, preexec_fn=os.setsid)
    running_process_pids.append(proc.pid)
    time.sleep(FUZZER_RUNTIME)
    close_current_fuzz_job()
    print 'libFuzzer: finished iteration ' + str(counter) + '.'


def minimize_corpus():
    global rename_current_corpus_dir, make_lfmin_corpus_dir, lf_minimize_cmd, afl_minimize_cmd, \
        make_aflmin_corpus_dir, remove_lfmin_corpus_dir, remove_old_corpus_dir, dev_null, out_corp
    print 'Minimizing main corpus...'
    call(rename_current_corpus_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call(make_lfmin_corpus_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call(make_aflmin_corpus_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call(lf_minimize_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call(afl_minimize_cmd, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call(remove_lfmin_corpus_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call(remove_old_corpus_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    print 'Main corpus minimized.'


def close_current_fuzz_job():
    global running_process_pids
    for proc_pid in running_process_pids:
        os.killpg(os.getpgid(proc_pid), signal.SIGTERM)
    running_process_pids = []


''' Program '''

parse_arguments()
generate_run_commands()
generate_corpus_minimization_commands()
run_double_fuzzing()


