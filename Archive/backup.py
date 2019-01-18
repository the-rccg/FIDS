# -*- coding: utf-8 -*-
"""
FITS Dash App
Quickly sketch and explore data tables and relations sae in FITS format 

@author: RCCG
"""
import numpy as np


# File names
name_pre = 'b'
name_end = '_stats_toothpick_v1.1.fits' 
name_list = np.array(["{}{:02}{}".format(
    name_pre, i, name_end) for i in range(2,24)])
filepath = '../PHAT_BEAST/'  #'/home/ilion/0/qd174/Git/PHAT_BEAST/'

# Load Data
from astropy.io import fits
data = np.array([fits.open(filepath + filename, memmap=True)[1] for filename in name_list])
column_names = data[0].columns.names

# Draw Params
max_display_count = 12000
display_count = 4000

# Default Parameters
brick_idx = [16]


# Subsample when data is too large
import numpy as np
data_counts = [d.header['NAXIS2'] for d in data]
"""
if all([(data_count > display_count) for brick_i in brick_idx]):
    print(np.sum([data[brick_i].data.shape for brick_i in brick_idx]))
    print("Using subsampling with {} points".format(display_count))
    # note: allows multiple identical values, hence n<=num_points, but orders mag faster
    select_points = np.random.randint(
        low=0, high=data_count+1, 
        size=display_count)
else: 
    select_points = range(data_count)
"""

# Reduce Columns to Useful
selected_columns = [name for name in column_names if name.split('_')[-1] not in ['p50', 'p84', 'p16', 'Exp']]
#print("Selected Columns: {}".format(selected_columns))

# Start App
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
app = dash.Dash('fits_dashboard')
app.title = 'FITS Dashboard: PHAT BEAST'

# Visual layout
app.layout = html.Div([
    
    # Element 1: Data File Selector
    html.Div(
        [
            dcc.Dropdown(
                id='brick_selector',
                options=[
                    {'label': 'Brick: {}'.format(i), 'value': i} 
                    for i in range(2,24)
                ],
                value=[16],
                multi=True
            )
        ]
    ),

    # Element 2: Data Amount Selector
    html.Div(
        [
            dcc.Slider(
                id='display_count_selection',
                min=0,
                max=max_display_count,
                value=display_count,
                step=1000,
            )
        ]
    ),

    # Element 3: New Subsample Generator
    # To Be Coded
        
    # Axis Selection
    html.Div(
        [
            # 4.1: Select X-Axis
            html.Div(
                [
                    dcc.Dropdown(
                        id='xaxis-column',
                        options=[{'label': i, 'value': i} for i in selected_columns],
                        value='DEC'
                    ),
                    dcc.RadioItems(
                        id='xaxis-type',
                        options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                        value='Linear',
                        labelStyle={'display': 'inline-block'}
                    )
                ],
                style={'width': '48%', 'display': 'inline-block'}
            ),
            # 4.2: Select Y-Axis
            html.Div(
                [
                    dcc.Dropdown(
                        id='yaxis-column',
                        options=[{'label': i, 'value': i} for i in selected_columns],
                        value='RA'
                    ),
                    dcc.RadioItems(
                        id='yaxis-type',
                        options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                        value='Linear',
                        labelStyle={'display': 'inline-block'}
                    )
                ],
                style={'width': '48%', 'float': 'right', 'display': 'inline-block'}
            )
        ]
    ),
    dcc.Graph(id='indicator-graphic'),
])

@app.callback(
    dash.dependencies.Output('indicator-graphic', 'figure'),
    [   
        dash.dependencies.Input('xaxis-column', 'value'),
        dash.dependencies.Input('yaxis-column', 'value'),
        dash.dependencies.Input('xaxis-type', 'value'),
        dash.dependencies.Input('yaxis-type', 'value'),
        dash.dependencies.Input('display_count_selection', 'value'),
        dash.dependencies.Input('brick_selector', 'value')
    ])


def update_graph(xaxis_column_name, yaxis_column_name,
                 xaxis_type, yaxis_type, 
                 display_count, brick_idx
                 ):
    """ update graph based on new selected variables """

    # Brick selection
    print("Brick {} selected".format(brick_idx))

    # Create new random sample
    print("resampling with {} points".format(display_count))

    # Special Functions on columns
    # 1. Herzsprung Russel columns
    # absolut magnitude / luminosity
    # stellar classification / effective temperatures
    custom_functions =  {}

    # Fill new data
    from datetime import datetime as dt
    t0 = dt.now()
    data_dic = {}
    if (xaxis_column_name in selected_columns) and (yaxis_column_name in selected_columns):
        brick_count = len(brick_idx)
        # Allocate Memory for Data
        data_dic['x'] = np.empty(display_count)
        data_dic['y'] = np.empty(display_count)
        text = np.empty(display_count, dtype=str)
        t1 = dt.now()
        print("empty:      {}".format(t1-t0))
        # Add Data to Array
        current_length = 0
        for brick_i in brick_idx:
            sample_size = int(display_count/brick_count)
            # note: allows multiple identical values, hence n<=num_points, but orders mag faster
            select_points = np.random.randint(
                                low=0, high=data_counts[brick_i]+1, 
                                size=sample_size
                            )
            print("random:     {}".format(dt.now()-t1))
            #sample_size = np.unique(selected_points)
            data_dic['x'][current_length:current_length+sample_size] = data[brick_i].data[xaxis_column_name][select_points]
            data_dic['y'][current_length:current_length+sample_size] = data[brick_i].data[yaxis_column_name][select_points]
            text[current_length:current_length+sample_size] = data[brick_i].data['Name'][select_points]
            print("assign {:02}:  {}".format(brick_i, dt.now()-t1))
            current_length += sample_size
            t1 = dt.now()

    """
    if xaxis_column_name in selected_columns:
        data_dic['x'] = np.concatenate(
            [
                data[brick_i].data[xaxis_column_name][select_points]
                for brick_i in brick_idx
            ]
        )
    elif xaxis_column_name in custom_functions.keys():
        data_dic['x'] = custom_functions[xaxis_column_name]  # TODO: Actually call the function
    else:
        print("This should not occur, column should not have been selectabl!")
    # TODO: function to handle both x and y
    if yaxis_column_name in selected_columns:
        data_dic['y'] = np.concatenate(
            [
                data[brick_i].data[yaxis_column_name][select_points]
                for brick_i in brick_idx
            ]
        )
    elif yaxis_column_name in custom_functions.keys():
        data_dic['y'] = custom_functions[yaxis_column_name]  # TODO: Actually call the function
    else:
        print("This should not occur, column should not have been selectabl!")
    
    text = np.concatenate(
                [
                    data[brick_i].data['Name'][select_points]
                    for brick_i in brick_idx
                ]
            )
    print(text.shape)
    """

    return {'data': [go.Scatter(
            **data_dic,
            text = text,
            mode = 'markers',
            marker = {
                'size': 15,
                'opacity': 0.5,
                'line': {'width': 0.5, 'color': 'white'}
            }
        )],
        'layout': go.Layout(
            xaxis={
                'title': xaxis_column_name,
                'type': 'linear' if xaxis_type == 'Linear' else 'log'
            },
            yaxis={
                'title': yaxis_column_name,
                'type': 'linear' if yaxis_type == 'Linear' else 'log'
            },
            margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
            hovermode='closest'
        )
    }


if __name__ == '__main__':
    app.run_server(debug=True, port=5001)