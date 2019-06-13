# -*- coding: utf-8 -*-
"""
Setup dataset min/max for slider use in FIDS
"""

# Import
import numpy as np
import json
from pprint import pprint
from os import listdir
from astropy.io import fits
# TODO: Integrate better to run smoothly when starting FIDS


# Load Settings
settings = json.load(open('../settings.json'))

# File names
filename_list = get_valid_filelist(settings['folderpath'], settings['filetypes'])

# Load Data
data = get_dict_of_files(filename_list, settings['folderpath'])

# Get File Descriptions
data_counts = get_data_counts(data, ftype=settings['filetypes'][0])  
# Defining columns
# TODO: Read or allow import of UNITS. Maybe visual initialization as an app?
column_names_file = sorted(settings['columns_to_use'])
column_names_data = sorted(data[filename_list[0]].columns.names)
column_names = get_column_names(data, filename_list, column_names_file, column_names_data)
# Reduce Columns to Useful
selected_columns = column_names
selected_columns.remove(settings['name_column']) #[name for name in column_names if name.split('_')[-1] not in ['p50', 'p84', 'p16', 'Exp']]


########################################################################################
#   Compute brick details
########################################################################################
slice_col_list = column_names#[0:5]
print("Slice Col List: ", slice_col_list)
from .get_file_info import get_missing_brick_info
from ..io_tools import load_json
brick_column_details = load_json('brick_column_details.json', savepath=settings['savepath'])
brick_column_details = get_missing_brick_info(
    data, brick_column_details, filename_list, slice_col_list, 
    acceptable_types=settings['allowed_slider_dtypes'])
########################################################################################
