# -*- coding: utf-8 -*-
""" FIDS

Dashboard to interactively visualize and slice FITS datafiles
Quickly sketch and explore data tables and relations sae in FITS format

Line-length:  84 (since thats VSCode on 1080 vertical)

@author: RCCG
"""
# General
import numpy as np
import pandas as pd
import json
from pprint import pprint
from datetime import datetime as dt
from memory_profiler import profile
# IO
from io_tools import get_valid_filelist, get_dict_of_files, get_data_counts, get_brick_data_types
from io_tools import parse_datatype, map_types
from io_tools import load_json
from os.path import isfile
# Processing
from data_tools import get_column_names, reduced_axis_list, args_to_criteria, update_interval
# Data
from data_tools import get_all_data, get_sample_data, get_subsetdata
from data_tools import get_limits, reduce_cols, slice_data, get_relevant_bricks
from data_tools import get_axis_data, format_two_columns, adjust_axis_type
# Polygon
from data_tools import get_data_in_polygon, get_data_in_selection
# Sliders
from setup_dataset import prepare_brick_info
from slider_magic import get_marks, get_range_slider, get_log_range_slider
# Download
from download import generate_df, generate_tmp, generate_small_file, unpack_vars
# Div
from div_updating import hide_unhide_div, update_status
# Dash
import dash
from dash.dependencies import Input, Output, State
import dash_auth
import plotly.graph_objs as go
# Components
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
# Web (Flask, etc.)
from flask import request, session, Response, send_file
import urllib
from urllib.parse import urlencode


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
filename_list = get_valid_filelist(settings['folderpath'], settings['filetypes'])

# Load Data
# TODO: Allow dictionary for renaming in display
# TODO: Allow other data types
# TODO: Allow heterogeneous data
data = get_dict_of_files(filename_list, settings['folderpath'])

# Get File Descriptions
data_counts = get_data_counts(data, ftype=settings['filetypes'][0])
# Defining columns
# TODO: Read or allow import of UNITS. Maybe visual initialization as an app?
column_names_file = sorted(settings['columns_to_use'])
column_names_data = sorted(data[filename_list[0]].columns.names)
column_names = get_column_names(data, filename_list, column_names_file, column_names_data)
# Reduce Columns to Useful
selected_columns = column_names
selected_columns.remove(settings['name_column']) #[name for name in column_names if name.split('_')[-1] not in ['p50', 'p84', 'p16', 'Exp']]

# Draw Params
display_count_max = settings['display_count_max']
display_count = settings['display_count_default']
display_count_step = settings['display_count_granularity']


####################################################################################
# Columns: Use, Slice, etc.
####################################################################################

# Slider Columns = Selected Columns with proper dtype
brick_data_types = map_types(get_brick_data_types(data, filename_list))
allowed_types = settings["allowed_slider_dtypes"]
slice_col_list = sorted([
    col_name for col_name in column_names
    if brick_data_types[col_name] in allowed_types
][:settings["max_slider_count"]])

# Get Brick Details
brick_column_details = load_json('brick_column_details.json', savepath=settings['savepath'])

# Fill in missing data if necessary
brick_column_details = prepare_brick_info(
    data, brick_column_details, filename_list, slice_col_list,
    settings['savepath'], acceptable_types=settings['allowed_slider_dtypes']
)

# Cut out bricks with computed details
filename_list = [
    filename for filename in filename_list
    if filename in brick_column_details.keys()
]
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
slider_style = {
    'padding': '0px 20px 3px 20px', # above right below left
    'width': 'inherit'
}
# List of: DIV( DIV( title ), DIV( slider ) )
# TODO: Fix Log Sliders
# TODO: Automatically recognize who needs log scale
slice_list = [
    html.Div(
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
    Input('{}'.format(col_name), 'value')
    for col_name in slice_col_list
]
slice_states = [
    State('{}'.format(col_name), 'value')
    for col_name in slice_col_list
]
####################################################################################

# Show only one file if only one present
fileselector_kwargs = {}
if len(filename_list) == 1:
    fileselector_kwargs = {
        'value': filename_list[0],
        'disabled': True
    }


debug_elements = []
if debug:
    debug_elements.append(
        html.Div(
            id='debug-container',
            children=[
                # Status
                html.Div(
                    id='debug-status',
                    children='debug status'
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
external_stylesheets = [dbc.themes.BOOTSTRAP, 'assets/FIDS.css']

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
    """ Wrap all Dropdowns with an explanation """
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
                                                {'label': i, 'value': i}
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
                                    'width': '100%'
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
# TODO: Move "style" into CSS
# TODO: Move to CSS Grid from mix of Float and Table
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
                multi=True,
                **fileselector_kwargs
            ), 
            style=dropdown_style
        ),

        # Element 2: Data Amount Selector
        # TODO: Display sample size somewhere
        html.Div(
            dcc.Slider(
                id='display_count_selection',
                min=0,
                max=display_count_max,
                value=display_count,
                step=display_count_step,
                marks={
                    0: '0',
                    display_count_max: "{:,}".format(display_count_max)
                }
            ),
            style={**slider_style, 'height': '34px'}
            #html.Div(id="selection-container")
        ),

        # Element 3: New Subsample Generator
        # TODO

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
                        'display': 'inline-block'
                    }
                ),

                # TODO: Allow switching X <-> Y

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

        # TODO: Graph Styling Section
        # Set min/max point size
        # Set colorscale

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
                            # 8.2.3.2 Status
                            html.Div(
                                id='download_file_status',
                                style={
                                    'padding': '0px 0px 0px 3px',
                                    'font-style': 'italic'
                                }
                            ),
                            # 8.2.3.3 File download
                            html.Div(
                                [
                                    # 8.2.3.3.1 Select File
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
                                    # 8.2.3.3.2 Download Button
                                    html.A(
                                        html.Button(
                                            'Download *ENTIRE FILE*',
                                            className='button-primary',
                                            type='button-primary',
                                            id='entire-file-button',
                                            n_clicks=0
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
                                }
                            ) 
                        ],
                        style={
                            'margin-top': '5px'
                        }
                    ),
                    # 8.2.2: Download Selected Criteria
                    html.Div(
                        [
                            # 8.2.2.1 Description
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
                            # 8.2.2.2 Status Bar
                            html.Div(
                                id='download_column_status',
                                style={
                                    'padding': '0px 0px 0px 3px',
                                    'font-style': 'italic'
                                }
                            ),
                            # 8.2.2.3 Selection
                            html.Div([
                                # 8.2.2.3.1 Column Selector
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
                                # 8.2.2.3.2 Download all data in criteria
                                # Download
                                add_explanation(
                                    #html.A(
                                    html.Div(
                                        html.Button(
                                            'Download *BY CRITERIA*',
                                            id='criteria_download_button',
                                            className='button-primary',
                                            type='button-primary',
                                            n_clicks=0
                                        ),
                                    #    id='download-criteria-link',
                                    #    href="",
                                    #    target="_blank",
                                        style={
                                            'padding': '3px',
                                            'display': 'table-cell',
                                            'width': '70px'
                                        }
                                    ),
                                    title="Download all data points that fall within the criteria of sliders, selection, columns graphed and columns selected additionally"
                                ),
                                dbc.Modal(
                                    [
                                        dbc.ModalHeader("Confirm Download"),
                                        dbc.ModalBody(
                                            "Confirm below to download",
                                            id='download-modal-body'
                                        ),
                                        dbc.ModalFooter(
                                            [
                                                html.A(
                                                    dbc.Button(
                                                        "Download", 
                                                        id="download-modal-button", 
                                                        className="button-primary"
                                                    ),
                                                    id='download-criteria-link',
                                                    href="",
                                                    target="_blank"
                                                ),
                                                dbc.Button(
                                                    "Close", 
                                                    id="download-modal-close", 
                                                    className="button"
                                                )
                                            ]
                                        ),
                                    ],
                                    id="download-modal",
                                ),
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
], style={'padding': '5px'})

####################################################################################
# Debug Elements
####################################################################################
if debug:
    @app.callback(
        Output('debug-status', 'children'),
        [Input('shutdown-button', 'n_clicks')]
    )
    def shutdown(action):
        """ shut down flask server via werkzeug """
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


####################################################################################
# Get Selection
####################################################################################
@app.callback(
    Output("download-modal", "is_open"),
    [
        Input("criteria_download_button", "n_clicks"),
        Input("download-modal-close", "n_clicks"),
        Input("download-criteria-link", "href")
    ],
    [
        State("download-modal", "is_open")
    ],
)
def toggle_modal(n1, n2, n3, is_open):
    if n3:
        if (n1 or n2):
            return not is_open
        return is_open 
    else: 
        return False

@app.callback(
    [
        Output('download-criteria-link', 'href'),
        Output('download_column_status', 'children'),
        Output('download-modal-body', 'children')
    ],
    [
        Input('criteria_download_button', 'n_clicks')
    ],
    [
        State('indicator-graphic', 'selectedData'),
        State('xaxis_column', 'value'),
        State('yaxis_column', 'value'),
        State('caxis_column', 'value'),
        State('saxis_column', 'value'),
        State('xaxis-type', 'value'),
        State('yaxis-type', 'value'),
        State('xaxis-combined-column', 'value'),
        State('yaxis-combined-column', 'value'),
        State('caxis-combined-column', 'value'),
        State('xaxis-operator', 'value'),
        State('yaxis-operator', 'value'),
        State('xaxis-combined-column', 'value'),
        State('yaxis-combined-column', 'value'),
        State('brick_selector', 'value'),
        State('download_columns', 'value'),
        *slice_states
    ]
)
def params_to_link(n_clicks, selected_data,
                   xaxis_name, yaxis_name, caxis_name, saxis_name,
                   xaxis_type, yaxis_type, #caxis_type, saxis_type,
                   xaxis_two_name, yaxis_two_name, caxis_two_name,
                   xaxis_operator, yaxis_operator,
                   xaxis_second_name, yaxis_second_name,
                   bricks_selected, download_columns, 
                   *args):
    """ Update status and link for downloading by encoding all criteria into the URL. """
    # Check:  No click
    if (not n_clicks):
        return [None, None, None]
    # Setup:  Pre-pack variables
    parameters = locals()
    # Setup:  Remove unnecessary variables
    del parameters['selected_data']  # Too big as it incldues every single point displayed
    del parameters['args']  # Relevant re-added with proper names for encoding
    # Setup:  Status
    status = [html.Div('Status: ')]
    status = update_status(status, bricks_selected, "Bricks Selected")
    # Check:  No Brick
    if (not bricks_selected):
        status[0] = html.Div('Status: Failed.')
        return [None, status, status]
    # Setup:  Axes to include
    axis_name_list = reduced_axis_list(
        download_columns, xaxis_name, yaxis_name, caxis_name, saxis_name,
        xaxis_two_name, yaxis_two_name, caxis_two_name
    )
    parameters['axis_name_list'] = axis_name_list
    status = update_status(status, axis_name_list, "Columns to Download Selected")
    # Check:  No axis
    if len(axis_name_list) == 0:
        status[0] = html.Div('Status: Failed.')
        return [None, status, status]
    # Otherwise Go Ahead-->
    status[0] = html.Div('Status: Please confirm by clicking "Download" below!')
    t0 = dt.now()
    # Setup:  Include Slider Criteria
    criteria_dict = args_to_criteria(bricks_selected, slice_col_list, brick_column_details, args)
    status = update_status(status, criteria_dict, "Criteria Specified", formats=["-","-"])
    # Check for combined axis
    is_xaxis_combined = (xaxis_two_name) and (xaxis_operator)
    is_yaxis_combined = (yaxis_two_name) and (yaxis_operator)
    # Selection Adjustments
    vertices = []
    if selected_data:
        # Option 1: Rectangle
        if ('range' in selected_data.keys()):
            # Step 1.1: Update Criteria
            x_interval = selected_data['range']['x']
            y_interval = selected_data['range']['y']
            if (xaxis_name in criteria_dict.keys()) and (not is_xaxis_combined):
                criteria_dict[xaxis_name] = update_interval(
                    criteria_dict, xaxis_name,
                    np.min(x_interval), np.max(x_interval)
                )
            if (yaxis_name in criteria_dict.keys() )and (not is_yaxis_combined):
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
            if (xaxis_name in criteria_dict.keys()) and (not is_xaxis_combined):
                criteria_dict[xaxis_name] = update_interval(
                    criteria_dict, xaxis_name,
                    xmin, xmax
                )
            if (yaxis_name in criteria_dict.keys()) and (not is_yaxis_combined):
                criteria_dict[yaxis_name] = update_interval(
                    criteria_dict, yaxis_name,
                    ymin, ymax
                )
            status = update_status(status, vertices.shape[0], "Lasso Vertices Selected", formats=["-","-"])
    # Pack criteria
    parameters['vertices'] = vertices
    parameters['criteria_dict'] = criteria_dict
    # Require confirmation
    if not(n_clicks % 2) and (n_clicks!=1):
        return ["", status, status]
    else:
        return [
            '/dash/selected_download.csv?'+urlencode(parameters), 
            status,
            status
        ]


@app.server.route('/dash/selected_download.csv')
def download_selection():
    """Serve download of defined data.

    TODO:
    - Fix the delay between updating URL and clicking the download link

    """
    # Unpack arguments - TODO: use proper decoding
    # Repack to types and nested types
    variables = unpack_vars(request.args.to_dict()) #urllib.parse.parse_qs(str(request.query_string))
    # 1. Get relevant data based on slice criteria
    return_data = get_all_data(
        variables['bricks_selected'],
        variables['axis_name_list'],
        variables['criteria_dict'],
        brick_column_details,
        brick_data_types,
        data
    )
    # 2. Cut to visual selection
    if len(variables['vertices']):
        # Reduce data to selection polygon
        t1 = dt.now()
        return_data = get_data_in_selection(
            variables['xaxis_name'], variables['yaxis_name'], variables['vertices'],
            return_data, variables['axis_name_list'],
            xaxis_type=variables['xaxis_type'], yaxis_type=variables['yaxis_two_name'],
            xaxis_two_name=variables['xaxis_two_name'], xaxis_operator=variables['xaxis_operator'],
            yaxis_two_name=variables['yaxis_two_name'], yaxis_operator=variables['yaxis_operator']
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
@app.callback(
    [
        Output('download-full-link', 'href'),
        Output('download-full-link', 'download')
    ],
    [
        Input('download_file', 'value')
    ]
)
def update_download_link(file_list):
    """ Return link to download multiple raw files. """
    if not file_list or file_list == "None":
        return [None, None]
    if type(file_list) != list:
        file_list = [file_list]
    return [
        '/dash/download?{}'.format(urlencode({'file_list':file_list})),
        file_list[0]
    ]

@app.callback(
    Output('download_file_status', 'children'),
    [Input('entire-file-button', 'n_clicks')],
    [State('download_file', 'value')]
)
def update_download_status(n_clicks, file_list):
    """ Update Status for downloading entire file. """
    if not n_clicks:
        return None
    else:
        if not file_list or file_list == "None":
            return "Status: Failed. No file selected."
        if type(file_list) != list:
            file_list = [file_list]
        return "Selected: {}".format(file_list[0])


@app.server.route('/dash/download')
def download_file():
    """ Retrieve filename and send to client via flask. """
    #pprint(request.args.to_dict())
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
#   Sliders
####################################################################################
output_list = [
    Output('{}_div'.format(column_name), 'style')
    for column_name in slice_col_list
]
@app.callback(
    output_list,
    [Input('column_slicer', 'value')]
)
def hide_unhide_sliders(criteria_show_list):
    """ Return Div.styles to hide and unhide divs. """
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
        Output('{}'.format(col_name), 'min')
        for col_name in slice_col_list
    ] + [
        Output('{}'.format(col_name), 'max')
        for col_name in slice_col_list
    ] + [
        Output('{}'.format(col_name), 'marks')
        for col_name in slice_col_list
    ],
    [Input('brick_selector', 'value')]
)
def update_slice_limits(bricks_selected):
    """ Update limits on sliders depending on bricks selected. """
    if bricks_selected:
        # Min
        mins = [
            parse_datatype(
                np.min([
                    brick_column_details[brick_name][col_name]['min']
                    for brick_name in bricks_selected
                ])
            )
            for col_name in slice_col_list
        ]
        # Max
        maxs = [
            parse_datatype(
                np.max([
                    brick_column_details[brick_name][col_name]['max']
                    for brick_name in bricks_selected
                ]
            ))
            for col_name in slice_col_list
        ]
        # Marks
        marks = [
            get_marks(np.array([mins[idx], maxs[idx]]))
            for idx in range(len(slice_col_list))
        ]
    else:
        # Min
        mins = [
            parse_datatype(column_details[col_name]['min'])
            for col_name in slice_col_list
        ]
        # Max
        maxs = [
            parse_datatype(column_details[col_name]['max'])
            for col_name in slice_col_list
        ]
        # Marks
        marks = [
            get_marks(np.array([mins[idx], maxs[idx]]))
            for idx in range(len(slice_col_list))
        ]
    reduced_limits = mins + maxs + marks
    return reduced_limits

@app.callback(
    [
        Output('{}_title'.format(col_name), 'children')
        for col_name in slice_col_list
    ],
    [
        *slice_inputs
    ],
    [
        State('brick_selector', 'value')
    ]
)
def update_slider_titles(*args):
    """ Update titles with limit values if applicable. """
    # TODO: Handle arguments nicer than this hack
    bricks_selected = args[-1]
    args = args[:-1]
    criteria = args_to_criteria(bricks_selected, slice_col_list, brick_column_details, args)
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

@app.callback(
    [
        Output('xaxis-formatting', 'style'),
        Output('yaxis-formatting', 'style'),
        Output('caxis-formatting', 'style')
    ],
    [
        Input('xaxis_column', 'value'),
        Input('yaxis_column', 'value'),
        Input('caxis_column', 'value')
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
        Input('xaxis_column', 'value'),
        Input('yaxis_column', 'value'),
        Input('caxis_column', 'value'),
        Input('saxis_column',  'value'),
        Input('xaxis-type', 'value'),
        Input('yaxis-type', 'value'),
        Input('caxis-type', 'value'),
        Input('xaxis-orientation', 'value'),
        Input('yaxis-orientation', 'value'),
        Input('caxis-orientation', 'value'),
        Input('xaxis-combined-column', 'value'),
        Input('yaxis-combined-column', 'value'),
        Input('caxis-combined-column', 'value'),
        Input('display_count_selection', 'value'),
        Input('brick_selector', 'value'),
        *slice_inputs
]

@app.callback(
    Output('indicator-graphic', 'figure'),
    update_graph_inputs,
    [
        State('xaxis-operator', 'value'),
        State('yaxis-operator', 'value'),
        State('caxis-operator', 'value')
    ])
def update_graph(xaxis_name, yaxis_name, caxis_name, saxis_name,
                 xaxis_type, yaxis_type, caxis_type,
                 xaxis_orientation, yaxis_orientation, caxis_orientation,
                 xaxis_second_column, yaxis_second_column, caxis_second_column,
                 display_count, bricks_selected, *args):
    """ Update graph based on new selected variables. """
    #print('args: ', args)
    #print('kwargs: ', kwargs)

    # Extract Operators from args
    xaxis_operator, yaxis_operator, caxis_operator = args[-3], args[-2], args[-1]
    # Extract Criteria from args
    criteria_dict = args_to_criteria(bricks_selected, slice_col_list, brick_column_details, args[:-3])

    # Brick selection
    print("  Brick {} selected".format(bricks_selected))

    # TODO: Allow more complex column variations
    # Special Functions on columns
    # 1. Herzsprung Russel columns
    # absolut magnitude / luminosity
    # stellar classification / effective temperatures
    #custom_functions = {}

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
    # TODO: Add Color and Size labels to "text" as they cannot be included in hoverinfo right now
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
    # Add sizing
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
        # NOTE: Sizing in titles not supported (2019-04)
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
