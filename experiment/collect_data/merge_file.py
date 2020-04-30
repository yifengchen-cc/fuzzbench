import pandas as pd
import os
import posixpath
import argparse

collect_data_root = os.environ.get('COLLECT_DATA_ROOT')
data_path = posixpath.join(collect_data_root,'csv')
keep_col = ['time','trial_id','edges_covered','id','fuzzer','experiment','benchmark','time_started','time_ended']

def merge_all():
    file_list = os.listdir(data_path)
    print(file_list)
    df = pd.read_csv(posixpath.join(data_path,file_list[0]))
    new_f = df[keep_col]
    new_f.to_csv("data.csv",index=False)
    for i in range(1,len(file_list)):
        df = pd.read_csv(posixpath.join(data_path,file_list[i]))
        new_f = df[keep_col]
        new_f.to_csv("data.csv",index=False,header=False,mode='a+')


def manual_merge(file_list):
    for i in range(0,len(file_list)):
        df = pd.read_csv(posixpath.join(data_path,file_list[i]))
        new_f = df[keep_col]
        new_f.to_csv("data.csv",index=False,header=False,mode='a+')
        

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m',
                        '--manual',
                        help='merge selected data from data path',
                        required=False,
                        nargs='+',
                        default=[]
                       )    
    args = parser.parse_args()
    
    if not args.manual :
        merge_all()
    else:
        manual_merge(args.manual)

if __name__ == '__main__':
    main()
