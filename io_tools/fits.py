# -*- coding: utf-8 -*-

"""
FITS Functions for IO.
"""

from astropy.io import fits


def get_fitstable_data(filenamepath, memmap=True):
    """ Return FITS DataTable from file.

    FITS Tables are normally located at [1]
    """
    try:
        return fits.open(filenamepath, memmap=memmap)[1]
    except:
        return fits.open(filenamepath, memmap=memmap)[0]


def get_data_counts_fits(data):
    """ Header is fastest way to get number of data points. """
    return {
        filename: data[filename].header['NAXIS2']
        for filename in data.keys()
    }


def get_brick_data_types_fits(data, filename_list):
    """ Return dict of column data types.
    The bad:    Load entire array in memory
                dict(data[filename_list[0]].data.dtype.descr)
    The good:   Load just dtypes of numpy array
                data[filename_list[0]].columns.dtype.fields
    """
    return dict(data[filename_list[0]].columns.dtype.descr)
