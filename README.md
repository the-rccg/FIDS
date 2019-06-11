# Introducing FIDS 
**A DASHboard for FITS files**

An interface for loading FITS Table data and displaying them in a Plotly.Dash dashboard for preliminary analysis of datasets in astronomy. 

Makes use of memory buffering of FITS files through AstroPy, subsampling of data to fit into memory through NumPy, and visualization using Flask and React through Dash

[![astropy](http://img.shields.io/badge/powered%20by-AstroPy-orange.svg?style=flat)](http://www.astropy.org/)

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

### Installing Numba & Dask
```pip
pip install numba
pip install dask
```

## Sample View
![sample view](https://github.com/the-rccg/FITS_dashboard/blob/master/assets/img/FIDS_screenshot.png)

