# -*- coding: utf-8 -*-
"""
Tools for processing files to get relevant meta information for setting up FIDS.
"""
from pprint import pprint
from io_tools import save_json, load_json, parse_datatype, get_brick_data_types
from tqdm import tqdm


def get_missing_column_dict(brick_name_list, brick_column_details, column_list):
    """ Return dict of lists showing missing columns for each key. """
    # Get missing_columns for each file
    missing_column_dict = {}
    for brick_name in brick_name_list:
        # Add all columns
        if brick_name not in brick_column_details.keys():
            missing_column_dict[brick_name] = column_list
        # Check individually
        else:
            missing_column_dict[brick_name] = [
                column
                for column in column_list
                if (column not in brick_column_details[brick_name])
            ]
            missing_column_dict[brick_name] += [
                column
                for column in brick_column_details[brick_name]
                if ('max' not in brick_column_details[brick_name][column] \
                    or 'min' not in brick_column_details[brick_name][column]) \
                    and (column in column_list)
            ]
        if not len(missing_column_dict[brick_name]):
            del missing_column_dict[brick_name]
    pprint(missing_column_dict)
    return missing_column_dict


def get_missing_brick_info(data, brick_column_details, missing_column_dict, savepath):
    """ Get missing minimum, maximum for brick_column_details. """
    # Compute all columns missing for each brick
    added_info = False
    # Loop over Files
    for brick_name in missing_column_dict.keys():
        print(brick_name)
        # Add it not present already
        if brick_name not in brick_column_details.keys():
            brick_column_details[brick_name] = {}
        # Loop over Columns
        for col_name in tqdm(missing_column_dict[brick_name]):
            brick_column_details[brick_name][col_name] = {}
            try:
                minimum = data[brick_name].data[col_name].min()
                brick_column_details[brick_name][col_name]['min'] = parse_datatype(minimum)
                added_info = True
            except Exception as e:
                print(brick_name, e)
            try:
                maximum = data[brick_name].data[col_name].max()
                brick_column_details[brick_name][col_name]['max'] = parse_datatype(maximum)
                added_info = True
            except Exception as e:
                print(brick_name, e)
        # Save updates from file
        if added_info:
            save_json(brick_column_details, 'brick_column_details.json', savepath=savepath)
            added_info = False
    # Save at end just in case
    if added_info:
        save_json(brick_column_details, 'brick_column_details.json', savepath=savepath)
    return brick_column_details


def prepare_brick_info(data, brick_column_details, brick_name_list, column_list, savepath,
                       acceptable_types=['>f8', '>f4', '>i8', '>i4']):
    """ Return full brick column details, updates where necessary. """
    if not brick_column_details.keys():
        print("Setting up dataset...")
    # Setup types
    brick_data_types = get_brick_data_types(data, list(data.keys()), ftype='')
    acceptable_col_list = [
        col_name
        for col_name in column_list
        if brick_data_types[col_name] in acceptable_types
    ]
    # Determine exactly what is missing
    missing_column_dict = get_missing_column_dict(
        brick_name_list, brick_column_details, acceptable_col_list
    )
    # Update when necessary
    if missing_column_dict:
        print(missing_column_dict)
        brick_column_details = get_missing_brick_info(
            data, brick_column_details, missing_column_dict, savepath
        )
    return brick_column_details
