from threading import Timer
import _thread
import time
import os
import csv
import posixpath
import fcntl
import subprocess
import shlex

#from common import filesystem
import filesystem

timer=[None for i in range(10)]
TRAIL_NUM=2
MAX_TOTAL_TIME=0
FETCH_DATA_TIME=3
#export COLLECT_DATA_ROOT=/root/fuzz/result
collect_data_root = os.environ.get('COLLECT_DATA_ROOT')
start_time=0
row_num=0


class CollectData:
    def __init__(self,trail_id,experiment,fuzzer,benchmark):
        self.fuzzer=fuzzer
        self.benchmark=benchmark
        self.experiment=experiment
        self.trail_id=trail_id

    def write_data_file(self,path_total,cur_time):
        global start_time,row_num
        data_file = posixpath.join(collect_data_root,'data.csv')
        if filesystem.file_exist(data_file): 
            with open(data_file,'a') as f:
                fcntl.flock(f.fileno(),fcntl.LOCK_EX)
                row=[row_num,int(cur_time-start_time),self.trail_id,path_total,self.trail_id,self.fuzzer,self.experiment,self.benchmark,0,0]
                f_csv = csv.writer(f)
                f_csv.writerow(row)
                row_num+=1
                fcntl.flock(f.fileno(),fcntl.LOCK_UN)
        else:
            with open(data_file,'x') as f:
                headers=[' ','time','trial_id','edges_cov','id','fuzzer','experiment','benchmark','time_started','time_ended']
                fcntl.flock(f.fileno(),fcntl.LOCK_EX)
                row=[row_num,int(cur_time-start_time),self.trail_id,path_total,self.trail_id,self.fuzzer,self.experiment,self.benchmark,0,0]
                f_csv = csv.writer(f)
                f_csv.writerow(headers)
                f_csv.writerow(row)
                row_num+=1
                fcntl.flock(f.fileno(),fcntl.LOCK_UN)

            

    def get_last_line(self,filename):
        """
        get last line of a file
        :param filename: file name
        :return: last line or None for empty file
        """
        try:
            filesize = os.path.getsize(filename)
            if filesize == 0:
                return None
            else:
                with open(filename, 'rb') as fp: # to use seek from end, must use mode 'rb'
                    offset = -8                 # initialize offset
                    while -offset < filesize:   # offset cannot exceed file size
                        fp.seek(offset, 2)      # read # offset chars from eof(represent by number '2')
                        lines = fp.readlines()  # read from fp to eof
                        if len(lines) >= 2:     # if contains at least 2 lines
                            return lines[-1]    # then last line is totally included
                        else:
                            offset *= 2         # enlarge offset
                    fp.seek(0)
                    lines = fp.readlines()
                    return lines[-1]
        except FileNotFoundError:
            print(filename + ' not found!')
            return None
    
    def get_path_total(self,filename):
        line = self.get_last_line(filename)
        path_total=-1
        if line:
            line_list = line.decode('utf-8').split(',')
            path_total = int(line_list[3])
            cur_time = int(line_list[0])
            #print(path_total,cur_time)
            self.write_data_file(path_total,cur_time)
        global timer
        timer[self.trail_id] = Timer(FETCH_DATA_TIME,self.get_path_total,(filename,))
        timer[self.trail_id].start()
    
    def loop_fetch(self,filename):
        global timer
        timer[self.trail_id] = Timer(FETCH_DATA_TIME,self.get_path_total,(filename,))
        timer[self.trail_id].start()
        time.sleep(MAX_TOTAL_TIME)
        timer[self.trail_id].cancel()
        print("timer {timer} canceled ".format(timer=self.trail_id))
    
def ini_trail_loop(experiment,fuzzer,benchmark,corpus_data_path,trial_id):

    coldat = CollectData(trial_id,experiment,fuzzer,benchmark)
    filename = 'plot_data'
    file_path = posixpath.join(corpus_data_path,filename)
    print(file_path)
    try:
        _thread.start_new_thread(coldat.loop_fetch,(file_path,))
    except:
        print("create thread error!")

def start_docker(corpus_data_path,fuzzer,benchmark,fuzz_target,docker_url,trail_id):

    """
    docker run -v /root/fuzz/result/afl-curl-0/:/out/corpus \
            --cap-add SYS_NICE --cap-add SYS_PTRACE \
            -e TRIAL_ID=0  -e MAX_TOTAL_TIME=60 \
            -e FUZZER=afl -e BENCHMARK=curl_curl_fuzzer_http \
            -e FUZZ_TARGET=curl_fuzzer_http \
            -it gcr.io/fuzzbench/oss-fuzz/runners/afl/curl >& /tmp/runner.txt &
    """

    start_script = '''docker run -v {corpus_data_path}:/out/corpus --cap-add SYS_NICE --cap-add SYS_PTRACE -e TRIAL_ID={trail_num} -e MAX_TOTAL_TIME={max_total_time} -e FUZZER={fuzzer} -e BENCHMARK={benchmark} -e FUZZ_TARGET={fuzz_target} -it {docker_url} >& /tmp/runner.txt &'''.format(
                    corpus_data_path = corpus_data_path,
                    trail_num = str(trail_id),
                    max_total_time = str(MAX_TOTAL_TIME),
                    fuzzer = fuzzer,
                    benchmark = benchmark,
                    fuzz_target = fuzz_target,
                    docker_url = docker_url)
    #print(shlex.split(start_script))
    process = subprocess.Popen(shlex.split(start_script))



def init_trail(experiment,fuzzer,benchmark,fuzz_target,max_total_time,trail_num,docker_url):
    global MAX_TOTAL_TIME,FETCH_DATA_TIME,TRAIL_NUM,start_time
    MAX_TOTAL_TIME = max_total_time
    TRAIL_NUM = trail_num
    FETCH_DATA_TIME = int(MAX_TOTAL_TIME / 100) # fetch 100 time data

    
    start_time=int(time.time())
    for i in range(TRAIL_NUM):
        data_folder = '-'.join([fuzzer,benchmark,str(i)])
        corpus_data_path = posixpath.join(collect_data_root,data_folder)
        start_docker(corpus_data_path,fuzzer,benchmark,fuzz_target,docker_url,i)
        time.sleep(3)
        ini_trail_loop(experiment,fuzzer,benchmark,corpus_data_path,i)

def main():
    init_trail('project-0','afl','curl_curl_fuzzer_http','curl_fuzzer_http',360,2,'gcr.io/fuzzbench/oss-fuzz/runners/afl/curl')
    while 1:
        pass
    return 0

if __name__ == '__main__':
    main()
