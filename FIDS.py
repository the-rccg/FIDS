# -*- coding: utf-8 -*-
"""
FITS Dash App
Quickly sketch and explore data tables and relations sae in FITS format 

@author: RCCG
"""
import numpy as np
import json
from pprint import pprint

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
filename_list = sorted([file for file in listdir(settings['folderpath']) if file[-5:].lower()==".fits"])

# Load Data
from astropy.io import fits
# TODO: Allow dictionary for renaming in display
data = {
            filename: fits.open(settings['folderpath'] + filename, memmap=True)[1] 
            for filename in filename_list
        }

# Defining columns
# TODO: Allow dictionary for renaming in dispaly
column_names_file = sorted(settings['columns_to_use'])
column_names_data = sorted(data[filename_list[0]].columns.names)
if column_names_file:
    column_names = [
        column_name for column_name in column_names_file 
            if column_name in column_names_data
    ]
else:
    column_names = sorted(data[filename_list[0]].columns.names)

# Draw Params
display_count_max = settings['display_count_max']
display_count = settings['display_count_default']
display_count_step = settings['display_count_granularity']

# Default Parameters: No Default

# Subsample when data is too large
data_counts = {filename: data[filename].header['NAXIS2'] for filename in data.keys()}  # Header is fastest way to get number of data points
def getSampleIndices(sample_size, total_size):
    """ returns data points for the subsample in the range

    Timed Tests:   data_count = 100,000,000;  sample_size = 100,000;
        926 us  np.random.randint(low=0, high=data_count+1, size=sample_size) 
        935 us  np.random.choice(data_count, size=sample_size, replace=True, p=None)
         85 ms  random.sample(range(data_count), sample_size)
          6 s   np.random.choice(data_count, size=sample_size, replace=False, p=None)
    """
    # note: allows multiple identical values, hence n<=num_points, but orders mag faster
    select_points = np.random.randint(
                        low=0, high=total_size, 
                        size=sample_size
                    )
    return select_points


# Reduce Columns to Useful
selected_columns = column_names
selected_columns.remove(settings['name_column']) #[name for name in column_names if name.split('_')[-1] not in ['p50', 'p84', 'p16', 'Exp']]
#print("Selected Columns: {}".format(selected_columns))


import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go


##################################################################################
#   Allow range slicing
##################################################################################
from io_tools import parse_datatype
# Add column criteria selection
brick_data_types = dict(data[filename_list[0]].data.dtype.descr)
#pprint(brick_data_types)
allowed_types = ['>f8', '>i8']
slice_col_list = [col_name for col_name in column_names if brick_data_types[col_name] in allowed_types][:17]
#pprint([(col_name, brick_data_types[col_name]) for col_name in column_names if brick_data_types[col_name] in allowed_types][17:21])
#print("Slice Col List: ", slice_col_list)

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

from slider_magic import get_range_slider, get_log_range_slider
from pprint import pprint

slider_style = {
    #'height':34, 
    #'width':'97%', 
    #'margin':'0px 0px 0px 0px',  # above right below left
    'padding': '0px 20px 0px 20px',
    'width': 'inherit'
}
slice_list = [
    html.Div(
        id = '{}_div'.format(column_name), 
        children=[
            #get_log_range_slider(
            #    column_name,
            #    column_details,
            #    id_given = '{}'.format(column_name),
            #    granularity = settings['selection_granularity']
            #)
            get_range_slider(
                column_name, 
                id_given = '{}'.format(column_name), 
                col_range = [
                    column_details[column_name]['min'], 
                    column_details[column_name]['max']
                ], 
                marks=None, 
                granularity=settings['selection_granularity']
            )
        ],
        style={**slider_style,
               'display': None
        }
    )
    for column_name in slice_col_list
]
slice_inputs = [dash.dependencies.Input('{}'.format(col_name), 'value') 
                    for col_name in slice_col_list]
##################################################################################


###############################################################################
# DASH Application
###############################################################################
external_stylesheets = ['assets/FIDS.css']
external_userbase = [
    ['hello', 'world']
]

app = dash.Dash(settings['name'], external_stylesheets=external_stylesheets)
if not settings['debug']:
    auth = dash_auth.BasicAuth(
        app,
        external_userbase
    )

app.title = 'FITS Dashboard: {}'.format(settings['name'])

dropdown_style = {
        'padding': '3px'
}
# Visual layout
app.layout = html.Div([
html.Div([
    
    # Element 1: Data File Selector
    html.Div(
        [
            dcc.Dropdown(
                id='brick_selector',
                placeholder='Select FITS files...',
                options=[
                    {'label': '{}'.format(i), 'value': i} 
                        for i in filename_list
                ],
                value=None,
                multi=True
            )
        ],
        style=dropdown_style 
    ),

    # Element 2: Data Amount Selector
    html.Div(
        [
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
            )
        ],
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
                    #html.H4('x-axis ', style={'display':'inline-block', 'width':60, 'margin': '0 auto', 'float':'left'}),
                    #html.Div([
                        dcc.Dropdown(
                            id='xaxis-column',
                            placeholder='Select X-Axis...',
                            options=[
                                {'label': i, 'value': i} 
                                    for i in selected_columns
                            ],
                            value=settings['default_x_column']
                        ),
                        #],
                        #style={'display':'inline-block', 'margin':'auto auto', 'width':'100%'}),
                    html.Div([
                        dcc.RadioItems(
                            id='xaxis-type',
                            options=[
                                {'label': i, 'value': i} 
                                    for i in ['Linear', 'Log']
                            ],
                            value='Linear',
                            labelStyle={'display': 'inline-block'}
                        )], style={'float': 'left', 'display': 'inline-block'}
                    ),
                    html.Div(
                        [
                            dcc.RadioItems(
                                id='xaxis-orientation',
                                options=[
                                    {'label': i, 'value': i} 
                                        for i in ['increasing', 'reversed']
                                ],
                                value='increasing',
                                labelStyle={'display': 'inline-block'}
                            )
                        ], 
                        style={
                                'float': 'right', 
                                'display': 'inline-block', 
                                'padding': '0px 5px 0px 0px'  # Adjust right alignment
                        }
                    )
                ],
                style={'width': '49%', 'display': 'inline-block'}
            ),
            # 4.2: Select Y-Axis
            html.Div(
                [
                    dcc.Dropdown(
                        id='yaxis-column',
                        placeholder='Select Y-Axis...',
                        options=[
                            {'label': i, 'value': i} 
                                for i in selected_columns
                        ],
                        value=settings['default_y_column']
                    ),
                    html.Div([
                        #html.H6('Scale:', style={'font-size':'12px', 'display':'inline-block', 'width':'50px'}),
                        dcc.RadioItems(
                            id='yaxis-type',
                            options=[
                                {'label': i, 'value': i} 
                                    for i in ['Linear', 'Log']
                            ],
                            value='Linear',
                            labelStyle={'display': 'inline-block'}
                        )], style={'width': '49%', 'display': 'inline-block'}
                    ),
                    html.Div(
                        [
                            dcc.RadioItems(
                                id='yaxis-orientation',
                                options=[
                                    {'label': i, 'value': i} 
                                        for i in ['increasing', 'reversed']
                                ],
                                value='increasing',
                                labelStyle={'display': 'inline-block'}
                            )
                        ], 
                        style={
                                'float': 'right', 
                                'display': 'inline-block', 
                                'padding':'0px 5px 0px 0px'  # Adjust right alignment
                        }
                    )
                ],
                style={'width': '49%', 'float': 'right', 'display': 'inline-block'}
            ),
        ],
        style=dropdown_style 
    ),
                    
    # Element 5: Color coding
    html.Div(
        [
            dcc.Dropdown(
                id='color-column',
                placeholder='Select Color-Axis...',
                options=[
                    {'label': i, 'value': i} 
                        for i in selected_columns
                ],
                value=None
            ),
        ],
        style=dropdown_style 
    ),
            
    # Element 6: Size coding
    html.Div(
        [
            dcc.Dropdown(
                id='size-column',
                placeholder='Select Size-Axis...',
                options=[
                    {'label': i, 'value': i} 
                        for i in selected_columns
                ],
                value=None
            ),
        ],
        style=dropdown_style 
    ),

    # Element 7: Add column slicors
    html.Div(
        [
            dcc.Dropdown(
                id='column_slicer',
                placeholder='Select fields to slice on...',
                options=[
                    {'label': '{}'.format(col_name), 'value': col_name} 
                        for col_name in slice_col_list
                ],
                value=None,
                multi=True
            )
        ],
        style=dropdown_style
    ),

    *slice_list,

    
    # Graph 1: Scatter Plot
    html.Div(
        dcc.Loading(
            dcc.Graph(
                id='indicator-graphic',
                #style={'responsive':'true'},
                config={
                    #'responsive':True,  # Whether layout size changes with window size
                    #'showLink':True,  # Link bottom right to plotly chartstudio
                    #'sendData':True,  # Send Data to plotly chartstudio
                    #'editable':True,  # Allow editing of title, axis name, etc.
                    'modeBarButtonsToRemove':['watermark', 'displaylogo'],
                    'displaylogo':False,  # Display plotly logo?
                    'showTips':True,
                    'toImageButtonOptions':{
                        'format':'svg',
                        'filename':'image_FIDS'
                    }
                }
            ),

            style={
                    #'border': 'solid 1px #A2B1C6', 
                    #'border-radius': '0px', 
                    'padding': '3px', 
                    #'width': '100%',
                    #'height': '100%',
                    #'resize': 'vertical',
                    #'overflow': 'auto'
                    #'margin-top': '20px'
            }
        )
    ),

    # Element 8: Download Selection
    html.A(
        html.Button(
                'Download *SELECTED* Data', 
                className='button-primary'),
        id='download-selection',
        #download="rawdata.fits",
        href="",
        target="_blank",
        style={'padding': '3px 20px 3px 3px'}
    ),

    # Element 9: Download entire brick
    html.A(
        html.Button('Download *CURRENT BRICK*', 
                     className='button-primary', type='button-primary'),
        id='download-full-link',
        download="rawdata.fits",
        href="",
        target="_blank",
        style={'padding': '3px'}
    ),

], 
style = { 
    'border': 'solid 1px #A2B1C6', 
    'border-radius': '5px', 
    'padding': '5px', 
    #'margin-top': '20px', 
    'flex': '1 0 auto'}),
# Element 10: Footer with links
html.Div(
    [
        html.H6(
            'FIDS - Flexible Imaging and Display System, provided by Ruprecht-Karls Universitaet Heidelberg',
            style={'font-size':'14px', 'padding':'5px'}
        )
    ], 
    className='footer', 
    style={'flex-shrink': '0'}
),
#html.Footer('test',style={'flex-shrink': '0'})
])
    

##################################################################################
# Download Selection
##################################################################################
from os import linesep 
import pandas as pd
import urllib.parse

def selected_data_to_csv(selected_data_dict, xaxis_name, yaxis_name, caxis_name, saxis_name):
    if saxis_name:
        print("WARNING SIZE IS ADJUSTED FOR VISUALIZATION!!!")
    points = selected_data_dict['points']
    #print(points)
    num_points = len(points)
    if num_points == 0:
        return ""
    if num_points > 10000:
        print('WARNING large dataset parsing: {}'.format(num_points))
    if not caxis_name and not saxis_name:
        csv_string = "description,{},{}".format(xaxis_name, yaxis_name) + linesep + "{}".format(linesep).join(['{}, {}, {}'.format(point['text'], point['x'], point['y']) for point in points])
    elif not saxis_name:
        csv_string = "description,{},{},{}".format(xaxis_name,yaxis_name,caxis_name) + linesep + "{}".format(linesep).join(['{}, {}, {}, {}'.format(point['text'], point['x'], point['y'], point['marker.color']) for point in points])
    else:
        csv_string = pd.DataFrame(points).to_csv()
    print(csv_string)
    return csv_string

@app.callback(
    dash.dependencies.Output('download-selection', 'href'),
    [
        dash.dependencies.Input('indicator-graphic', 'selectedData'),
        dash.dependencies.Input('xaxis-column', 'value'),
        dash.dependencies.Input('yaxis-column', 'value'),
        dash.dependencies.Input('color-column', 'value'),
        dash.dependencies.Input('size-column', 'value')
    ])
def download_selected(selected_data, xaxis_name, yaxis_name, caxis_name, saxis_name):
    if type(selected_data) == dict:
        return "data:text/csv;charset=utf-8,%EF%BB%BF" + urllib.parse.quote(selected_data_to_csv(selected_data, xaxis_name, yaxis_name, caxis_name, saxis_name), encoding="utf-8")
    else:
        return 
    

##################################################################################
# Allow Downloading Entire Brick
##################################################################################
from os.path import isfile
@app.callback(dash.dependencies.Output('download-full-link', 'href'),
              [dash.dependencies.Input('brick_selector', 'value')])
def update_download_link(file_list):
    '''  '''
    if not file_list or file_list == "None":
        return 
    if type(file_list) is list:
        print(file_list)
        return '/dash/download?value={}'.format(",".join(file_list))
        #file_value = file_value[0]
    filepath = settings['folderpath'] + file_list
    if not isfile(filepath):
        return
    else:
        return '/dash/download?value={}'.format(file_list)

from flask import request, send_file
@app.server.route('/dash/download') 
def download_file():
    filename = request.args.get('value')
    file_list = filename.split(',')
    print("download: ", file_list)
    filepath_list = [settings['folderpath'] + filename for filename in file_list]
    filepath = filepath_list[0]  # TODO: Allow downloading of multiple files
    return send_file(filepath,
                #mimetype='text/csv',
                attachment_filename=filename,
                as_attachment=True)
##################################################################################

output_list = [
    dash.dependencies.Output('{}_div'.format(column_name), 'style')
    for column_name in slice_col_list
]
@app.callback(
        output_list,
        [dash.dependencies.Input('column_slicer', 'value')]
        )
def hide_unhide(criteria_show_list):
    # Hide all
    print("hide_unhide()")
    show_dict = {
        '{}_div'.format(column_name):{**slider_style, 'display': 'none'} 
        for column_name in slice_col_list
    }
    # Show selected
    if criteria_show_list:
        for col_show in criteria_show_list:
            show_dict['{}_div'.format(col_show)] = {**slider_style, 'display': 'block'}
        #print(show_dict)
    return list(show_dict.values())


##################################################################################
#   Getting Data
##################################################################################
#def get_all_data(brick_data, axis_name_list, criteria_dict={}) 
#    return get_data(brick_data, axis_name_list, sample_size=data_counts[brick_name])

def get_data(brick_data, axis_name_list, sample_size=0, brick_size=0, criteria_dict={}, brick_use=1):
    """ 
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
            FITS_rec[col_name][point_idx_list]
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
    print("Getting {} points".format(sample_size))
    print(axis_name_list)
    sufficient_data = False
    #brick_data_types = dict(brick_data.data.dtype.descr)
    selected_data = {}
    if criteria_dict:
        selected_data = {
            axis_name:np.empty(sample_size, dtype=brick_data_types[axis_name])
            for axis_name in axis_name_list
        }
    current_length = 0
    slice_count = 0
    while not sufficient_data:
        # Slicing 
        if criteria_dict:
            # TODO: Better handling for this
            if slice_count > settings['max_fill_attempts']:
                sufficient_data = True
            # Oversample by 1/brick_use.
            select_points = getSampleIndices(int(round(sample_size/brick_use)), brick_size)
            new_data = slice_data(
                brick_data.data[select_points],
                axis_name_list,
                criteria_dict)  
            data_size = min(sample_size-current_length, min(sample_size, len(new_data[axis_name_list[0]])))
            print("new slice: {}/{}".format(len(new_data), int(round(sample_size/brick_use))))
            for axis_name in axis_name_list:
                selected_data[axis_name][current_length:current_length+data_size] = new_data[axis_name][0:data_size]
            current_length += data_size
            slice_count += 1
            # Check for sufficienct
            if current_length >= sample_size:
                sufficient_data = True
        # Simple
        else:
            select_points = getSampleIndices(sample_size, brick_size)
            selected_data = reduce_cols(brick_data.data[select_points], axis_name_list)
            sufficient_data = True
    # Return data
    return selected_data
##################################################################################

from data_selector import get_limits, reduce_cols, slice_data, get_brick_usage

##################################################################################
#   make slicers dynamic
##################################################################################
from slider_magic import get_marks

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
    '''  '''
    print("update_slice_limits")
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
    print('slice_limits: ')
    pprint(reduced_limits)
    return reduced_limits


##################################################################################



def get_axis_properties(axis_column_name, axis_type, axis_orientation):
    return {
        'title': axis_column_name,
        'type': 'linear' if axis_type == 'Linear' else 'log',
        'autorange': 'reversed' if axis_orientation == 'reversed' else True,
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
        dash.dependencies.Input('xaxis-column', 'value'),
        dash.dependencies.Input('yaxis-column', 'value'),
        dash.dependencies.Input('color-column', 'value'),
        dash.dependencies.Input('size-column', 'value'),
        dash.dependencies.Input('xaxis-type', 'value'),
        dash.dependencies.Input('yaxis-type', 'value'),
        dash.dependencies.Input('xaxis-orientation', 'value'),
        dash.dependencies.Input('yaxis-orientation', 'value'),
        dash.dependencies.Input('display_count_selection', 'value'),
        dash.dependencies.Input('brick_selector', 'value'),
        *slice_inputs
]
from datetime import datetime as dt
@app.callback(
    dash.dependencies.Output('indicator-graphic', 'figure'),
    update_graph_inputs)
def update_graph(xaxis_column_name, yaxis_column_name, color_column_name, size_column_name,
                 xaxis_type, yaxis_type, 
                 xaxis_orientation, yaxis_orientation,
                 display_count, bricks_selected, *args, **kwargs
                 ):
    """ update graph based on new selected variables """
    print('args: ', args)
    #print('kwargs: ', kwargs)

    criteria_dict = {}
    if args:
        # NOTE: REMEMBER TO DELOG IF LOG USED
        criteria_dict = {slice_col_list[i]:limits for i, limits in enumerate(args)}
        #print(criteria_dict)
        if bricks_selected and criteria_dict:
            criteria_dict = get_limits(bricks_selected, criteria_dict, brick_column_details)
        else:
            criteria_dict = {}

    # Brick selection
    print("Brick {} selected".format(bricks_selected))

    # Special Functions on columns
    # 1. Herzsprung Russel columns
    # absolut magnitude / luminosity
    # stellar classification / effective temperatures
    #custom_functions =  {}

    # Fill new data
    t0 = dt.now()
    # Check for valid axis
    has_bricks = (type(bricks_selected) is list)
    has_xaxis = (xaxis_column_name in selected_columns)
    has_yaxis = (yaxis_column_name in selected_columns)
    has_caxis = (color_column_name in selected_columns)
    has_saxis = (size_column_name  in selected_columns)
    # Require X and Y to plot
    if has_bricks and has_xaxis and has_yaxis:
        # Create Title
        title = '{} vs. {}'.format(xaxis_column_name, yaxis_column_name)
        
        # Allocate Memory for Data
        x_data = np.empty(display_count)  # X-Axis
        y_data = np.empty(display_count)  # Y-Axis
        if has_caxis:  c_data = np.empty(display_count)  # Color
        else:          c_data = np.array([])
        if has_saxis:  s_data = np.empty(display_count)  # Size
        else:          s_data = np.array([])
        text = np.empty(display_count, dtype=str)  # Description
        t1 = dt.now()
        print("empty:      {}".format(t1-t0))
        # Create new random sample
        print("resampling with {} points".format(display_count))
        
        
        # Adjust for Brick usage: Only use above min, oversample proportionally, etc.
        brick_usage = get_brick_usage(bricks_selected, criteria_dict, brick_column_details)
        print(brick_usage)
        bricks_selected = [
            brick for brick in bricks_selected 
            if brick_usage[brick]>settings['min_brick_usage']]
        brick_count = len(bricks_selected)  # Number of bricks
        # Add Data to Array
        current_length = 0
        for ix, brick_i in enumerate(bricks_selected):
            sample_size = round(display_count/brick_count)
            # Fix uneven split by rounding, then fill remainder: introduces a skew in data
            if ix == brick_count-1 and brick_count%2 == 1:
                sample_size = int(display_count-current_length)
                print("adjustment done: {}".format(sample_size))
            #select_points = getSampleIndices(sample_size, data_counts[brick_i])
            #print("random:     {}".format(dt.now()-t1))
            axis_name_list = [settings['name_column'], xaxis_column_name, yaxis_column_name]
            if has_caxis:  axis_name_list.append(color_column_name)
            if has_saxis:  axis_name_list.append(size_column_name)
            selected_data = get_data(
                    data[brick_i],#.data, 
                    axis_name_list, 
                    sample_size=sample_size, 
                    brick_size=data_counts[brick_i],
                    criteria_dict=criteria_dict,
                    brick_use=brick_usage[brick_i])
            print("slice data: {}".format(dt.now()-t1))
            x_data[current_length:current_length+sample_size] = selected_data[xaxis_column_name]
            y_data[current_length:current_length+sample_size] = selected_data[yaxis_column_name]
            if has_caxis:  
                c_data[current_length:current_length+sample_size] = selected_data[color_column_name]
            if has_saxis:  
                s_data[current_length:current_length+sample_size] = selected_data[size_column_name]
            text[current_length:current_length+sample_size] = selected_data[settings['name_column']]
            print("assign {}:  {}".format(brick_i, dt.now()-t1))
            current_length += sample_size
            t1 = dt.now()
        print(current_length)
    else:
        x_data = np.array([])
        y_data = np.array([])
        c_data = np.array([])
        text   = np.array([''])
        title  = ''
        

    # Format for sending  
    data_dic = {
        'x': x_data,
        'y': y_data
    }
    # Add color scale
    if has_caxis:
        # Update Title
        title += ' colored by {}'.format(color_column_name)
        # Set Color
        marker_properties['color'] = c_data  
        marker_properties['colorscale'] = settings['color_scale']  # 'Greys', 'YlGnBu', 'Greens', 'YlOrRd', 'Bluered', 'RdBu', 'Reds', 'Blues', 'Picnic', 'Rainbow', 'Portland', 'Jet', 'Hot', 'Blackbody', 'Earth', 'Electric', 'Viridis', 'Cividis'
        marker_properties['showscale'] = True
        marker_properties['colorbar'] = {'title':color_column_name}
    if has_saxis:
        # Update Title
        title += ' sized by {}'.format(size_column_name)
        # Set Size
        marker_properties['size'] = scale_max(s_data)*20
    # Finish Title
    if has_bricks:
        title += '<br><i>('+', '.join(sorted(bricks_selected))+')</i>'

    if display_count > settings["display_count_webgl_min"]:
        print("using go.Scattergl")
        plot_fig = go.Scattergl(
            **data_dic,
            text = text,
            mode = 'markers',
            marker = marker_properties
        )
    else:
        plot_fig = go.Scatter(
            **data_dic,
            text = text,
            mode = 'markers',
            marker = marker_properties
        )

    return {'data': [
            plot_fig
        ],
        'layout': go.Layout(
            title=title,
            xaxis=get_axis_properties(xaxis_column_name, xaxis_type, xaxis_orientation),
            yaxis=get_axis_properties(yaxis_column_name, yaxis_type, yaxis_orientation),
            autosize=True,
            margin={'l': 40, 'b': 60, 't': 80, 'r': 0},
            hovermode='closest'
        )
    }



app.scripts.config.serve_locally = True

if __name__ == '__main__':
    app.run_server(debug=settings['debug'], host=settings['host'], port=settings['port'])# host='129.206.102.157')