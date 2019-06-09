# -*- coding: utf-8 -*-
import math
import numpy as np
import dash_core_components as dcc
import dash_html_components as html


# Log


def get_log_range(column_min, column_max, log_base=10):
    """ returns the log range as tuple """
    if column_min > 0:
        log_range = (
            math.floor(math.log(column_min, log_base)), 
            math.ceil(math.log(column_min, log_base) 
                + math.log(column_max/column_min, log_base)
            )
        )
    elif column_min < 0:
        log_range = (
            -math.ceil(math.log(-column_min, log_base)), 
            math.ceil(math.log(column_min, log_base))
        )
    else: 
        log_range = (
            0, 
            math.ceil(0+math.log(column_max, log_base)
            )
        )
    return log_range


def construct_log_range(column_name, column_details):
    """ construct slider with log markings adjusting for negatives """
    marks = {'0':0, **{
        (i): '{}'.format(10 ** i) 
        for i in range(*get_log_range(column_name, column_details))
    }}
    return marks    


def get_log_range_slider(column_name, column_details, id_given, marks=None, log_base=10, granularity=1000):
    """ create a log range slider """
    log_range = get_log_range(
        column_details[column_name]['min'], 
        column_details[column_name]['max'], 
        log_base=log_base)
    marks = {i:'{}'.format(log_base**i) for i in range(log_range[0], log_range[1]+1)}
    return get_range_slider(column_name, id_given, log_range, marks=marks, granularity=granularity)


def delog(value):
    """ delog values """
    return 10**np.array(value)


# Creating Range Slider


def get_range_slider(column_name, id_given, col_range, marks=None, granularity=1000, certainty=2):
    """
    create a proper styled range slider
    returns:  title, DIV( slider )
    """
    # Automatically set marks if not defined
    if not marks:
        marks = get_marks(col_range, certainty=certainty) #{i:'{}'.format(i) for i in [col_range[0], col_range[1]]}
    # Create Slider Object
    slider = dcc.RangeSlider(
        id = id_given,
        min = col_range[0],
        max = col_range[1],
        value = col_range,
        marks = marks,
        step = (col_range[1]-col_range[0])/granularity
    )
    # Set Title and position it above it
    title = html.Div(
        '{}'.format(column_name), 
        id = "{}_title".format(id_given),
        style = {'margin': '0   0 -5px 10px'}
    )
    # Create wrapper to allow title
    return title, html.Div(slider, style = {'margin': '0px 0  15px 0'})


# Marks & Significant Digits


def get_marks(col_range, certainty=2, include_zero=0.1):
    """ returns {number:'formatted_number'} with proper formatting for marks 
    
    NOTE: 
    - Slider unable to show with keys of "xxx.0" format 
      (see https://github.com/plotly/dash-core-components/issues/159)
    """
    sig_digits = get_sig_digits(col_range, certainty)
    sig_digit_formatter = "{}".format(sig_digits)
    marks = {
        parse_datatype(val): str(("{:#."+sig_digit_formatter+"g}").format(val))
        for val in col_range
    }
    # Include zero based on percentage distance to each label
    if include_zero \
            and abs(col_range[0])/(col_range[1]-col_range[0]) > include_zero \
            and abs(col_range[1])/(col_range[1]-col_range[0]) > include_zero:
        marks[0] = '0.0'
    # TODO: Fix overflow of box by aligning. Currently leads to disappearing labels. (fix div width?)
    #marks[col_range[0]]  = {'label':marks[col_range[0]],  'style':{'text-align':'center'}}
    #marks[col_range[-1]] = {'label':marks[col_range[-1]], 'style':{'text-align':'center'}}
    return marks


def get_sig_digits(col_range, certainty):
    """
    given tuple and certainty, 
    return number of significant digits necessary to differentiate 
    between the two numbers and add a desired further certainty
    """
    sig_digit = round(abs(np.log10(1-np.min(np.abs(col_range))/np.max(np.abs(col_range)))))+certainty
    if not np.isfinite(sig_digit):
        print(col_range)
        sig_digit=0
    sig_digit = int(max(sig_digit, certainty))
    return sig_digit


def float_cast(value):
    if value.is_integer():
        value = int(value)
    return value


recast_map = {
    int: int,
    np.int64: int,
    np.int32: int,
    float: float_cast,
    np.float64: float_cast,
    np.float32: float_cast,
    bool: bool, 
    np.bool_: bool
}


def parse_datatype(value):
    """ parse numpy datatypes to python standard for JSON serialization """
    return recast_map[type(value)](value)
