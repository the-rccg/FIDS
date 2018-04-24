# Define Parameters
input_filename = 'PHAT_BEAST/b16_stats_toothpick_v1.1.fits'
max_num_points = 2000

# Load Data
from astropy.io import fits
data = fits.open(input_filename, memmap=True)[1]
column_names = data.columns.names

# Check Data Size
import numpy as np
num_points = data.data.shape[0]
if num_points > max_num_points:
    print(data.data.shape)
    print("Using subsampling with {} points".format(max_num_points))
    select_points = np.random.choice(num_points, size=max_num_points, replace=False, p=None)
else: 
    select_points = range(num_points)

# Reduce to useful
available_indicators = [name for name in column_names if name.split('_')[-1] not in ['p50', 'p84', 'p16', 'Exp']] #df['Indicator Name'].unique()
print(available_indicators)

# Start App
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
app = dash.Dash()
app.title = 'FITS Dashboard'

# Visual layout
app.layout = html.Div([
    
    # Data Amount Selector
    # To Be Coded
    
    # New Subsample Generator
    # To Be Coded
        
    # Axis Selection
    html.Div([
        # Select X-Axis
        html.Div([
            dcc.Dropdown(
                id='xaxis-column',
                options=[{'label': i, 'value': i} for i in available_indicators],
                value='DEC'
            ),
            dcc.RadioItems(
                id='xaxis-type',
                options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                value='Linear',
                labelStyle={'display': 'inline-block'}
            )
        ],
        style={'width': '48%', 'display': 'inline-block'}),
        # Select Y-Axis
        html.Div([
            dcc.Dropdown(
                id='yaxis-column',
                options=[{'label': i, 'value': i} for i in available_indicators],
                value='RA'
            ),
            dcc.RadioItems(
                id='yaxis-type',
                options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                value='Linear',
                labelStyle={'display': 'inline-block'}
            )
        ],style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ]),

    dcc.Graph(id='indicator-graphic'),

])

@app.callback(
    dash.dependencies.Output('indicator-graphic', 'figure'),
    [dash.dependencies.Input('xaxis-column', 'value'),
     dash.dependencies.Input('yaxis-column', 'value'),
     dash.dependencies.Input('xaxis-type', 'value'),
     dash.dependencies.Input('yaxis-type', 'value')])
def update_graph(xaxis_column_name, yaxis_column_name,
                 xaxis_type, yaxis_type
                 ):

    return {
        'data': [go.Scatter(
            x = data.data[xaxis_column_name][select_points],
            y = data.data[yaxis_column_name][select_points],
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