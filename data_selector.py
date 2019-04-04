import numpy as np
from datetime import datetime as dt


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
        bricks_used = {}
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
            bricks_used[brick] = np.product(brick_col_usage)           
    else:
        bricks_used = {brick:1 for brick in bricks_selected}
    return bricks_used

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

def slice_data(data, axis_name_list, criteria_dict):
    ''' given criteria {'column_name':(min, max)}, return sliced '''
    #print("slicing...")
    t0 = dt.now()
    # TODO: Individual slicing for more efficient computation
    print(criteria_dict.items())
    selection = np.all(
        [np.all([data[col_name] > limits[0], data[col_name] < limits[1]], 0)
            for col_name, limits in criteria_dict.items()],
        0)
    #print(len(selection), np.sum(selection))
    #print("{}".format(dt.now()-t0))
    return data[selection]#reduce_cols(data[selection], axis_name_list)
##################################################################################
