# FITS_dashboard
An interface for loading FITS Table data and displaying them in a Plotly.Dash dashboard for preliminary analysis of datasets in astronomy. 

Makes use of memory buffering of FITS files through AstroPy, subsampling of data to fit into memory through NumPy, and visualization using Flask and React through Dash

## Setup
### Installing Astropy
```cmd
pip install astropy
```

### Installing Plotly.Dash  (https://dash.plot.ly/installation)
```pip
pip install dash  # The core dash backend
pip install dash-renderer  # The dash front-end
pip install dash-html-components  # HTML components
pip install dash-core-components  # Supercharged components
pip install plotly --upgrade  # Plotly graphing library used in examples
```

## Sample View
![sample view](https://github.com/the-rccg/FITS_dashboard/blob/master/img/FIDS_screenshot.png)

