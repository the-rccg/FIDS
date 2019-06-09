# -*- coding: utf-8 -*-
from memory_profiler import profile
# General
import os
# Processing
import numpy as np
# Data Type support
import json
# Import IO Packs
from .fits import get_fitstable_data, get_data_counts_fits, get_brick_data_types_fits

# TODO: Implement other filetypes in the future
read_fncs = {
    'fits': get_fitstable_data
}

data_count_fncs = {
    'fits': get_data_counts_fits
}

data_type_fncs = {
    'fits': get_brick_data_types_fits
}


# JSON Handling


def load_json(filename, savepath='/'):
    """ check if it exists, if so, load it """
    if filename in os.listdir(savepath):
        return json.load(open(savepath+filename, 'r'))
    else:
        print("{} not in directory".format(filename))
        return {}


def save_json(dictionary, filename, savepath='/'):
    """ save dictionary as json """
    with open(savepath+filename,'w') as f:
        json.dump(dictionary, f, sort_keys=True, indent=4)
    return True


# Type Handling


def get_ftype(filename):
    return filename.split(".")[-1].lower()


def parse_datatype(value):
    """ numpy datatypes to python native types for JSON serialization """
    if type(value) in [np.int64, np.int32]:
        return int(value)
    elif type(value) in [np.float64, np.float32]:
        return float(value)
    elif type(value) in [np.bool_]:
        return bool(value)
    else:
        return value


def map_types(dictionary):
    """ NOTE: The following give DIFFERENT types
    data.data[col_name].dtype       -- read as NumPy array (desired)  e.g. >f8, <U100
    dict(data.columns.dtype.descr)  -- fastest to get (raw storaoge)  e.g. <f8, |S100
    data.data.columns.dtype.fields  -- Python dtype                   e.g. float64, S100
    dict(data.data.dtype.descr))    -- ???                            e.g. >f8, |S100

    # TODO: This is still a hacky attempt to fix things for FITS
    #       more general solution needed
    """
    for key in dictionary.keys():
        if dictionary[key][0] == "<":
            dictionary[key] = ">"+dictionary[key][1:]
        if dictionary[key][0] == "|":
            dictionary[key] = "<"+dictionary[key][1:]
        if dictionary[key][1] == "S":
            dictionary[key] = dictionary[key][0] + "U" + dictionary[key][2:]
    return dictionary


# Getting Data


def get_valid_filelist(folderpath, filetypelist):
    """ Return files with proper file ending 
    
    Check if it contains a point 
    and if proper filetype in ending 
    """
    return sorted(
        [
            filename for filename in os.listdir(folderpath) 
            if len(filename.split(".")) > 1 \
                and (get_ftype(filename) in filetypelist)
        ]
    )


def get_dict_of_files(filename_list, folderpath, memmap=True):
    """ Return dictonary of files to access
    
    Recognize filetype and use appropriate function to read file 
    """
    return {
        filename: read_fncs[get_ftype(filename)](folderpath+filename, memmap=True)
        for filename in filename_list
    }


def get_data_counts(data, ftype):
    return data_count_fncs[ftype](data)


def get_brick_data_types(data, filename_list, ftype=''):
    """ 
    Assumes homogeneous data structure
    Assumes homogeneous file type
    """
    if not ftype:
        ftype = get_ftype(filename_list[0])
    return data_type_fncs[ftype](data, filename_list)
