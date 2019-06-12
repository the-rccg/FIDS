# Introducing FIDS 
**A DASHboard for FITS files**

An interface for visualizing large FITS Table data remotely or locally in a dashboard for preliminary analysis of datasets and interactively selecting the data to download.

FIDS makes use of memory buffering of FITS files through AstroPy, subsampling of data to fit into memory through NumPy, visualizing using Flask and React through Dash, and interactive selecting through Numba compiled point-in-polygon algorithms. 

Distributed computing through Dask is still being developed to ensure comparable performance and minimal setup is maintained under all circumstances. 

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

