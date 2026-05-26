import pandas as pd
import datetime
import re
import os



class Cleaning:

    def __init__(self):
        self.metadata_path = '/path/to/preprocessing/metadata/'
        self.original_path = self.metadata_path + 'original/' 
        self.cleaned_path = self.metadata_path + 'cleaned/' 
        self.edited_cols = ['projectID','testID','envCode','startNb','startTime','startLabel','endNb','endTime','endLabel','equipID','subjectsID','replicate','comments']    


    def main(self):
        for fichier in os.listdir(self.original_path):
            file = os.path.join(self.original_path,fichier)
            xls = pd.ExcelFile(file)
            for sheet_name in xls.sheet_names:
                self.process_file(file,sheet_name)


    def get_unique_filename(self, path):
        dir_name = os.path.dirname(path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        counter = 1
        new_path = f"{base}_{counter}{ext}"
        while os.path.exists(new_path):
            counter += 1
            new_path = f"{base}_{counter}{ext}"
        return new_path


    def convert_hours_minutes(self, x, filePath):        
        try:
            if type(x) == str:
                values = x.split(':')
                if len(values) == 3:
                    x = datetime.time(
                        hour = int(values[0]),
                        minute = int(values[1]),
                        second = int(values[2])
                    )
                elif len(values) == 2:
                    x = datetime.time(
                        minute = int(values[0]),
                        second = int(values[1]),
                    )
            elif type(x) == float:
                x = str(x).split('.')
                minute = int(x[0])
                second = int(x[1])
                x = datetime.time(
                    minute = minute,
                    second = second
                )
            elif type(x) == datetime.time:
                # if x.hour != 0 and x.second == 0:
                if x.second == 0:
                    hour, minute, second = x.hour, x.minute, x.second
                    # minute = x.hour
                    # second = x.minute
                    x = datetime.time(
                        hour = hour,
                        minute = minute,
                        second = second
                    )
            else:
                print('Error {0} datetime format in {1}'.format(filePath, x))
        except:

                print('Error except {0} datetime format in {1}'.format(filePath, x))
        return x


    def process_file(self, original_file, sheet_n):
        try:

            # Read file
            df = pd.read_excel(
                original_file,
                sheet_name= sheet_n,
                skiprows = [0],
                #index_col=None,
                index_col=False,
                names = self.edited_cols,
                converters={'subjectsID': str}
            )
            
            # get exact date from startLabel
            df['day'] = df['startLabel'].str.split('_', expand=False).str[1]#.split('-',expand=False)
            df['day'] = df['day'].str.split('-', expand=False).str[0]
            
            # Convert time
            time_cols = ['startTime', 'endTime']
            for time_col in time_cols:
                df[time_col] = df[time_col].map(lambda x: self.convert_hours_minutes(x, filePath=original_file))
            
            # # EquipmentID
            df['equipID'] = df['equipID'].str.replace('Cam','')
            df['equipType'] = df['equipID'].str.replace(r'\d+', '', regex=True)
            
            # Comments
            df = df.drop('comments', axis = 1)
            # remove white spaces
            df['subjectsID'] = df['subjectsID'].astype(str).str.replace(' ','')
            df['startLabel'] = df['startLabel'].astype(str).str.replace(' ','')
            df['endLabel'] = df['endLabel'].astype(str).str.replace(' ','')
            
            # Outfile
            df['outfile'] = df['projectID'] + '_' + df['testID'] + '_' + df['envCode'] + '_' + df['day'] + '_' + df['equipID'] + '_' + df['subjectsID'] + '_' + df['replicate'].astype(str) + '.mp4'
            df['outfile'] = df['outfile'].str.replace('(','_')
            df['outfile'] = df['outfile'].str.replace(')','_')
            
            # Filter out the empty fields
            na_cols = ['startNb','endNb','startTime', 'endTime', 'startLabel', 'endLabel']            
            for col in na_cols:
                df = df[~df[col].isna()]
            
            # export files per day
            for this_day in df['day'].unique():                
                day_df = df[df['day'] == this_day]
                for eqType in day_df['equipType'].unique():
                    day_eq_df = day_df[day_df['equipType'] == eqType]
                    output = os.path.join(self.cleaned_path, eqType, f'{this_day}.csv')
                    unique_output = self.get_unique_filename(output)
                    day_eq_df.to_csv(unique_output, index=False)
                                                  
        except Exception as e:
            print(original_file)
            print(e)




if __name__ == "__main__":
    Cleaning().main()
