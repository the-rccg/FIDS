# -*- coding: utf-8 -*-
import numpy as np
from datetime import datetime as dt
import time
from numba import jit

from memory_profiler import profile


def get_sample_indices(sample_size, total_size):
    """ Return data points for the subsample in the range

    Timed Tests:   data_count = 100,000,000;  sample_size = 100,000;
        926 us  np.random.randint(low=0, high=data_count+1, size=sample_size) 
        935 us  np.random.choice(data_count, size=sample_size, replace=True, p=None)
         85 ms  random.sample(range(data_count), sample_size)
          6 s   np.random.choice(data_count, size=sample_size, replace=False, p=None)
    """
    # NOTE: allows multiple identical values, hence n<=num_points, but computes faster
    select_points = np.random.randint(
                        low=0, high=total_size, 
                        size=sample_size
                    )
    return select_points

####################################################################################
#   Getting Data
####################################################################################

def get_all_data(bricks_selected, axis_name_list, criteria_dict, 
                 brick_column_details, brick_data_types, data):
    """ Return all data in bricks which conform by criteria

    Iteratively appends data from bricks
    """
    # 0. Adjust for Brick usage: Only query bricks with data in criteria
    bricks_selected = get_relevant_bricks(bricks_selected, criteria_dict, brick_column_details, min_usage=0)
    # 1. Setup with appropriate types: No length known to fall under criteria
    return_data = {
        axis_name:np.array([], dtype=brick_data_types[axis_name])
        for axis_name in axis_name_list
    }
    current_length = 0
    # 2. Get Data for each brick individually
    for brick_name in bricks_selected:
        # 2.1 Slicing data once reads it once, making it faster than using index
        t1 = dt.now()
        selected_data = slice_data(
                data[brick_name].data,  # Pass immutable for reference to limit copies
                criteria_dict,
                axis_name_list) 
        print("  slice data: {}".format(dt.now()-t1))
        # 2.2. Assign
        # TODO: Test memory and CPU for np.append vs np.concat
        # NOTE: Creates copies. Length unknown, hence no better option. 
        t1 = dt.now()
        for axis_name in axis_name_list:
            return_data[axis_name] = np.append(
                return_data[axis_name], 
                selected_data[axis_name]
            )
        # 4. Wrap up
        sample_size = selected_data[axis_name_list[0]].shape[0]
        current_length += sample_size
    print("  data points: {:,}".format(current_length))
    return return_data

def get_sample_data(bricks_selected, display_count, axis_name_list, criteria_dict, 
                    brick_column_details, data, brick_data_types, data_counts, settings):
    """ Return subsample of data within brick

    Pre-allocate memory, slice, and insert.
    """
    print("  resampling with {} points".format(display_count))
    # 0. Allocate memory
    t1 = dt.now()
    return_data = {
        col_name: np.empty(display_count, dtype=brick_data_types[col_name])
        for col_name in axis_name_list
    }
    print("  memory allocation: {}".format(t1 - dt.now()))
    # 1. Adjust for Brick usage: Only use above min, oversample proportionally, etc.
    brick_usage = get_brick_usage(bricks_selected, criteria_dict, brick_column_details)
    bricks_selected = [
        brick for brick in bricks_selected 
        if brick_usage[brick] > settings['min_brick_usage']
    ]
    brick_count = len(bricks_selected)  # Number of bricks
    current_length = 0
    # 2. Get Data for each Brick
    t1 = dt.now()
    for ix, brick_i in enumerate(bricks_selected):
        # 2.1 Sample Size
        sample_size = round(display_count/brick_count)
        # 2.2 Fix uneven split by rounding, then fill remainder: introduces a skew in data
        if ix == brick_count-1 and brick_count%2 == 1:
            sample_size = int(display_count-current_length)
            print("  adjustment done: {}".format(sample_size))
        # 2.3 Slice Data
        selected_data = get_subsetdata(
                data[brick_i],  # do NOT add ".data" as it will create a copy 
                axis_name_list, 
                sample_size=sample_size, 
                brick_size=data_counts[brick_i],
                criteria_dict=criteria_dict,
                brick_use=brick_usage[brick_i],
                max_fill_attempts=settings['max_fill_attempts'],
                brick_data_types=brick_data_types)
        print("  slice data: {}".format(dt.now()-t1))
        data_size = min(
            sample_size-current_length, 
            min(sample_size, selected_data[axis_name_list[0]].shape[0])
        )
        # 2.4 Assign Data
        for axis_name in axis_name_list:
            try:
                return_data[axis_name][current_length:current_length+data_size] = selected_data[axis_name][0:data_size]
            except Exception as e:
                print("  could not assign, appending. {}".format(e))
                return_data[axis_name] = np.append(return_data[axis_name], selected_data[axis_name])
        print("  assign {}:  {}".format(brick_i, dt.now()-t1))
        current_length += data_size
        t1 = dt.now()
    # 3. Cut Data
    for axis_name in axis_name_list:
        return_data[axis_name] = return_data[axis_name][0:current_length]
    return return_data

def get_subsetdata(brick_data, axis_name_list, sample_size=0, brick_size=0, criteria_dict={}, brick_use=1, max_fill_attempts=1, brick_data_types={}):
    """ 
        Return exact axis subset

        TODO: 
            Speed comparisons
            Implement Dask
    
        References:
            FITS IO (TableData) - http://docs.astropy.org/en/stable/io/fits/ 
            FITS_rec has as base numpy.recarray, inherits all methods of numpy.ndarray
            NumPy Structured Arrays - https://docs.scipy.org/doc/numpy/user/basics.rec.html
            NumPy Recarray - https://docs.scipy.org/doc/numpy/reference/generated/numpy.recarray.html
            NumPy Record - https://docs.scipy.org/doc/numpy/reference/generated/numpy.record.html 

        FITS rec can be accessed with 
            FITS_rec[col_name][point_idx_list]  ! Much faster !
            FITS_rec[point_idx_list][col_name]

        but NOT with
            FITS_rec[point_idx_list][col_list]
            FITS_rec[col_list][point_idx_list]
            FITS_rec[[col_list]][point_idx_list]
            FITS_rec[*col_list][point_idx_list]
            FITS_rec[**col_list][point_idx_list]
            FITS_rec[[*col_list]][point_idx_list]
            
            FITS_rec[col_tuple][point_idx_list]
            FITS_rec[[col_tuple]][point_idx_list]
            FITS_rec[*col_tuple][point_idx_list]
            FITS_rec[[*col_tuple]][point_idx_list]
            FITS_rec[col_name][point_idx_list]
            
            FITS_rec[col_list, point_idx_list]
            FITS_rec[point_idx_list, col_list]
    """
    print("  Getting {} points".format(sample_size))
    print(axis_name_list)
    # 0. Setup
    sufficient_data = False
    current_length = 0
    slice_count = 0
    # A) Criteria Based Slicing
    if criteria_dict:
        # 1. Pre-Allocate Memory
        selected_data = {
            axis_name:np.empty(sample_size, dtype=brick_data_types[axis_name])
            for axis_name in axis_name_list
        }
        # 2. Oversample by 1/brick_use.  e.g. 5% brick_use: (1/0.05 = 20)*sample_size
        next_sample_size = int(round(sample_size/brick_use))
        # 3. Ensure enough data
        while not sufficient_data: 
            # 3.1 Get random sample
            select_points = get_sample_indices(next_sample_size, brick_size)
            # 3.2 Get Data
            new_data = slice_data(
                brick_data.data[select_points],
                criteria_dict,
                axis_name_list)
            data_size = min(sample_size-current_length, min(sample_size, len(new_data[axis_name_list[0]])))
            print("  new slice (got/wanted/queried): {:,}/{:,}/{:,}".format(
                len(new_data[axis_name_list[0]]), 
                sample_size,
                int(round(sample_size/brick_use))))
            # 3.3 Assign data
            for axis_name in axis_name_list:
                selected_data[axis_name][current_length:current_length+data_size] = new_data[axis_name][0:data_size]
            current_length += data_size
            slice_count += 1
            # 3.4 Check for sufficienct
            if current_length >= sample_size:
                sufficient_data = True  
            # TODO: Better handling for this
            # 3.5 Limit Cycles
            if slice_count > max_fill_attempts:
                sufficient_data = True
                # Cut to how much data we got
                for axis_name in axis_name_list:
                    selected_data[axis_name] = selected_data[axis_name][0:current_length]
            # 3.6 Adjust next Iteration
            # Vaguely analogous to iteratively approaching distribution
            # TODO: Set maximum number of sample to be used for memory usage
            #if not sufficient_data:
            #    sample_use = data_size/next_sample_size  # Fraction received
            #    # Oversample by fraction received previously
            #    next_sample_size = np.min([
            #        int(round(sample_size/sample_use)),
            #        brick_size,
            #        settings['max_sample_size']
            #    ])
    # B) Simple
    else:
        # 2. Sample
        select_points = get_sample_indices(sample_size, brick_size)
        # 3. Get & Assign data
        selected_data = reduce_cols(brick_data.data[select_points], axis_name_list)
    # Return data
    return selected_data

####################################################################################


####################################################################################
#   Unpacking Data
####################################################################################

def extract_common_subset(string_one, string_two):
    """ extract the common subset of strings, lists, arrays, etc. """
    idx = 0
    for i in range(min(len(string_one), len(string_two))):
        if string_one[i] == string_two[i]:
            idx += 1
        else:
            break
    return string_one[:i], string_one[i:], string_two[i:]

def extract_common_subwords(string_one, string_two):
    """ only cut by words """
    string_list_one = string_one.split(" ")
    string_list_two = string_two.split(" ")
    common, sub_string_one, sub_string_two = extract_common_subset(string_list_one, string_list_two)
    return " ".join(common), " ".join(sub_string_one), " ".join(sub_string_two)

def format_two_columns(binding, column_one, column_two, bracketed=False):
    """ format two columns together """
    common, string_one, string_two = extract_common_subwords(
            column_one.replace("_", " "), 
            column_two.replace("_", " ")
    )
    if bracketed:
        if common:
            common += ' '
        return '{}[{} {} {}]'.format(common, string_one, binding, string_two)
    else:
        if common:
            common += ':  '
        return '{}{} {} {}'.format(common, string_one, binding, string_two)

def get_axis_data(data, axis_one_name, axis_operator='', axis_two_name=''):
    """ return the adjusted axis and formatted name """
    if (not axis_one_name):
        return '', np.array([])
    elif (not axis_operator) or (not axis_two_name):
        return axis_one_name.replace("_", " "), data[axis_one_name]
    else:
        if axis_operator == '+':
            ret_axis_name = format_two_columns("+", axis_one_name, axis_two_name, bracketed=True)
            return ret_axis_name, (data[axis_one_name] + data[axis_two_name])
        elif axis_operator == '-':
            ret_axis_name = format_two_columns("-", axis_one_name, axis_two_name, bracketed=True)
            return ret_axis_name, (data[axis_one_name] - data[axis_two_name])
        elif axis_operator == '/':
            ret_axis_name = format_two_columns("/", axis_one_name, axis_two_name, bracketed=True)
            return ret_axis_name, (data[axis_one_name] / data[axis_two_name])
        elif axis_operator == 'x':
            ret_axis_name = format_two_columns("$\times$", axis_one_name, axis_two_name, bracketed=True)
            return ret_axis_name, (data[axis_one_name] * data[axis_two_name])

####################################################################################


# Process Data
def adjust_axis_type(axis_type, axis_name, axis_data):
    """ adjust arrays by type """
    if axis_type == 'e^()':
        np.exp(axis_data, out=axis_data)
        axis_name = 'e^({})'.format(axis_name)
    elif axis_type == '10^()':
        np.power(axis_data, 10, out=axis_data)
        axis_name = '10^({})'.format(axis_name)
    elif axis_type == 'Ln()':
        np.log(axis_data, out=axis_data)
        axis_name = 'Ln({})'.format(axis_name)
    elif axis_type == 'Log10()':
        np.log10(axis_data, out=axis_data)
        axis_name = 'Log10({})'.format(axis_name)
    return axis_type, axis_name, axis_data

####################################################################################
#   Slicing Data
####################################################################################
def get_limits(bricks_selected, limit_dict, brick_column_details):
    """ Return limits which are smaller than the brick limits """
    if limit_dict:
        brick_limits = {
            col_name:[ 
                np.min([brick_column_details[brick][col_name]['min'] 
                        for brick in bricks_selected]),
                np.max([brick_column_details[brick][col_name]['max'] 
                        for brick in bricks_selected])
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
    """ Return dict of brick usage {brick_name:fractional_usage} """
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
                brick_interval_size = (brick_column_details[brick][col_name]['max']
                                      -brick_column_details[brick][col_name]['min'])
                brick_col_usage.append(
                    intersection_size/brick_interval_size
                )     
            brick_usage[brick] = np.product(brick_col_usage)           
    else:
        brick_usage = {brick:1 for brick in bricks_selected}
    return brick_usage

def get_relevant_bricks(bricks_selected, criteria_dict, brick_column_details, min_usage):
    """ Return brick list that is above criteria """
    # Adjust for Brick usage: Only use above min, oversample proportionally, etc.
    brick_usage = get_brick_usage(bricks_selected, criteria_dict, brick_column_details)
    print("    brick_usage: ", brick_usage)
    bricks_selected = [
        brick for brick in bricks_selected 
        if brick_usage[brick] > min_usage
    ]
    return bricks_selected

def reduce_cols(data, axis_name_list, selection=0):
    """ Slice named array by axis name list """
    # TODO: testing other implementation
    t1 = time.time()
    if type(selection) != int:
        selection = {
            axis_name:data[axis_name][selection]
            for axis_name in axis_name_list
        }
    else:
        selection = {
            axis_name:data[axis_name]
            for axis_name in axis_name_list
        }
    t2 = time.time()
    print("    reduce: {:.2f}s".format(t2-t1))
    # Test:  Requires ColumnDef, and does implicit copy too just into a rec_array
    #     data.from_columns(axis_name_list, nrows=len(data))
    # Test:  ValueError: could not convert string to float: 'PHAT J....' (since np.empty has 1 type rather than multiple)
    #selection = np.empty((len(data), len(axis_name_list)))
    #for i, axis_name in enumerate(axis_name_list):
    #    selection[:,i] = data[axis_name]
    return selection

#@jit(nopython=True, parallel=True)
def get_within_limits(data, col_name, limits):
    """ Return boolean array, where elements are within limits """
    return np.logical_and(
        data[col_name] > limits[0], 
        data[col_name] < limits[1]
    )

def slice_data(data, criteria_dict, axis_name_list=[], list_comp=True):
    """ Return sliced data as dictionary
    
    given named array, slice it according to (min,max) defined in criteria,
    return dictionary of subarrays
    """
    # Pass in Data reference
    #t1 = time.time()
    #data = data.data
    #print("accessing time: {:.2f}s".format(time.time()-t1))
    # Bulk slicing
    if list_comp:
        t1 = time.time()
        selection = np.all(
            [get_within_limits(data, col_name, limits)
                for col_name, limits in criteria_dict.items()],
            0)
        t2 = time.time()
        print("    list comprehension: {:.2f}s".format(t2-t1))
    # Individual slicing for more efficient computation
    else:
        t1 = time.time()
        selection = np.array([])#np.ones(data.data.shape[0], dtype=bool)
        # TODO: Order by smallest fraction first to reduce Trues
        for col_name, limits in criteria_dict.items():
            if selection.shape[0] < 2:
                selection = get_within_limits(data, col_name, limits)
            else:
                np.logical_and(selection, get_within_limits(data, col_name, limits), out=selection)
        t2 = time.time()
        print("    cycle {:.2f}s".format(t2-t1))
    return reduce_cols(data, axis_name_list, selection)

####################################################################################
# No longer used...

def get_slice_idx(data, axis_name_list, criteria_dict):
    """ Return sliced, given criteria {'column_name':(min, max)} """
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
    """ Return sliced, given criteria {'column_name':(min, max)} """
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
