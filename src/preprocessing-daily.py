#!/bin/python3

import os
import re
import logging
import datetime
import argparse
import subprocess
import pandas as pd
from pathlib import Path
from glob import glob
from pathlib import Path

"""
Preprocessing of video files using metadata extracted from inventory files
To execute, all videos that need to be flipped should be already done
"""
class Preprocessing:
    
    def __init__(self, args):        
        
        self.USE_GPU = self.has_nvidia_gpy()
        self.input_path = args.input_data
        self.experiment = args.experiment
        self.rotate = args.rotate # set to True if videos need to be rotated
        self.target_date = args.target_date
        target_metadata = args.meta_data if args.meta_data else 'cleaned'
        self.local_path = args.local
        self.metadata_path = os.path.join(self.local_path,'metadata', target_metadata)
        self.temp_path = os.path.join(self.local_path, 'temp')
        self.log_path = os.path.join(self.local_path, 'log')
        self.output_path = args.output_data
        self.convert_flags = "-vcodec h264 -acodec aac -movflags +faststart"
        self.convert_flags = '-vf "transpose=1" ' + self.convert_flags if self.rotate else self.convert_flags
        self.concat_flags = "-c copy -movflags +faststart"
        self.ext = '.mp4'    # MP4 or mp4            
                        
        logging.basicConfig(
            filename = os.path.join(self.log_path, self.experiment + '_' + self.target_date +'.log'),
            encoding = 'utf-8',
            level = logging.NOTSET
            )
        
        for this_path in [self.temp_path, self.log_path, self.output_path, self.metadata_path]:
            if not os.path.isdir(this_path):
                if('meta' in this_path):
                    logging.error('Metadata requested folder does not exist in %s', self.metadata_path)
                    exit()
                else:
                    os.mkdir(this_path)
        
    
    # check for GPU presence 
    def has_nvidia_gpy(self):
        try:
            result = subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    # handle ffmpeg command specifically
    def run_ffmpeg(self, cmd):
        """Run an ffmpeg command with error handling."""    
        if self.USE_GPU: 
            print('using GPU')
            cmd = re.sub(r'-vcodec h264', '-c:v h264_nvenc', cmd)
        #logging.info(cmd)        
        try:
            subprocess.run(cmd, shell=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"FFmpeg command failed. Error: \n {e}")
            return False

    # handle the preprocessing of videos
    # using ffmpeg
    def preprocess_video(self, row):
        video_delta = int(row['endNb']) - int(row['startNb'])
        logging.info(f"Treating metadata file {row['start_file']}")
        # processes multiple replicates
        if(video_delta >= 1):
            start_out = os.path.join(self.temp_path, os.path.basename(row['start_file']))
            end_out = os.path.join(self.temp_path, os.path.basename(row['end_file']))
            concat_list = os.path.join(self.temp_path, os.path.basename(row['out_file'])+'.txt')
            cmd = f"ffmpeg -i \"{row['start_file']}\" -ss {row['startTime']} {self.convert_flags} \"{start_out}\""
            ok = self.run_ffmpeg(cmd)

            if ok:
                cmd = f"ffmpeg -i \"{row['end_file']}\" -to {row['endTime']} {self.convert_flags} \"{end_out}\""               
                ok = self.run_ffmpeg(cmd)

                     
                start_filename = os.path.basename(row['start_file'])       
                ext = '_blurred' + self.ext if 'blurred' in start_filename else self.ext 
                #TODO: confirm change
                file_bsn = re.sub(r'\d'+ ext, '', start_filename)
                #file_bsn = re.sub(r'\d+.MP4', '', os.path.basename(row['start_file']))
                if ok:
                    with open(concat_list, 'w') as handle:
                        for i in range(int(row['startNb']), int(row['endNb'])+1):
                            this_path = str(Path(f"{self.input_path}/{row['day']}/{file_bsn}{i}{ext}"))
                            tmp = f"file {this_path}\n"
                            handle.write(tmp)

                    cmd = f"ffmpeg -f concat -safe 0 -i \"{concat_list}\" {self.concat_flags} \"{row['out_file']}\""
                    ok = self.run_ffmpeg(cmd)

        # processes a single replicate
        else:
            cmd = f"ffmpeg -ss {row['startTime']} -to {row['endTime']} -i \"{row['start_file']}\" {self.convert_flags} \"{row['out_file']}\""
            self.run_ffmpeg(cmd)
        
        return 'processed'
        
    
    # check if start, end, and output files exist 
    # or not before calling preprocessing task
    def check_files(self, row, col, ext):
        main_path = self.output_path if 'outfile' in col else self.input_path
        if(row[col]):            
            filename = os.path.join(main_path,row['day'],row[col]+ext)
            if('outfile' in col):
                if not os.path.isfile(filename):
                    return filename
                else:
                    logging.info('Skipping: output file already processed.')
                    return pd.NA
            else:
                # if not os.path.isfile(filename):
                #     logging.error("Cannot find %s file %s", col, filename)
                #     return pd.NA
                # else:
                    return filename
        else:
            logging.error('Value missing for %s', col)
    
    
    # run main method for preprocessing
    def run(self):                         
        # select target date if specified   
        ext = self.target_date +'*.csv' if self.target_date else '*.csv'        
        files_lst = glob(os.path.join(self.metadata_path,ext))
        print('Inventory files to be processed:', files_lst)
        
        metadata_map = {}
        for file in files_lst:
            start, end = re.search(r'\d{2}\D{3}\d{4}', file).span()
            this_date = file[start:end]
            metadata_map[this_date] = pd.read_csv(file, index_col = 0)

        # iterate over multiple dates
        for this_date, metadata in metadata_map.items():
            
                if not os.path.isdir(os.path.join(self.output_path,this_date)):
                    os.mkdir(os.path.join(self.output_path,this_date))
                    
                metadata = metadata_map[this_date]
                metadata['day'] = this_date
                logging.info(f'Treating metadata file for date {this_date} location {self.metadata_path}')
                
                # check and define paths for start, end, and output files
                metadata['start_file'] = metadata.apply(lambda x: self.check_files(x, 'startLabel', self.ext), axis=1)
                metadata['end_file'] = metadata.apply(lambda x: self.check_files(x, 'endLabel', self.ext), axis=1)
                metadata['out_file'] = metadata.apply(lambda x: self.check_files(x, 'outfile', ''), axis=1)
                
                # preprocess video according to specific replicates
                # using ffmpeg
                metadata = metadata[~metadata['out_file'].isna()]
                metadata['status'] = metadata.apply(lambda x: self.preprocess_video(x), axis=1)
                
                # clear up temp files
                tmp_files = glob(os.path.join(self.temp_path,'*'))
                # for file in tmp_files:
                #     os.remove(file)



if __name__ == '__main__':
    
    # arg values for debugging
    default_args = {
        'input_data': os.path.join(os.getcwd() + '/project_name/raw/'),
        'local': os.getcwd(),
        'meta_data': 'debug/',
        'target_date': '21MAY2025',
        'experiment': "project_name",
        'output_data': os.path.join(os.getcwd() + '/processed/'),
        'rotate': False
    }
        
    # Initialize argument parser with default values
    parser = argparse.ArgumentParser(description='Preprocessing of video files using metadata extracted from inventory files')    
    parser.add_argument('-i', '--input_data', type=str, default=default_args['input_data'], help='PATH to the parent directory containing the data to process.')
    parser.add_argument('-l', '--local', default=default_args['local'], type=str, help='PATH to local directory to save logs, find metadata, save temp files.')
    parser.add_argument('-m', '--meta_data', type=str, default=default_args['meta_data'], help='Name of folder in /metadata/ to retrieve files to process.')
    parser.add_argument('-dt', '--target_date', type=str, default=default_args['target_date'], help='Target day in format DDMMMYYYY (e.g. 13SEP2024) to process.')
    parser.add_argument('-rt', '--rotate', action="store_true", default=default_args['rotate'], help='Enable rotate videos in 90 degrees.')
    parser.add_argument('-e', '--experiment', type=str, default=default_args['experiment'], help='Experiment name to process the data for.')
    parser.add_argument('-o', '--output_data', type=str, default=default_args['output_data'], help='PATH to a directory for outputting the files')
    
    args = parser.parse_args()
    preprocess = Preprocessing(args)     
    preprocess.run()

    print('Preprocessing of videos completed!')
