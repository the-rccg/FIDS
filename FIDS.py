# -*- coding: utf-8 -*-
"""
FITS Dash App
Quickly sketch and explore data tables and relations sae in FITS format 

Line-length:  84 (since thats VSCode on 1080 vertical)

@author: RCCG
"""
import numpy as np
import json
from pprint import pprint
from memory_profiler import profile

# Load Settings
settings = json.load(open('settings.json'))
debug = settings['debug']
if debug:
    print("---- Running in Debug-Mode ----")
    host = '127.0.0.1'
    port = '5001'
    enable_login = False
else:
    host = settings['host']
    port = settings['port']
    enable_login = settings['enable_login']

# File names
# TODO: Allow dictionary for renaming in display
from os import listdir
filename_list = sorted([file for file in listdir(settings['folderpath']) 
                             if  file[-5:].lower()==".fits"])

# Load Data
from astropy.io import fits
# TODO: Allow dictionary for renaming in display

def dict_of_files(filename_list):
    return {
        filename: fits.open(settings['folderpath'] + filename, memmap=True)[1] 
        for filename in filename_list
    }
data = dict_of_files(filename_list)

# Defining columns
# TODO: Allow dictionary for renaming in dispaly
# TODO: Read or allow import of UNITS. Maybe visual initialization as an app?
column_names_file = sorted(settings['columns_to_use'])
column_names_data = sorted(data[filename_list[0]].columns.names)
def get_column_names(filename_list, column_names_file, column_names_data):
    if column_names_file:
        column_names = [
            column_name for column_name in column_names_file 
                if column_name in column_names_data
        ]
    else:
        column_names = sorted(data[filename_list[0]].columns.names)
    return column_names
column_names = get_column_names(filename_list, column_names_file, column_names_data)

# Draw Params
display_count_max = settings['display_count_max']
display_count = settings['display_count_default']
display_count_step = settings['display_count_granularity']

# Default Parameters: No Default

# Subsample when data is too large
def get_data_counts(data):
    return {filename: data[filename].header['NAXIS2'] for filename in data.keys()}
data_counts = get_data_counts(data)  # Header is fastest way to get number of data points

# Reduce Columns to Useful
selected_columns = column_names
selected_columns.remove(settings['name_column']) #[name for name in column_names if name.split('_')[-1] not in ['p50', 'p84', 'p16', 'Exp']]
#print("Selected Columns: {}".format(selected_columns))


import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go


####################################################################################
# Columns: Use, Slice, etc.
####################################################################################

# Getting dtypes
from io_tools import parse_datatype
# Add column criteria selection
def map_types(dictionary):
    """ NOTE: The following give DIFFERENT types
    data.data[col_name].dtype       -- read as NumPy array (desired)  e.g. >f8, <U100
    dict(data.columns.dtype.descr)  -- fastest to get (raw storaoge)  e.g. <f8, |S100
    data.data.columns.dtype.fields  -- Python dtype                   e.g. float64, S100
    dict(data.data.dtype.descr))    -- ???                            e.g. >f8, |S100
    """
    for key in dictionary.keys():
        if dictionary[key][0] == "<":
            dictionary[key] = ">"+dictionary[key][1:]
        if dictionary[key][0] == "|":
            dictionary[key] = "<"+dictionary[key][1:]
        if dictionary[key][1] == "S":
            dictionary[key] = dictionary[key][0] + "U" + dictionary[key][2:]
    return dictionary
def get_brick_data_types(data, filename_list):
    # The bad: Load entire array in memory
    #dict(data[filename_list[0]].data.dtype.descr)
    # The good: Load just dtypes of numpy array
    #data[filename_list[0]].columns.dtype.fields
    return dict(data[filename_list[0]].columns.dtype.descr)
brick_data_types = map_types(get_brick_data_types(data, filename_list))
#for col in brick_data_types.keys():
#    if brick_data_types[col][:2] == '|S':
#        brick_data_types[col] = '<U'+brick_data_types[col][2:]
allowed_types = ['>f8', '>i8', '<f8', '<i8']
slice_col_list = [col_name for col_name in column_names if brick_data_types[col_name] in allowed_types][:17]

# Get Brick Details
from io_tools import load_json
brick_column_details = load_json('brick_column_details.json', savepath=settings['savepath'])
# Cut out bricks without computed details
filename_list = [filename for filename in filename_list if filename in brick_column_details.keys()]
column_details = {
    col_name: {
        'min': parse_datatype(np.min([brick_column_details[brick_name][col_name]['min'] for brick_name in filename_list])),
        'max': parse_datatype(np.max([brick_column_details[brick_name][col_name]['max'] for brick_name in filename_list])),
    }
    for col_name in slice_col_list
}
slice_col_list = [col for col in slice_col_list if col in column_details.keys()]
print("Reduced Slice Col List: ", slice_col_list)

# Set up range sliders
from slider_magic import get_range_slider, get_log_range_slider

slider_style = {
    #'height':34, 
    #'width':'97%', 
    #'margin':'0px 0px 0px 0px',  # above right below left
    'padding': '0px 20px 3px 20px', # above right below left
    'width': 'inherit'
}
# List of: DIV( DIV( title ), DIV( slider ) ) 
slice_list = [
    html.Div(
        # TODO: Fix Log Sliders
        # TODO: Automatically recognize who needs log scale
        #get_log_range_slider(
        #    column_name,
        #    column_details,
        #    id_given = '{}'.format(column_name),
        #    granularity = settings['selection_granularity']
        #)
        get_range_slider(
                column_name, 
                id_given='{}'.format(column_name), 
                col_range=[
                    column_details[column_name]['min'], 
                    column_details[column_name]['max']
                ],
                marks=None,
                granularity=settings['selection_granularity'],
                certainty=settings["slider_number_certainty"]
        ),
        id='{}_div'.format(column_name), 
        style={
            **slider_style,
            'display': 'none'
        }
    )
    for column_name in slice_col_list
]
slice_inputs = [
    dash.dependencies.Input('{}'.format(col_name), 'value') 
    for col_name in slice_col_list
]
slice_states = [
    dash.dependencies.State('{}'.format(col_name), 'value') 
    for col_name in slice_col_list
]
####################################################################################

debug_elements = []
if debug:
    debug_elements.append(
        html.Div(
            id='debug-container',
            children=[
                # Status
                html.Div(
                    id = 'debug-status',
                    children = 'debug status'
                ),
                # Shutdown Button
                html.Button(
                    'shutdown app', 
                    id='shutdown-button',
                    className='button-primary', 
                    type='button-primary'
                ),
            ],
            style={'padding': '3px'}
        )
    )
    # style
    debug_elements = [
        html.Div(
            debug_elements,
            style={ 
                'border': 'solid 1px #A2B1C6', 
                'border-radius': '5px', 
                'padding': '5px', 
                'margin-top': '20px', 
            }
        )]


####################################################################################
# DASH Application
####################################################################################
external_stylesheets = ['assets/FIDS.css']

# TODO: Move to external file
external_userbase = [
    ['hello', 'world']
]
dropdown_style = {
    'padding': '3px'
}

def add_explanation(obj, title=""):
    """ Wrap a DCC object with an explanation on mouse-over """
    # Inherit "title" from child
    if not title:
        try:
            title = obj.placeholder
        except:
            title = "??"
    # Inherit "style" from child
    try:
        base_style = obj.style
    except:
        base_style = {}
    return html.Abbr(obj, title=title, style={**base_style, 'border': 'none', 'text-decoration': 'none'})

def Dropdown(*args, **kwargs):
    """ wrap all Dropdowns with an explanation """
    return add_explanation(dcc.Dropdown(*args, **kwargs))

def create_formatter(axis_naming, axis_title, column_list):
    """ Return collapsable formatting div """
    # TODO: Move to table from float/inline-block
    return html.Details(
                id='{}-formatting'.format(axis_naming),
                children=[
                    # 1: Summary
                    html.Summary(
                        '{} Formatting'.format(axis_title),
                        style={
                            'font-size': '14px',
                            'color': '#444',
                            'padding': '0px 0px 0px 5px'
                        }
                    ),
                    # 2: Wrapper for Axis Adjustments
                    html.Div(
                        [
                            # 2.1: Linear vs. Log vs. Exp
                            html.Div(
                                Dropdown(
                                    placeholder='Axis scaling',
                                    id='{}-type'.format(axis_naming),
                                    options=[
                                        {'label': i, 'value': i} 
                                            for i in ['Linear', 'Log Scale', 'Ln()', 'Log10()', 'e^()', '10^()']
                                    ],
                                    value='Linear'
                                ), 
                                style={
                                    'width': '49%', 
                                    'display': 'inline-block'
                                }
                            ),
                            # 2.2: Increasing vs. Decreasing
                            html.Div(
                                Dropdown(
                                    placeholder='Axis orientation',
                                    id='{}-orientation'.format(axis_naming),
                                    options=[
                                        {'label': i, 'value': i} 
                                            for i in ['increasing', 'decreasing']
                                    ],
                                    value='increasing',
                                ),
                                style={
                                    'float': 'right',
                                    'width': '49%',
                                    'display': 'inline-block',
                                }
                            ),
                            # 2.3: Combined plotting
                            # Alternatively, pop in after selecting first column on axis?
                            html.Div(
                                [
                                    # 2.3.1: Operator
                                    html.Div(
                                        Dropdown(
                                            placeholder='Operator',
                                            id='{}-operator'.format(axis_naming),
                                            options=[
                                                {'label':i, 'value':i}
                                                    for i in ['+', '-', '/', 'x']
                                            ],
                                            value=''
                                        ),
                                        style={
                                            'width': '70px',
                                            'display': 'table-cell',
                                            'vertical-align': 'top'
                                        }
                                    ),
                                    # 2.3.2: 2nd Column
                                    html.Div(
                                        Dropdown(
                                            placeholder='Column',
                                            id='{}-combined-column'.format(axis_naming),
                                            options=[
                                                {'label': i, 'value': i} 
                                                    for i in column_list
                                            ],
                                            value=''
                                        ),
                                        style={
                                            'display': 'table-cell',
                                            'width': 'auto',
                                            'vertical-align': 'top',
                                            'padding': '0px 0px 0px 5px'
                                        }
                                    )
                                ],
                                style={
                                    'display': 'table', 
                                    'width':'100%'
                                }
                            )
                        ],
                        style={
                            'padding': '0px 0px 0px 15px',
                        }
                    )
                ],
                style={
                    'display': 'none'
                }
            )

app = dash.Dash(settings['name'], external_stylesheets=external_stylesheets)
# Use Local Script and CSS
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Allow Login User:Password
if not settings['debug']:
    auth = dash_auth.BasicAuth(
        app,
        external_userbase
    )

app.title = 'FITS Dashboard: {}'.format(settings['name'])

# Visual layout
# TODO: Move "style"-img into CSS
app.layout = html.Div([
    html.Div([
        
        # Element 1: Data File Selector
        html.Div(
            Dropdown(
                id='brick_selector',
                placeholder='Select FITS files...',
                options=[
                    {'label': '{}'.format(i), 'value': i} 
                        for i in filename_list
                ],
                multi=True
            ),
            style=dropdown_style 
        ),

        # Element 2: Data Amount Selector
        html.Div(
            dcc.Slider(
                id='display_count_selection',
                #placeholder='',
                min=0,
                max=display_count_max,
                value=display_count,
                step=display_count_step,
                marks={
                    0: '0', 
                    display_count_max: "{:,}".format(display_count_max)
                }
            ),
            style={**slider_style, 'height':'34px'}
            #html.Div(id="selection-container")
        ),

        # Element 3: New Subsample Generator
        # To Be Coded
            
        # Element 4: Axes selections, orientation, type
        # Axis Selection
        html.Div(
            [
                # 4.1: Select X-Axis
                html.Div(
                    [
                        # 4.1.1: X-Axis Column
                        Dropdown(
                            id='xaxis_column',
                            placeholder='Select X-Axis...',
                            options=[
                                {'label': i, 'value': i} 
                                    for i in selected_columns
                            ],
                            value=settings['default_x_column']
                        ),
                        # 4.1.2 X-Axis Formatting
                        # TODO: Align heights between float (Y), and block (X)
                        create_formatter('xaxis', 'X-Axis', selected_columns),
                    ],
                    style={
                        'width': '49.5%', 
                        #'float': 'left',
                        'display': 'inline-block'
                    }
                ),
                # 4.2: Select Y-Axis
                html.Div(
                    [
                        # 4.2.1 Y-Axis Column
                        Dropdown(
                            id='yaxis_column',
                            placeholder='Select Y-Axis...',
                            options=[
                                {'label': i, 'value': i} 
                                    for i in selected_columns
                            ],
                            value=settings['default_y_column']
                        ),
                        # 4.2.2 Y-Axis Formatting
                        create_formatter('yaxis', 'Y-Axis', selected_columns),
                    ],
                    style={
                        'width': '49.5%', 
                        'float': 'right', 
                        'display': 'inline-block'
                    }
                ),
                # 4.3: Select Z-Axis ?
                # TODO: 3D Graphing
            ],
            style=dropdown_style
        ),
                        
        # Element 5: Color coding
        html.Div(
            [
                # 5.1 Color Column
                Dropdown(
                    id='caxis_column',
                    placeholder='Select Color-Axis...',
                    options=[
                        {'label': i, 'value': i} 
                            for i in selected_columns
                    ],
                    value=settings['default_color_column']
                ),
                # 5.2 Color-Axis Formatting
                create_formatter('caxis', 'Color-Axis', selected_columns),
            ],
            style=dropdown_style
        ),
                
        # Element 6: Size coding
        html.Div(
            [
                Dropdown(
                    id='saxis_column',
                    placeholder='Select Size-Axis...',
                    options=[
                        {'label': i, 'value': i} 
                            for i in selected_columns
                    ],
                ),
                # TODO: Scaling sizes
            ],
            style=dropdown_style 
        ),

        # Element 7: Add column slice sliders
        html.Div(
            [
                Dropdown(
                    id='column_slicer',
                    placeholder='Select fields to slice on...',
                    options=[
                        {'label': '{}'.format(col_name), 'value': col_name} 
                            for col_name in slice_col_list
                    ],
                    multi=True
                )
            ],
            style=dropdown_style
        ),

        # Element 7.1: Sliders
        *slice_list,

        
        # Graph 1: Scatter Plot
        html.Div(
            dcc.Loading(
                dcc.Graph(
                    id='indicator-graphic',
                    config={
                        #'responsive':True,  # Whether layout size changes with window size
                        #'showLink':True,  # Link bottom right to plotly chartstudio
                        #'sendData':True,  # Send Data to plotly chartstudio
                        #'editable':True,  # Allow editing of title, axis name, etc.
                        'modeBarButtonsToRemove': ['watermark', 'displaylogo'],
                        'displaylogo': False,  # Display plotly logo?
                        'showTips': True,
                        'toImageButtonOptions':{
                            'format': 'svg',
                            'filename': 'image_FIDS'
                        }
                    },
                    style={
                        'responsive': 'true',
                        'height': 'inherit', 
                        'width': 'inherit'
                    }
                ),
                style={
                    #'border': 'solid 1px #A2B1C6', 
                    #'border-radius': '0px', 
                    'padding': '3px', 
                    'width': 'inherit',
                    'height': 'inherit',
                    #'resize': 'vertical',
                    #'overflow': 'auto'
                    #'margin-top': '20px'
                }
            ),
            style={
                'width': 'inherit', 
                'height': 'inherit'
            }
        ),

        # Element 8: Download Section
        html.Details([
            # 8.1 Collapsable Header
            html.Summary(
                'Download Data', 
                style={'padding': '0px 0px 0px 5px'}
            ),  
            # 8.2 Download Section
            html.Div(
                [
                    # 8.2.1: Download Raw File
                    html.Div(
                        [
                            # 8.2.3.1 Description
                            html.Div(
                                'Download entire file:',
                                style={
                                    'padding': '3px 20px 0px 3px',
                                    'font-size': '16px',
                                    'font-weight': 'bold'
                                }
                            ),
                            # 8.2.3.2 File download
                            html.Div([
                                # 8.2.3.1 Select File
                                html.Div(
                                    Dropdown(
                                        id='download_file',
                                        placeholder='Select file to download...',
                                        options=[
                                            {'label': '{}'.format(i), 'value': i} 
                                            for i in filename_list
                                        ],
                                        multi=False,
                                    ),
                                    style={
                                        **dropdown_style,
                                        'display': 'table-cell',
                                        'width': 'auto',
                                    }
                                ),
                                # 8.2.3.1 Download Button
                                html.A(
                                    html.Button(
                                        'Download *ENTIRE FILE*', 
                                        className='button-primary', 
                                        type='button-primary',
                                        id='entire-file-button'
                                    ),
                                    id='download-full-link',
                                    download="rawdata.fits",
                                    href="",
                                    target="_blank",
                                    style={
                                        'padding': '3px',
                                        'display': 'table-cell',
                                        'width': '50px'
                                    }
                                ),
                            ],
                            style={
                                'width': '100%',
                                'display': 'table'
                            })
                        ],
                        style={
                            'margin-top': '5px'
                        }
                    ),
                    # 8.2.2: Download Selected Criteria
                    html.Div( 
                        [
                            # 8.2.4.1 Description
                            html.Div(
                                add_explanation(
                                    'Download all data fitting the criteria:',
                                    title="Download all data points that fall within the criteria of sliders, selection, columns graphed and columns selected additionally"
                                ),
                                style={
                                    'padding': '3px 20px 0px 3px',
                                    'font-size': '16px',
                                    'font-weight': 'bold'
                                }
                            ),
                            # 8.2.4.2 Status Bar
                            html.Div(
                                id='download_column_status',
                                style={
                                    'padding': '0px 0px 0px 3px',
                                    'font-style': 'italic'
                                }
                            ),
                            html.Div([
                                # 8.2.4.3 Column Selector
                                html.Div(
                                    Dropdown(
                                        id='download_columns',
                                        placeholder='Select fields to download...',
                                        options=[
                                            {'label': '{}'.format(col_name), 'value': col_name}
                                                for col_name in column_names
                                        ],
                                        multi=True,
                                    ),
                                    style={
                                        **dropdown_style,
                                        'display': 'table-cell',
                                        'width': 'auto'
                                    }
                                ),
                                # 8.2.3 Download all data in criteria
                                add_explanation(
                                    html.A(
                                        html.Button(
                                            'Download *BY CRITERIA*',
                                            id='criteria_download_button',
                                            className='button-primary', 
                                            type='button-primary',
                                            n_clicks=0
                                        ),
                                        id='download-criteria-link',
                                        #download="within_criteria_data.csv",
                                        href="",
                                        target="_blank",
                                        style={
                                            'padding': '3px',
                                            'display': 'table-cell',
                                            'width': '70px'
                                        }
                                    ),
                                    title="Download all data points that fall within the criteria of sliders, selection, columns graphed and columns selected additionally"
                                )
                            ],
                            style={
                                'display': 'table',
                                'width': '100%'
                            }),
                        ],
                        style={
                            #'padding': '0px 5px 0px 0px',
                            'margin-top': '5px'
                        }
                    )
                ],
                style={
                    'border': 'solid 1px #A2B1C6',
                    'border-radius': '5px',
                    'padding': '5px',
                    #'width': '100%'
                }
            ),
        ]),

        # Element 9: Debug Tools
        *debug_elements,

    ], 
    style = { 
        'border': 'solid 1px #A2B1C6', 
        'border-radius': '5px', 
        'padding': '5px', 
        #'margin-top': '20px', 
        'flex': '1 0 auto'
    }),

    # Element 11: Footer with links
    html.Div(
        html.H6(
            [
                # 11.1 Link to FIDS
                html.A(
                    'FIDS: Flexible Imaging and Display System, ',
                    id='repository_link',
                    href='https://www.github.com/the-rccg/FIDS',
                    target='_blank',
                    style={
                        'color': '#444',#rgb(116, 101, 130)',
                        'text-decoration': 'none',
                        'letter-spacing': '0.03em'
                    }
                ),
                # 11.2 Link to University
                html.A(
                    'provided by Ruprecht-Karls Universitaet Heidelberg',
                    id='university_link',
                    href='https://www.uni-heidelberg.de/',
                    target='_blank',
                    style={
                        'color': '#444',#'rgb(116, 101, 130)',
                        'text-decoration': 'none',
                        'letter-spacing': '0.03em'
                    }
                )
            ],
            style={
                'font-size': '14px', 
                'padding': '5px'
            }
        ), 
        className='footer', 
        style={'flex-shrink': '0'}
    ),
    #html.Footer('test',style={'flex-shrink': '0'})
])

####################################################################################
# Debug Elements
####################################################################################
from flask import request

if debug:
    @app.callback(
        dash.dependencies.Output('debug-status', 'children'),
        [dash.dependencies.Input('shutdown-button', 'n_clicks')]
    )
    def shutdown(action):
        #import sys
        #sys.exit(0)
        if action:
            if action > 1:
                func = request.environ.get('werkzeug.server.shutdown')
                if func is None:
                    raise RuntimeError('Not running with the Werkzeug Server')
                func()
                ret_str = "shutting down...." #'/dash/shutdown'
            else:
                ret_str = "please confirm"
        else:
            ret_str = "debug status"
        return ret_str


def hide_unhide_div(truth_statement, base_style={}, debug=False, show='block'):
    """ Return style with display if true """
    if truth_statement or debug:
        return {**base_style, 'display':show}
    else:
        return {**base_style, 'display':'none'}

####################################################################################
# Get Selection
####################################################################################
from polygon_selection import get_data_in_polygon
import urllib
import pandas as pd

from data_selector import get_limits, reduce_cols, slice_data, get_relevant_bricks, get_brick_usage
from datetime import datetime as dt

from flask import session


def args_to_criteria(bricks_selected, args):
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

def update_status(status, variable, text, formats=["[ ]", "[x]"]):
    """ NOTE: ugly. div does not allow: \n, linesep, <br> """
    if type(status) != list:
        status = list(status)
    if variable:
        return [*status, html.Div('{} {}: {}'.format(formats[1], text, variable))]
    else: 
        return [*status, html.Div('{} No {}'.format(formats[0], text))]


from urllib.parse import urlencode
@app.callback(
    [
        dash.dependencies.Output('download-criteria-link', 'href'),
        dash.dependencies.Output('download_column_status', 'children')
    ],
    [
        dash.dependencies.Input('criteria_download_button', 'n_clicks')
    ],
    [
        dash.dependencies.State('indicator-graphic', 'selectedData'),
        dash.dependencies.State('xaxis_column', 'value'),
        dash.dependencies.State('yaxis_column', 'value'),
        dash.dependencies.State('caxis_column', 'value'),
        dash.dependencies.State('saxis_column', 'value'),
        dash.dependencies.State('xaxis-combined-column', 'value'),
        dash.dependencies.State('yaxis-combined-column', 'value'),
        dash.dependencies.State('caxis-combined-column', 'value'),
        dash.dependencies.State('xaxis-operator', 'value'),
        dash.dependencies.State('yaxis-operator', 'value'),
        dash.dependencies.State('xaxis-combined-column', 'value'),
        dash.dependencies.State('yaxis-combined-column', 'value'),
        dash.dependencies.State('brick_selector', 'value'),
        dash.dependencies.State('download_columns', 'value'),
        *slice_states
    ]
)
def params_to_link(n_clicks, selected_data, xaxis_name, yaxis_name, caxis_name, saxis_name,
                   xaxis_two_name, yaxis_two_name, caxis_two_name,
                   xaxis_operator, yaxis_operator, 
                   xaxis_second_name, yaxis_second_name,
                   bricks_selected, download_columns, *args):
    # Check:  No click
    if (not n_clicks):
        return [None, None]
    # Setup:  Pre-pack variables
    parameters = locals()
    # Setup:  Remove unnecessary variables
    del parameters['selected_data']
    del parameters['args']
    # Setup:  Status
    status = [html.Div('Status: ')]
    status = update_status(status, bricks_selected, "Bricks Selected")
    # Check:  No Brick
    if (not bricks_selected):
        return [None, status]
    # Setup:  Axes to include
    axis_name_list = reduced_axis_list(
        download_columns, xaxis_name, yaxis_name, caxis_name, saxis_name, 
        xaxis_two_name, yaxis_two_name, caxis_two_name
    )
    parameters['axis_name_list'] = axis_name_list
    status = update_status(status, axis_name_list, "Columns to Download Selected")
    # Check:  No axis
    if len(axis_name_list) == 0:
        return [None, status]
    # Otherwise Go Ahead-->
    t0 = dt.now()
    # Setup:  Include Slider Criteria
    criteria_dict = args_to_criteria(bricks_selected, args)
    status = update_status(status, criteria_dict, "Criteria Specified", formats=["-","-"])
    # Selection Adjustments
    vertices = []
    if selected_data:
        # Option 1: Rectangle
        if 'range' in selected_data.keys():
            # Step 1.1: Update Criteria
            x_interval = selected_data['range']['x']
            y_interval = selected_data['range']['y']
            if xaxis_name in criteria_dict.keys():
                criteria_dict[xaxis_name] = update_interval(
                    criteria_dict, xaxis_name, 
                    np.min(x_interval), np.max(x_interval)
                )
            if yaxis_name in criteria_dict.keys():
                criteria_dict[yaxis_name] = update_interval(
                    criteria_dict, yaxis_name, 
                    np.min(y_interval), np.max(y_interval)
                )
            status = update_status(status, [x_interval, y_interval], "Rectangle Selected", formats=["-","-"])
        # Option 2: Curve
        if 'lassoPoints' in selected_data.keys():
            # Step 2.1: Create array of vertices
            vertices = np.array(list(zip(selected_data['lassoPoints']['x'], selected_data['lassoPoints']['y'])))
            # Step 2.2: Update Criteria
            xmin, ymin = vertices.min(0)
            xmax, ymax = vertices.max(0)
            if xaxis_name in criteria_dict.keys():
                criteria_dict[xaxis_name] = update_interval(
                    criteria_dict, xaxis_name, 
                    xmin, xmax
                )
            if yaxis_name in criteria_dict.keys():
                criteria_dict[yaxis_name] = update_interval(
                    criteria_dict, yaxis_name,
                    ymin, ymax
                )
            status = update_status(status, vertices.shape[0], "Lasso Vertices Selected", formats=["-","-"])
    # Pack criteria
    parameters['vertices'] = vertices
    parameters['criteria_dict'] = criteria_dict
    if n_clicks > 2:
        return ['/dash/selected_download.csv?'+urlencode(parameters), status]
    else:
        return ['', 'Please confirm by pressing the button again!']


from flask import Response, send_file
from download import generate_df, generate_tmp, generate_small_file, unpack_vars

@app.server.route('/dash/selected_download.csv') 
def download_selection():
    """ Serve download of defined data """
    # TODO: Not working with combined axes
    # Unpack arguments - TODO: use proper decoding
    variables = unpack_vars(request.args.to_dict()) #urllib.parse.parse_qs(str(request.query_string))
    # TODO: Fix the 1 click delayed update
    #print(int(variables['n_clicks']), int(variables['n_clicks'])%2)
    #if int(variables['n_clicks'])%2:
    #    return ""
    # Repack to types and nested types
    # Get relevant data based on criteria
    return_data = get_all_data(
        variables['bricks_selected'], 
        variables['axis_name_list'], 
        variables['criteria_dict'], 
        brick_column_details, 
        brick_data_types, 
        data
    )
    # Cut to vertices
    if len(variables['vertices']):
        # Step 2.4: Reduce data to selection polygon
        t1 = dt.now()

        return_data = get_data_in_polygon(
            variables['xaxis_name'], variables['yaxis_name'], 
            variables['vertices'], return_data
        )
        print("  polygon slicing: {}".format(dt.now()-t1))
    # Inspect sizes:  size(CSV_string) ~ 2.725*size(return_data)
    return_size_mb = np.sum([return_data[key].nbytes for key in return_data.keys()])/1024/1024
    # Send small files as one
    if return_size_mb < settings['stream_min_size_mb']:
        return send_file(generate_small_file(return_data, return_size_mb),
                         mimetype='text/csv',
                         attachment_filename='selected_criteria_data.csv',
                         as_attachment=True,
                         cache_timeout=0)
    # Asynchronous Streaming of Large Files
    else:
        print("  Raw Size:  {:,.2f} mb".format(
            return_size_mb
        ))
        return Response(generate_tmp(return_data, settings['stream_chunk_size_mb']), mimetype='text/csv')
    # Catch nothing
    return


####################################################################################
# Allow Downloading Entire Brick
####################################################################################
from os.path import isfile
@app.callback(
    [
        dash.dependencies.Output('download-full-link', 'href'),
        dash.dependencies.Output('download-full-link', 'download')
    ],
    [dash.dependencies.Input('download_file', 'value')]
)
def update_download_link(file_list):
    """ Return link to download multiple raw files """
    if not file_list or file_list == "None":
        return [None, None]
    if type(file_list) != list:
        file_list = [file_list]
    return [
        '/dash/download?{}'.format(urlencode({'file_list':file_list})), 
        file_list[0]
    ]

@app.server.route('/dash/download') 
def download_file():
    """ Retrieve filename and send to client via flask """
    args = unpack_vars(request.args.to_dict())
    file_list = args['file_list']
    if type(file_list) != list:
        file_list = [file_list]
    print("download: ", file_list)
    filepath_list = [settings['folderpath'] + filename for filename in file_list]
    # TODO: Allow downloading of multiple files
    filepath = filepath_list[0]
    filename = file_list[0]
    print("{}: {}".format(filename, filepath))
    return send_file(filepath,
                #mimetype='text/csv',
                attachment_filename=filename,
                as_attachment=True,
                cache_timeout=0)
####################################################################################




####################################################################################
#   Get Data 
####################################################################################
from data_selector import get_all_data, get_sample_data, get_subsetdata
####################################################################################


####################################################################################
#   Sliders 
####################################################################################
from slider_magic import get_marks

output_list = [
    dash.dependencies.Output('{}_div'.format(column_name), 'style')
    for column_name in slice_col_list
]
@app.callback(
        output_list,
        [dash.dependencies.Input('column_slicer', 'value')]
        )
def hide_unhide_sliders(criteria_show_list):
    """ Return Div.styles to hide and unhide divs """
    if not criteria_show_list:
        criteria_show_list = []
    # Show if column is selected, otherwise hide
    style_dict = {
        '{}_div'.format(column_name):hide_unhide_div(
            (column_name in criteria_show_list), 
            base_style=slider_style
        ) 
        for column_name in slice_col_list
    }
    return list(style_dict.values())

@app.callback(
    [
        dash.dependencies.Output('{}'.format(col_name), 'min') 
        for col_name in slice_col_list
    ] + [
        dash.dependencies.Output('{}'.format(col_name), 'max') 
        for col_name in slice_col_list
    ] + [
        dash.dependencies.Output('{}'.format(col_name), 'marks') 
        for col_name in slice_col_list
    ],
    [dash.dependencies.Input('brick_selector', 'value')]
)
def update_slice_limits(bricks_selected):
    """ Update limits on sliders depending on bricks selected """
    #print("update_slice_limits")
    if bricks_selected:
        mins = [
            # Min
            parse_datatype(np.min([brick_column_details[brick_name][col_name]['min'] for brick_name in bricks_selected]))
            for col_name in slice_col_list
        ] 
        maxs = [
            # Max
            parse_datatype(np.max([brick_column_details[brick_name][col_name]['max'] for brick_name in bricks_selected]))
            for col_name in slice_col_list
        ]
        # Marks
        marks = [
            get_marks(np.array([mins[idx], maxs[idx]]))
            for idx in range(len(mins))
        ]
        reduced_limits = mins + maxs + marks
    else:
        reduced_limits = [
            # Min
            parse_datatype(column_details[col_name]['min'])
            for col_name in slice_col_list
        ] + [
            # Max
            parse_datatype(column_details[col_name]['max'])
            for col_name in slice_col_list
        ]        
        # Marks
        reduced_limits += [
            get_marks(
                np.array([
                    reduced_limits[idx], 
                    reduced_limits[idx+int(len(reduced_limits)/2)]
                ])
            )
            for idx in range(int(len(reduced_limits)/2))
        ]
    #print('slice_limits: ', reduced_limits)
    return reduced_limits

@app.callback(
    [
        dash.dependencies.Output('{}_title'.format(col_name), 'children') 
        for col_name in slice_col_list
    ],
    [
        *slice_inputs
    ],
    [   
        dash.dependencies.State('brick_selector', 'value')
    ]
)
def update_slider_titles(*args):
    """ Update titles with limit values if applicable """
    # TODO: Handle arguments nicer than this hack
    bricks_selected = args[-1]
    args = args[:-1]
    criteria = args_to_criteria(bricks_selected, args)
    pprint(criteria)
    # TODO: Rewrite this more efficient
    new_titles = []
    for slider_col_name in slice_col_list:
        title = slider_col_name
        if slider_col_name in criteria:
            # TODO: Make significant digits dependent on granularity of slider
            marks = get_marks(
                criteria[slider_col_name],
                certainty=settings["slider_number_certainty"], 
                include_zero=False)
            title = "{}  ({} - {})".format(
                title,
                *marks.values()
            )
        new_titles.append(title)
    return new_titles

####################################################################################


####################################################################################
#   Axis Adjustments
####################################################################################
from data_selector import get_axis_data, format_two_columns, adjust_axis_type

@app.callback(
    [
        dash.dependencies.Output('xaxis-formatting', 'style'),
        dash.dependencies.Output('yaxis-formatting', 'style'),
        dash.dependencies.Output('caxis-formatting', 'style')
    ],
    [
        dash.dependencies.Input('xaxis_column', 'value'),
        dash.dependencies.Input('yaxis_column', 'value'),
        dash.dependencies.Input('caxis_column', 'value')
    ]
)
def unhide_axis_formatter(*args):
    """ return list of styles if name defined """
    return [hide_unhide_div(arg) for arg in args]

def get_axis_properties(axis_column_name, axis_type, axis_orientation):
    return {
        'title': axis_column_name,
        'type': 'log' if axis_type == 'Log Scale' else 'linear',  # TODO: Log base ___???
        'autorange': 'reversed' if axis_orientation == 'decreasing' else True,
        'automargin': True
    }

def scale_max(arr):
    arr[np.isinf(arr)] = 0
    return arr/np.max(arr)

# Define Marker properties
marker_properties = {
    'size': settings['marker_size'],
    'opacity': settings['marker_opacity'],
    'line': {'width': 0.5, 'color': 'white'}
}

update_graph_inputs = [
        dash.dependencies.Input('xaxis_column', 'value'),
        dash.dependencies.Input('yaxis_column', 'value'),
        dash.dependencies.Input('caxis_column', 'value'),
        dash.dependencies.Input('saxis_column',  'value'),
        dash.dependencies.Input('xaxis-type', 'value'),
        dash.dependencies.Input('yaxis-type', 'value'),
        dash.dependencies.Input('caxis-type', 'value'),
        dash.dependencies.Input('xaxis-orientation', 'value'),
        dash.dependencies.Input('yaxis-orientation', 'value'),
        dash.dependencies.Input('caxis-orientation', 'value'),
        dash.dependencies.Input('xaxis-combined-column', 'value'),
        dash.dependencies.Input('yaxis-combined-column', 'value'),
        dash.dependencies.Input('caxis-combined-column', 'value'),
        dash.dependencies.Input('display_count_selection', 'value'),
        dash.dependencies.Input('brick_selector', 'value'),
        *slice_inputs
]

@app.callback(
    dash.dependencies.Output('indicator-graphic', 'figure'),
    update_graph_inputs,
    [
        dash.dependencies.State('xaxis-operator', 'value'),
        dash.dependencies.State('yaxis-operator', 'value'),
        dash.dependencies.State('caxis-operator', 'value')
    ])
def update_graph(xaxis_name, yaxis_name, caxis_name, saxis_name,
                 xaxis_type, yaxis_type, caxis_type,
                 xaxis_orientation, yaxis_orientation, caxis_orientation,
                 xaxis_second_column, yaxis_second_column, caxis_second_column,
                 display_count, bricks_selected, *args):
    """ update graph based on new selected variables """
    #print('args: ', args)
    #print('kwargs: ', kwargs)

    # Extract Operators from args
    xaxis_operator, yaxis_operator, caxis_operator = args[-3], args[-2], args[-1]
    # Extract Criteria from args
    criteria_dict = args_to_criteria(bricks_selected, args[:-3])

    # Brick selection
    print("  Brick {} selected".format(bricks_selected))

    # TODO: Allow more complex column variations
    # Special Functions on columns
    # 1. Herzsprung Russel columns
    # absolut magnitude / luminosity
    # stellar classification / effective temperatures
    #custom_functions =  {}

    # Fill new data
    t0 = dt.now()
    # Check for valid axis
    has_bricks = (type(bricks_selected) is list)
    has_xaxis = (xaxis_name in selected_columns)
    has_yaxis = (yaxis_name in selected_columns)
    has_caxis = (caxis_name in selected_columns)
    has_saxis = (saxis_name in selected_columns)
    # Require X and Y to plot
    if has_bricks and has_xaxis and has_yaxis:
        # Adjust for Brick usage: Only use above min, oversample proportionally, etc.
        bricks_selected = get_relevant_bricks(bricks_selected, criteria_dict, brick_column_details, min_usage=0)
        # Column list
        axis_name_list = reduced_axis_list(
            settings['name_column'],
            xaxis_name, yaxis_name, caxis_name, saxis_name,
            xaxis_second_column, yaxis_second_column, caxis_second_column
        )
        print(axis_name_list)

        # Subsample
        if display_count:    
            return_data = get_sample_data(
                bricks_selected, display_count, axis_name_list, 
                criteria_dict, brick_column_details,
                data, 
                brick_data_types, data_counts, settings)
        # ALL DATA
        else:
            return_data = get_all_data(
                bricks_selected,
                axis_name_list,
                criteria_dict, brick_column_details, brick_data_types,
                data)
        # Unpack
        text_name,  text   = get_axis_data(return_data, settings['name_column'])
        xaxis_name, x_data = get_axis_data(return_data, xaxis_name, xaxis_operator, xaxis_second_column)
        yaxis_name, y_data = get_axis_data(return_data, yaxis_name, yaxis_operator, yaxis_second_column)
        caxis_name, c_data = get_axis_data(return_data, caxis_name, caxis_operator, caxis_second_column)
        saxis_name, s_data = get_axis_data(return_data, saxis_name)

        # Create Title  
        title = format_two_columns('vs.', xaxis_name, yaxis_name)
        
    else:
        x_data = np.array([])
        y_data = np.array([])
        c_data = np.array([])
        text   = np.array([''])
        title  = ''
    t1 = dt.now()
    print("  getting data: {}".format(t1-t0))

    # Axis Adjustments
    xaxis_type, xaxis_name, x_data = adjust_axis_type(xaxis_type, xaxis_name, x_data)
    yaxis_type, yaxis_name, y_data = adjust_axis_type(yaxis_type, yaxis_name, y_data)
    if has_caxis:
        caxis_type, caxis_name, c_data = adjust_axis_type(caxis_type, caxis_name, c_data)

    # Format for sending  
    data_dic = {
        'x': x_data,
        'y': y_data
    }
    # TODO: Add Color and Size labels before "text" as they cannot be included in hoverinfo right now
    # Add color scale
    if has_caxis:
        # Color Scales:  'Greys', 'YlGnBu', 'Greens', 'YlOrRd', 'Bluered', 'RdBu', 'Reds', 'Blues', 'Picnic', 'Rainbow', 'Portland', 'Jet', 'Hot', 'Blackbody', 'Earth', 'Electric', 'Viridis', 'Cividis'
        title += ' colored by {}'.format(caxis_name)
        # Set Color
        marker_properties['color'] = c_data
        if caxis_orientation == 'increasing':
            marker_properties['colorscale'] = settings['color_scale']
        else:
            marker_properties['colorscale'] = settings['inv_color_scale']
        marker_properties['showscale'] = True
        marker_properties['colorbar'] = {'title':caxis_name, 'titleside':'right'}
    else:
        marker_properties['color'] = 1  # Recolor after color axis removed
    if has_saxis:
        # Update Title
        title += ' sized by {}'.format(saxis_name)
        # Set Size
        marker_properties['size'] = scale_max(s_data)*20
    else:
        marker_properties['size'] = settings['marker_size']  # Resize after color axis removed
    # Finish Title
    annotations = []
    if has_bricks:
        # Below title
        title = title + '<br><i>('+', '.join(sorted(bricks_selected))+')<i>'
        # Subtitle Variant with Annotation (NOTE: Not alignable with title)
        #annotations.append({
        #    'text': '<i>('+', '.join(sorted(bricks_selected))+')</i>',
        #    'font': {
        #        'size': 10,
        #        'color': 'rgb(116, 101, 130)',
        #    },
        #    'showarrow': False,
        #    'align': 'center',
        #    'x': 0.5,
        #    'y': 1,
        #    'xref': 'paper',
        #    'yref': 'paper',
        #    'xanchor': 'center',
        #    'yanchor': 'bottom'
        #})

    # Use WebGL for large datasets
    if data_dic['x'].shape[0] > settings["display_count_webgl_min"]:
        print("using go.Scattergl")
        plot_fig = go.Scattergl(
            **data_dic,
            text = text,
            mode = 'markers',
            marker = marker_properties
        )
    # Otherwise stick with standard
    else:
        plot_fig = go.Scatter(
            **data_dic,
            text = text,
            mode = 'markers',
            marker = marker_properties
        )
    print("entire call: {}".format(dt.now()-t0))
    return {'data': [
            plot_fig
        ],
        'layout': go.Layout(
            title=title,
            annotations=annotations,
            xaxis=get_axis_properties(xaxis_name, xaxis_type, xaxis_orientation),
            yaxis=get_axis_properties(yaxis_name, yaxis_type, yaxis_orientation),
            autosize=True,
            margin={'l': 40, 'b': 60, 't': 80, 'r': 0},
            hovermode='closest'
        )
    }


if __name__ == '__main__':
    app.run_server(debug=settings['debug'], host=settings['host'], port=settings['port'])# host='129.206.102.157')