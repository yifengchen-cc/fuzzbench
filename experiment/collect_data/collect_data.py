from threading import Timer
import _thread
import time
import os
import csv
import posixpath
import fcntl

#from common import filesystem
import filesystem

timer=[None for i in range(10)]
TRAIL_NUM=2
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
            print(path_total,cur_time)
            self.write_data_file(path_total,cur_time)
        global timer
        timer[self.trail_id] = Timer(3,self.get_path_total,(filename,))
        timer[self.trail_id].start()
    
    def loop_fetch(self,filename):
        global timer
        timer[self.trail_id] = Timer(3,self.get_path_total,(filename,))
        timer[self.trail_id].start()
        time.sleep(180)
        timer[self.trail_id].cancel()
        print("cancel")
    
def ini_trail_loop(experiment,fuzzer,benchmark):

    global start_time
    start_time=int(time.time())
    for i in range(TRAIL_NUM):
        coldat = CollectData(i,experiment,fuzzer,benchmark)
        data_folder = '-'.join([fuzzer,benchmark,str(i)])
        filename = 'plot_data'
        file_path = posixpath.join(collect_data_root,data_folder,filename)
        print(file_path)
        try:
            _thread.start_new_thread(coldat.loop_fetch,(file_path,))
        except:
            print("create thread error!")

def main():
    ini_trail_loop('project-0','afl','curl')
    while 1:
        pass
    return 0

if __name__ == '__main__':
    main()
