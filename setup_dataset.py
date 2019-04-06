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
from get_file_info import get_missing_brick_info
from io_tools import load_json
brick_column_details = load_json('brick_column_details.json', savepath=settings['savepath'])
brick_column_details = get_missing_brick_info(data, brick_column_details, filename_list, slice_col_list, acceptable_types=acceptable_types)
########################################################################################