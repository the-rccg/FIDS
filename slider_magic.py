# -*- coding: utf-8 -*-
import math
import numpy as np
import dash_core_components as dcc
import dash_html_components as html

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

def get_range_slider(column_name, id_given, col_range, marks=None, granularity=1000, certainty=2):
    """ create a proper styled range slider """
    if not marks:
        marks = get_marks(col_range, certainty=certainty) #{i:'{}'.format(i) for i in [col_range[0], col_range[1]]}
    slider = dcc.RangeSlider(
        id = id_given,
        min = col_range[0],
        max = col_range[1],
        value = col_range,
        marks = marks,
        step = (col_range[1]-col_range[0])/granularity
    )
    title = html.Div('{}'.format(column_name), style={'margin': '0   0 -5px 10px'})
    return html.Div([title, html.Div(slider, style = {'margin': '0px 0  15px 0'})])

def get_marks(col_range, certainty=2, include_zero=False):
    """ get proper formatting for marks """
    sig_digits = get_sig_digits(col_range, certainty)
    sig_digit_formatter = "{}".format(sig_digits)
    marks = {
        parse_datatype(val):str(("{:#."+sig_digit_formatter+"g}").format(val))
        for val in col_range
    }
    if include_zero and col_range[0] < 0 and col_range[1] > 0:
        marks[0] = '0.0'
    # TODO: Fix showing of zero label. Maybe value it differently form zero??
    #if col_range[0] == 0:
    #    marks[0] = '0.00'
    # TODO: Fix overflow of box by aligning. Currently leads to disappearing labels. (fix div width?)
    #marks[col_range[0]]  = {'label':marks[col_range[0]],  'style':{'text-align':'center'}}
    #marks[col_range[-1]] = {'label':marks[col_range[-1]], 'style':{'text-align':'center'}}
    return marks

def get_sig_digits(col_range, certainty):
    """ given tuple and certainty, return number of significant digits necessary to differntiate between the two numbers """
    sig_digit = round(abs(np.log10(1-np.min(np.abs(col_range))/np.max(np.abs(col_range)))))+certainty
    if not np.isfinite(sig_digit):
        print(col_range)
        sig_digit=0
    sig_digit = int(max(sig_digit, certainty))
    return sig_digit

def parse_datatype(value):
    """ parse numpy datatypes to python standard for JSON serialization """
    if type(value) in [np.int64, np.int32]:
        return int(value)
    elif type(value) in [np.float64, np.float32]:
        return float(value)
    elif type(value) in [np.bool_]:
        return bool(value)
    else:
        return value