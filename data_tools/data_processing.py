# -*- coding: utf-8 -*-
"""
Helper functions for processing data in FIDS
"""

import numpy as np
from .data_selector import get_limits


def get_column_names(data, filename_list, column_names_file, column_names_data):
    """ Get column names based on column_names_data """
    if column_names_file:
        column_names = [
            column_name for column_name in column_names_file 
                if column_name in column_names_data
        ]
    else:
        column_names = sorted(data[filename_list[0]].columns.names)
    return column_names


def reduced_axis_list(*args):
    """ Return list of used, nun-duplicate columns """
    # Add non-list items
    axis_list = [col for col in args if (col) and type(col)!=list]
    # Add lists 
    for col in args:
        if type(col) == list:
            axis_list += col
    return sorted(list(set(axis_list)))


def update_interval(data, key, min_two, max_two):
    """ Return updated (min, max) """
    if key in data.keys():
        new_min = np.maximum(min_two, data[key][0])
        new_max = np.minimum(max_two, data[key][1])
    else:
        new_min = min_two
        new_max = max_two
    return new_min, new_max


def args_to_criteria(bricks_selected, slice_col_list, brick_column_details, args):
    """ Return dictionary: 'column_name': [min, max] """
    criteria_dict = {}
    if args:
        # NOTE: REMEMBER TO DELOG IF LOG USED
        criteria_dict = {slice_col_list[i]:limits for i, limits in enumerate(args)}
        if bricks_selected and criteria_dict:
            criteria_dict = get_limits(bricks_selected, criteria_dict, brick_column_details)
        else:
            criteria_dict = {}
    return criteria_dict


def from_dict(dictionary, key_list):
    """ Return list of values from dictionary """
    return [dictionary[key] for key in key_list]
