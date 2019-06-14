# Introducing FIDS

**A DASHboard for FITS files**

An interface for visualizing large FITS Table data remotely or locally in a dashboard for preliminary analysis of datasets and interactively selecting the data to download.

FIDS makes use of memory buffering of FITS files through AstroPy, subsampling of data to fit into memory through NumPy, visualizing using Flask and React through Dash, and interactive selecting through Numba compiled point-in-polygon algorithms. 

Distributed computing through Dask is still being developed to ensure comparable performance and minimal setup is maintained under all circumstances. 

[![astropy](http://img.shields.io/badge/powered%20by-AstroPy-orange.svg?style=flat)](http://www.astropy.org/)

## Setup

### Installing Astropy

```bash
pip install astropy
```

### Installing Plotly.Dash  (https://dash.plot.ly/installation)

```bash
pip install dash  # The core dash backend
pip install dash-renderer  # The dash front-end
pip install dash-html-components  # HTML components
pip install dash-core-components  # Supercharged components
pip install dash-bootstrap-components  # Bootstrap components
pip install dash-auth  # Authorization component
pip install plotly --upgrade  # Plotly graphing library used in examples
```

### Installing Numba & Dask

```bash
pip install numba  # JIT Compilation of code
pip install dask  # Allow distributed computing
```
### Installing other dependencies
```bash
pip install tqdm  # Progress bar in setup
```

## Running FIDS

### Adjusting Settings

Open settings.json and simply point the path to the folder with your data. That's it!

Additionally, there are other parameters to adjust for your applications from visual formatting to the port to run on. However, none of these settings are necessary to adjust in order for FIDS to run besides defining the path to the data.

### Starting FIDS

Just run the FIDS file and wait for the server IP to show up (e.g. 127.0.0.1:80) 

```shell
python FIDS.py
```

## Sample View

![sample view](https://github.com/the-rccg/FITS_dashboard/blob/master/assets/img/FIDS_screenshot.png)
