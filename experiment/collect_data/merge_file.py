import pandas as pd
import os
import posixpath

collect_data_root = os.environ.get('COLLECT_DATA_ROOT')
data_path = posixpath.join(collect_data_root,'csv')
file_list = os.listdir(data_path)
print(file_list)
df = pd.read_csv(posixpath.join(data_path,file_list[0]))
keep_col = ['time','trial_id','edges_covered','id','fuzzer','experiment','benchmark','time_started','time_ended']
new_f = df[keep_col]
new_f.to_csv("data.csv",index=False)
for i in range(1,len(file_list)):
    df = pd.read_csv(posixpath.join(data_path,file_list[i]))
    new_f = df[keep_col]
    new_f.to_csv("data.csv",index=False,header=False,mode='a+')
    
