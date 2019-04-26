import numpy as np
from datetime import datetime as dt
import time

from memory_profiler import profile

##################################################################################
#   Slicing Data
##################################################################################
def get_limits(bricks_selected, limit_dict, brick_column_details):
    ''' returns limits that are smaller than the limits in the selected bricks '''
    if limit_dict:
        brick_limits = {
            col_name:[ 
                np.min([brick_column_details[brick][col_name]['min'] for brick in bricks_selected]),
                np.max([brick_column_details[brick][col_name]['max'] for brick in bricks_selected])
            ]
            for col_name in limit_dict.keys()
        }
        #print('brick_limits: ', brick_limits)
        lim_dict = {
            col_name:[
                max(limit_dict[col_name][0], brick_limits[col_name][0]),
                min(limit_dict[col_name][1], brick_limits[col_name][1])
            ]
            for col_name in limit_dict.keys()
            if (limit_dict[col_name][0] > brick_limits[col_name][0]) \
                or (limit_dict[col_name][1] < brick_limits[col_name][1])
        }
        #print('lim_dict: ', lim_dict)
    else:
        lim_dict = {}
    return lim_dict

def get_brick_usage(bricks_selected, limit_dict, brick_column_details):
    ''' returns dict with brick name and fraction of brick used '''
    if limit_dict:
        brick_usage = {}
        for brick in bricks_selected:
            brick_col_usage = []
            for col_name in limit_dict.keys():
                # Intersection Size = max(0, min(maxes) - max(mins))
                intersection_size = np.max([
                    np.min([
                        brick_column_details[brick][col_name]['max'],
                        limit_dict[col_name][1]
                    ]) - np.max([
                        brick_column_details[brick][col_name]['min'],
                        limit_dict[col_name][0]
                    ]),
                    0])
                brick_interval_size = brick_column_details[brick][col_name]['max']-brick_column_details[brick][col_name]['min']
                brick_col_usage.append(
                    intersection_size/brick_interval_size
                )     
            brick_usage[brick] = np.product(brick_col_usage)           
    else:
        brick_usage = {brick:1 for brick in bricks_selected}
    return brick_usage

def get_relevant_bricks(bricks_selected, criteria_dict, brick_column_details, min_usage):
    # Adjust for Brick usage: Only use above min, oversample proportionally, etc.
    brick_usage = get_brick_usage(bricks_selected, criteria_dict, brick_column_details)
    print(brick_usage)
    bricks_selected = [
        brick for brick in bricks_selected 
        if brick_usage[brick] > min_usage
    ]
    return bricks_selected

def reduce_cols(data, axis_name_list):
    ''' slice by axis name list '''
    # TODO: testing other implementation
    #     data.from_columns(axis_name_list, nrows=len(data))
    selection = {
        axis_name:data[axis_name]
        for axis_name in axis_name_list
    }
    # Test:  ValueError: could not convert string to float: 'PHAT J....' (since np.empty has 1 type rather than multiple)
    #selection = np.empty((len(data), len(axis_name_list)))
    #for i, axis_name in enumerate(axis_name_list):
    #    selection[:,i] = data[axis_name]
    return selection

def get_within_limits(data, col_name, limits):
    return np.logical_and(
        data.data[col_name] > limits[0], 
        data.data[col_name] < limits[1]
    )

def slice_data(data, axis_name_list, criteria_dict, list_comp=True):
    ''' given data array, slice it and return 
    criteria {'column_name':(min, max)}, return sliced '''
    data = data.data
    # Bulk slicing
    if list_comp:
        t1 = time.time()
        selection = np.all(
            [get_within_limits(data, col_name, limits)
                for col_name, limits in criteria_dict.items()],
            0)
        t2 = time.time()
        print("list comprehension: {:.2f}s".format(t2-t1))
    # Individual slicing for more efficient computation
    else:
        t1 = time.time()
        selection = np.array([])#np.ones(data.data.shape[0], dtype=bool)
        for col_name, limits in criteria_dict.items():
            if selection.shape[0] < 2:
                selection = get_within_limits(data, col_name, limits)
            else:
                np.logical_and(selection, get_within_limits(data, col_name, limits), out=selection)
        t2 = time.time()
        print("cycle {:.2f}s".format(t2-t1))
    return data[selection]
##################################################################################
# No longer used...

def get_slice_idx(data, axis_name_list, criteria_dict):
    ''' given criteria {'column_name':(min, max)}, return sliced '''
    # Bulk slicing
    #print(criteria_dict.items())
    #t1 = time.time()
    selection = np.all(
        [get_within_limits(data, col_name, limits)
            for col_name, limits in criteria_dict.items()],
        0)
    #t2 = time.time()
    #print("list comprehension: {:.2f}s".format(t2-t1))
    return selection

def get_slice_idx2(data, axis_name_list, criteria_dict):
    ''' given criteria {'column_name':(min, max)}, return sliced '''
    # Individual slicing for more efficient computation
    #t1 = time.time()
    selection = np.array([])#np.ones(data.data.shape[0], dtype=bool)
    for col_name, limits in criteria_dict.items():
        if selection.shape[0] < 2:
            selection = get_within_limits(data, col_name, limits)
        else:
            np.logical_and(selection, get_within_limits(data, col_name, limits), out=selection)
    #t2 = time.time()
    #print("cycle {:.2f}s".format(t2-t1))
    return selection
