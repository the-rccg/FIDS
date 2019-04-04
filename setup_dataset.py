import numpy as np
import json
from pprint import pprint

# Load Settings
settings = json.load(open('settings.json'))

# File names
# TODO: Allow dictionary for renaming in display
from os import listdir
filename_list = sorted([file for file in listdir(settings['folderpath']) if file[-5:].lower()==".fits"])

# Load Data
from astropy.io import fits
# TODO: Allow dictionary for renaming in display
data = {
            filename: fits.open(settings['folderpath'] + filename, memmap=True)[1] 
            for filename in filename_list
        }

# Defining columns
# TODO: Allow dictionary for renaming in dispaly
column_names_file = sorted(settings['columns_to_use'])
column_names_data = sorted(data[filename_list[0]].columns.names)
if column_names_file:
    column_names = [
        column_name for column_name in column_names_file 
            if column_name in column_names_data
    ]
else:
    column_names = sorted(data[filename_list[0]].columns.names)

########################################################################################
#   Compute brick detaiks
########################################################################################
slice_col_list = column_names#[0:5]
print("Slice Col List: ", slice_col_list)
acceptable_types = ['>f8', '>f4', '>i8', '>i4']

from io_tools import save_json, load_json
def get_missing_brick_info(brick_column_details, brick_name_list, column_list):
    brick_data_types = dict(data[filename_list[0]].data.dtype.descr)
    # Save all columns missing for each brick
    missing_column_dict = {}
    for brick_name in brick_name_list:
        if brick_name not in brick_column_details.keys():
            missing_column_dict[brick_name] = column_list
        else:
            missing_column_dict[brick_name] = [
                column for column in column_list 
                if column not in brick_column_details[brick_name] \
                    and brick_data_types[column] in acceptable_types]
            missing_column_dict[brick_name] += [
                column for column in brick_column_details[brick_name]
                if ('max' not in brick_column_details[brick_name][column] \
                    or 'min' not in brick_column_details[brick_name][column]) \
                    and brick_data_types[column] in acceptable_types]
    pprint(missing_column_dict)
    # Compute all columns for each brick
    #try:
    #    brick_column_details = {
    #        brick_name:{
    #            col_name: {
    #                'min': data[brick_name].data[col_name].min(),
    #                'max': data[brick_name].data[col_name].max(),
    #            }
    #            for col_name in slice_col_list
    #        }
    #        for brick_name in filename_list
    #    }
    #except OSError as exception:
    #try:
    # Handle small paging
    #print(exception)
    # Compute all columns missing for each brick
    added_info = False
    for brick_name in missing_column_dict.keys():
        print(brick_name)
        if brick_name not in brick_column_details.keys():
            brick_column_details[brick_name] = {}
        for col_name in missing_column_dict[brick_name]:
            brick_column_details[brick_name][col_name] = {}
            try:
                minimum = data[brick_name].data[col_name].min()
                print(minimum)
                brick_column_details[brick_name][col_name]['min'] = parse_datatype(minimum)
                added_info = True
            except Exception as e:
                print(brick_name, e)
            try:
                maximum = data[brick_name].data[col_name].max()
                print(maximum)
                brick_column_details[brick_name][col_name]['max'] = parse_datatype(maximum)
                added_info = True
            except Exception as e:
                print(brick_name, e)
        if added_info:
            save_json(brick_column_details, 'brick_column_details.json', savepath=settings['savepath'])
            added_info = False
    #except:
    #    print('serious problem')
    #    raise
    if added_info:
        save_json(brick_column_details, 'brick_column_details.json', savepath=settings['savepath'])
    return brick_column_details

def parse_datatype(value):
    if type(value) in [np.int64, np.int32]:
        return int(value)
    elif type(value) in [np.float64, np.float32]:
        return float(value)
    elif type(value) in [np.bool_]:
        return bool(value)
    else:
        return value

brick_column_details = load_json('brick_column_details.json', savepath=settings['savepath'])
brick_column_details = get_missing_brick_info(brick_column_details, filename_list, slice_col_list)
########################################################################################
