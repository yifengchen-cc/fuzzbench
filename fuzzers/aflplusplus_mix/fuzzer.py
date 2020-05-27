# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Integration code for AFLSmart fuzzer."""

import os
import shutil
import subprocess
import glob

from multiprocessing import Pool
from fuzzers.afl import fuzzer as afl_fuzzer
from fuzzers.aflplusplus import fuzzer as aflplusplus_fuzzer
from fuzzers import utils

# OUT environment variable is the location of build directory (default is /out).
def get_cmplog_build_directory(target_directory):
    """Return path to CmpLog target directory."""
    return os.path.join(target_directory, 'cmplog')


def build():
    """Build benchmark."""
    aflplusplus_fuzzer.build('instrim', 'laf','cmplog')

    print('[post_build] Copying libradamsa.so to $OUT directory')
    shutil.copy('/afl/libradamsa.so', os.environ['OUT'])

    # Copy Peach binaries to OUT
    shutil.copytree('/afl/peach-3.0.202-source/output/linux_x86_64_debug/bin',
                    os.environ['OUT'] + '/peach-3.0.202')

    # Copy supported input models
    for file in glob.glob('/afl/input_models/*.xml'):
        print(file)
        shutil.copy(file, os.environ['OUT'])


def fuzz_func(command):
    global output_stream
    print('[run_fuzzer] Running command: ' + ' '.join(command))
    subprocess.call(command, stdout=output_stream, stderr=output_stream)

def fuzz(input_corpus, output_corpus, target_binary):
    global output_stream
    hide_output = False
    target_binary_directory = os.path.dirname(target_binary)
    cmplog_target_binary_directory = (
        get_cmplog_build_directory(target_binary_directory))
    target_binary_name = os.path.basename(target_binary)
    cmplog_target_binary = os.path.join(cmplog_target_binary_directory,
                                        target_binary_name)
    """Run afl-fuzz on target."""
    afl_fuzzer.prepare_fuzz_environment(input_corpus)
    os.environ['PATH'] += os.pathsep + '/out/peach-3.0.202/'

    input_model = ''
    benchmark_name = os.environ['BENCHMARK']
    if benchmark_name == 'libpng-1.2.56':
        input_model = 'png.xml'
    if benchmark_name == 'libpcap_fuzz_both':
        input_model = 'pcap.xml'
    if benchmark_name == 'libjpeg-turbo-07-2017':
        input_model = 'jpeg.xml'

    flags = ['-pmmopt']  # rare branch scheduling.
    flags += ['-s123']  # fixed random seed.
    flags += ['-h'] # Enable stacked mutations
    flags += ['-w','peach'] # Enable structure-aware fuzzing
    flags += ['-g',input_model] # Select input model
    if os.path.exists(cmplog_target_binary):
        flags += ['-c', cmplog_target_binary]
    if input_model != '':
        fuzzer_name = 'fuzzer'
        command = ['./afl-fuzz','-S',fuzzer_name,'-i',input_corpus,'-o',output_corpus,'-m','none']
        if flags:
            command.extend(flags)
        dictionary_path = utils.get_dictionary_path(target_binary)
        if dictionary_path:
            command.extend(['-x', dictionary_path])
        command += [
            '--',
            target_binary,
            # Pass INT_MAX to afl the maximize the number of persistent loops it
            # performs.
            '2147483647'
        ]
        output_stream = subprocess.DEVNULL if hide_output else None
        command1 = ['./afl-fuzz','-S',fuzzer_name,'-i',input_corpus,'-o',output_corpus,'-m','none','-L0','-pmmopt','-s123','--',target_binary,'2147483647']
        command2 = ['./afl-fuzz','-S',fuzzer_name,'-i',input_corpus,'-o',output_corpus,'-m','none','-L0','-pmmopt','-s123','--',target_binary,'2147483647']
        command3 = ['./afl-fuzz','-S',fuzzer_name,'-i',input_corpus,'-o',output_corpus,'-m','none','-R','-pmmopt','-s123','--',target_binary,'2147483647']
        command4 = list(command)
        command5 = list(command)
        command_list = [command1,command2,command3,command4,command5]
        for i in range(0,5):
            command_list[i][2]=fuzzer_name+str(i)
            #print('[run_fuzzer] Running command: ' + ' '.join(command_list[i]))
        
        with Pool(5) as p:
            p.map(fuzz_func,command_list)
        
