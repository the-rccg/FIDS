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
filepath = 'D:/OneDrive/Grad School/Research/Klessen/Gouliermis/PHAT_BEAST/'  #'/home/ilion/0/qd174/Git/PHAT_BEAST/'

# Load Data
from astropy.io import fits
import os
file_list = [item for item in os.listdir(filepath) if item[-5:]=='.fits']
data = np.array([fits.open(filepath+file, memmap=True)[1] for file in file_list])
column_names = data[0].columns.names

# Draw Params
max_display_count = 12000
display_count = 4000

# Default Parameters
brick_idx = [1]

# Subsample when data is too large
import numpy as np
data_counts = [d.header['NAXIS2'] for d in data]  # Header is fastest way to get number of data points
def getSampleIndices(sample_size, total_size):
    """ 
    Returns data points for the subsample in the range
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
                value=[1],
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
                marks={0:'0', max_display_count:"{:,}".format(max_display_count)}
            )
        ],
        style={'height':34, 'width':'97%', 'margin':'auto auto'}
        #html.Div(id="selection-container")
    ),

    # Element 3: New Subsample Generator
    # To Be Coded
        
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
                            options=[{'label': i, 'value': i} for i in selected_columns],
                            value='DEC'
                        ),
                        #],
                        #style={'display':'inline-block', 'margin':'auto auto', 'width':'100%'}),
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
            ),
        ]
    ),
    html.Div(
        [
            dcc.Dropdown(
                id='color-column',
                options=[{'label': i, 'value': i} for i in selected_columns],
                value='logA_Best'
            ),
        ]
    ),
    dcc.Graph(id='indicator-graphic'),
])

#@app.callback(
#    dash.dependencies.Output('selection-container','children'),
#    [dash.dependencies.Input('display_count_selection', 'value')]
#)

#def update_sample(display_count_selection):



@app.callback(
    dash.dependencies.Output('indicator-graphic', 'figure'),
    [   
        dash.dependencies.Input('xaxis-column', 'value'),
        dash.dependencies.Input('yaxis-column', 'value'),
        dash.dependencies.Input('color-column', 'value'),
        dash.dependencies.Input('xaxis-type', 'value'),
        dash.dependencies.Input('yaxis-type', 'value'),
        dash.dependencies.Input('display_count_selection', 'value'),
        dash.dependencies.Input('brick_selector', 'value')
    ])


def update_graph(xaxis_column_name, yaxis_column_name, color_column_name,
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
    # Check for valid axis
    if (xaxis_column_name in selected_columns) and (yaxis_column_name in selected_columns) and (color_column_name in selected_columns):
        brick_count = len(brick_idx)  # Number of bricks
        # Allocate Memory for Data
        data_dic['x'] = np.empty(display_count)  # X-Axis
        data_dic['y'] = np.empty(display_count)  # Y-Axis
        data_dic_c = np.empty(display_count)  # Color
        text = np.empty(display_count, dtype=str)  # Description
        t1 = dt.now()
        print("empty:      {}".format(t1-t0))
        # Add Data to Array
        current_length = 0
        for brick_i in brick_idx:
            sample_size = int(display_count/brick_count)
            select_points = getSampleIndices(sample_size, data_counts[brick_i])
            print("random:     {}".format(dt.now()-t1))
            #sample_size = np.unique(selected_points)
            data_dic['x'][current_length:current_length+sample_size] = data[brick_i].data[xaxis_column_name][select_points]
            data_dic['y'][current_length:current_length+sample_size] = data[brick_i].data[yaxis_column_name][select_points]
            data_dic_c[current_length:current_length+sample_size] = data[brick_i].data[color_column_name][select_points]
            text[current_length:current_length+sample_size] = data[brick_i].data['Name'][select_points]
            print("assign {:02}:  {}".format(brick_i, dt.now()-t1))
            current_length += sample_size
            t1 = dt.now()

    return {'data': [
        go.Scatter(
            **data_dic,
            text = text,
            mode = 'markers',
            marker = {
                'size': 10,
                'opacity': 0.5,
                'color': data_dic_c,  # Add color scale
                'colorscale': 'Bluered',  # 'Greys', 'YlGnBu', 'Greens', 'YlOrRd', 'Bluered', 'RdBu', 'Reds', 'Blues', 'Picnic', 'Rainbow', 'Portland', 'Jet', 'Hot', 'Blackbody', 'Earth', 'Electric', 'Viridis', 'Cividis'
                'showscale': True,
                'colorbar': {'title':color_column_name},
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
    app.run_server(debug=False, port='5001')# host='129.206.102.157')