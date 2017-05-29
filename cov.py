from subprocess import call
import sys
import subprocess
import os


''' Global variables '''

nosan_bin = None
corpus_dir = None
results_dir = None


''' Functions '''


def parse_arguments():
    global nosan_bin, corpus_dir, results_dir
    if not (len(sys.argv) == 4):
        print '\nUsage: python2.7 cov.py <nosan_binary> <corpus_dir> <results_dir>\n'
        sys.exit()
    else:
        nosan_bin = str(sys.argv[1])
        corpus_dir = str(sys.argv[2])
        results_dir = str(sys.argv[3])


def produce_coverage_results():
    global nosan_bin, corpus_dir, results_dir
    dev_null = open(os.devnull, 'w')
    results_file = open('results.txt', 'w')
    get_corpus_coverage_cmd = './' + nosan_bin + ' ' + corpus_dir + ' -runs=0 -dump_coverage=1'
    call(get_corpus_coverage_cmd, stdout=results_file, stderr=subprocess.STDOUT, shell=True)
    results_file.close()

    results_file = open('results.txt', 'r')
    output_lines = results_file.read().split('\n')
    nr_of_guards = get_nr_of_guards(output_lines)
    initialized_coverage = get_initialized_coverage(output_lines)
    sancov_filename = get_sancov_filename(output_lines)
    coverage_ratio = initialized_coverage / nr_of_guards
    results_file.close()

    results_file = open('results.txt', 'a')
    results_file.write('\nThe coverage ratio of the corpus is: ' + ('%.3f' % coverage_ratio) + '\n\n')
    print '\nThe coverage ratio of the corpus is: ' + ('%.3f' % coverage_ratio) + '\n'
    results_file.close()
    symcov_filename = generate_symcov_file(sancov_filename, dev_null)
    call('mkdir ' + results_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('mv results.txt ' + results_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('mv ' + sancov_filename + ' ' + results_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    call('mv ' + symcov_filename + ' ' + results_dir, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    dev_null.close()


def get_nr_of_guards(output_lines):
    for i in range(len(output_lines)):
        output_line = output_lines[i].split()
        for j in range(len(output_line)):
            if 'guards):' in output_line[j]:
                return float(output_line[j - 1][1:])
    return None


def get_initialized_coverage(output_lines):
    for i in range(len(output_lines)):
        output_line = output_lines[i].split()
        for j in range(len(output_line)):
            if 'INITED' in output_line[j]:
                return float(output_line[j + 2])
    return None


def get_sancov_filename(output_lines):
    for i in range(len(output_lines)):
        output_line = output_lines[i].split()
        for j in range(len(output_line)):
            if 'SanitizerCoverage:' in output_line[j]:
                return str(output_line[j + 1][2:])
    return None


def generate_symcov_file(sancov_filename, dev_null):
    global nosan_bin, corpus_dir
    symcov_filename = nosan_bin + '.' + corpus_dir + '.symcov'
    symcov_command = 'sancov -symbolize ' + sancov_filename + ' ' + nosan_bin + ' > ' + symcov_filename
    call(symcov_command, stdout=dev_null, stderr=subprocess.STDOUT, shell=True)
    return symcov_filename


''' Program '''

parse_arguments()
produce_coverage_results()








