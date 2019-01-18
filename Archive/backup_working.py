# -*- coding: utf-8 -*-
"""
FITS Dash App
Quickly sketch and explore data tables and relations sae in FITS format 

@author: RCCG
"""

# Define Parameters
filename = 'b16_stats_toothpick_v1.1.fits'
filepath = '/home/ilion/0/qd174/Git/PHAT_BEAST/'
max_num_points = 8000



# Load Data
from astropy.io import fits
input_filename = filepath + filename
data = fits.open(input_filename, memmap=True)[1]
column_names = data.columns.names

# Subsample when data is too large
import numpy as np
num_points = data.data.shape[0]
if num_points > max_num_points:
    print(data.data.shape)
    print("Using subsampling with {} points".format(max_num_points))
    select_points = np.random.choice(num_points, size=max_num_points, replace=False, p=None)
else: 
    select_points = range(num_points)

# Reduce Columns to Useful
selected_columns = [name for name in column_names if name.split('_')[-1] not in ['p50', 'p84', 'p16', 'Exp']]
print("Selected Columns: {}".format(selected_columns))

# Start App
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
app = dash.Dash('fits_dashboard')
app.title = 'FITS Dashboard: {}'.format(filename)

# Visual layout
app.layout = html.Div([
    
    # Data Amount Selector
    # To Be Coded
    html.Div(
        [
            dcc.Slider(
                id='num_selection',
                min=0,
                max=num_points,
                value=max_num_points,
                step=1000,
            )
        ]
        #html.Div(id='slider-container')
    ),
    # New Subsample Generator
    # To Be Coded
        
    # Axis Selection
    html.Div([
        # Select X-Axis
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
        # Select Y-Axis
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
            style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
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
        dash.dependencies.Input('num_selection', 'value')
    ])


def update_graph(xaxis_column_name, yaxis_column_name,
                 xaxis_type, yaxis_type, num_points
                 ):
    """ update graph based on new selected variables """
    select_points = np.random.choice(num_points, size=max_num_points, replace=False, p=None)
    print("resampling with {} points".format(num_points))
    # allow for special functions on columns
    # 1. Herzsprung Russel columns
    # absolut magnitude / luminosity
    # stellar classification / effective temperatures
    custom_functions =  {}

    data_dic = {}
    if xaxis_column_name in selected_columns:
        data_dic['x'] = data.data[xaxis_column_name][select_points]
    elif xaxis_column_name in custom_functions.keys():
        data_dic['x'] = custom_functions[xaxis_column_name]  # TODO: Actually call the function
    else:
        print("This should not occur, column should not have been selectabl!")
    # TODO: function to handle both x and y
    if yaxis_column_name in selected_columns:
        data_dic['y'] = data.data[yaxis_column_name][select_points]
    elif yaxis_column_name in custom_functions.keys():
        data_dic['y'] = custom_functions[yaxis_column_name]  # TODO: Actually call the function
    else:
        print("This should not occur, column should not have been selectabl!")
    
    
    return {'data': [go.Scatter(
            **data_dic,
            text = data.data['Name'][select_points],
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