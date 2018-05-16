# FITS_dashboard
An interface for loading FITS Table data and displaying them in a Plotly.Dash dashboard for preliminary analysis of datasets in astronomy. 

Makes use of memory buffering of FITS files through AstroPy, subsampling of data to fit into memory through NumPy, and visualization using Flask and React through Dash

## Setup
### Installing Astropy
```python
pip install astropy
```

### Installing Plotly.Dash  (https://dash.plot.ly/installation)
```python
pip install dash  # The core dash backend
pip install dash-renderer  # The dash front-end
pip install dash-html-components  # HTML components
pip install dash-core-components  # Supercharged components
pip install plotly --upgrade  # Plotly graphing library used in examples
```
