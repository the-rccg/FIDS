# Documentation

## Requirements

FIDS requires Python 3.6+ installed and the use of your preferred package manager for Python.

## Setup

### Getting FIDS

FIDS is hosted as a package on GitHub (<https://www.github.com/the-rccg/FIDS/>).
There are two ways to start your version of FIDS locally:

- download FIDS as a ZIP file from GitHub and extract to desired directory
- fork the GitHub repository directly

### Configuring the settings

Settings are saved in the home directory of the package under settings.json in the common and readable JSON format.
There are numerous settings available, however only a very select few are critical for getting FIDS to run.

Critical Settings:

- ```folderpath:  [string]``` Relative or absulte path to the folder containing all FITS DataTables that you want to look at with FIDS
- ```savepath:  [string]``` Relative or absolute path where FIDS will save local adjustment files

Deployment Settings:

- ```debug:  [bool]``` Boolean defining the plotly.Dash flask instance mode, and turns off login
- ```host:  [string]``` IP Address for the flask server to run on
- ```port:  [integer]```Open HTTP port for the flask server to run on
- ```enable_login:  [bool]``` Is a "login" shield needed to see the applicaion? Currently only a rudimentary login is available to reduce spamming and the simplest hacking attempts

Visual Settings:

- ```name:  [string]``` Name of the app to be displayed in the title bar of the browser
- ```title:  [string]``` Name of the app to be displayed in the center-top of the applicaiton
- ```columns_to_use:  [list of strings]``` Column names that will be allowed to be selected in the application
- ```name_column:  [string]``` Name of the column used to name the datapoints with on selection
- ```color_scale:  [string]``` Name of the colorscheme used for the color axis
- ```marker_size:  [int]``` Size of datapoints
- ```marker_opacity:  [1>x>0]``` Fraction of transparency of a datapoint
- ```display_count_max:  [integer]``` Maximum number of datapoints allowed to plott
- ```display_count_granularity:  [integer]``` smallest increment allowed to be selected on in the display count
- ```display_count_webgl_min:  [integer]``` Minimum number of points after which GPU accelerated WebGL plotting is used

Default Values:

- ```default_file:  [string]``` Default file to load for every visit
- ```default_x_column:  [string]``` Default x-column to load for every visitor
- ```default_y_column:  [string]``` Default y-column to load for every visitor
- ```default_color_column:  [string]``` Default color-collumn to load for every visitor
- ```display_count_default:  [integer]``` Default for the number of points to be loaded

Slicing Settings:

- ```selection_granularity:  [integer]``` Number of elements in which the space if uniformly cut to allow slicing
- ```min_brick_usage:  [1>x>0]``` Fraction of range to overlap with the fraction of a file for it to be surveyed for potential matches (e.g. File has range 0-100 and wanted is range -1 to +1, meaning only a 0.01 fraction of the file is within the range, therefore making slicing on it very cost inefficient)
- ```max_fill_attempts:  [integer]``` Maximum number of random sampling iterations attempted before returning only the found examples

### Initializing a new dataset

FIDS needs certain metadata to display limits, and determine if a file should even be sliced on.
In order to calculate these, just run the "setup.py" file after pointing the path in settings to the correct destination as described in the preceeding section.

It is also possible to manually provide these. For this a nested JSON format is used in the local/brick_columns_details.json (or whever you specified your local file destination). The format for this is:

```json
{
    "file_name.fits": {
        "column_name_1": {
            "max": 0,
            "min": 1
        }
    }
}
```

## Using FIDS

### Starting FIDS

Once the column details JSON is created the app can be started by running FIDS.py in your console.
This will start the flask server on your defined IP address. 

To access FIDS simply open up a window in your browser, type in the IP address and port into the address field (e.g. ```127.0.0.1:80```) and wait for the app to load. Note, the first load can take longer as the server has to check and set up the application.

### Selecting Data To Display

To see data appear in the plot the following parameters have to be given:

- Number of points to be selected
- File(s) to query from
- X-Axis Column
- Y-Axis Column

Additional variables may be defined for the color-axis and size-axis, as well as slicing on each of the columns present in the dataset is enabled when selecting them in the dropdown.

## Motivation

The use of commercial databases and cloud infrastrucure for analysis of astronomical daa has been investigated in the recent years to great progress [(Williams et al)](https://iopscience.iop.org/article/10.3847/1538-4365/aab762/pdf), however, there has been little progress in implementing cloud based visualization in combination with the cloud based computing. This means that the new technologies are not used to ttheir full poential in astronomy yet and marks the point where this project aims to make significant progress.

## Current Features

- [x] Load FITS files via memory maps
- [x] Read out columns for plotting and slicing
- [x] Adjust limits based on selected files
- [x] Interactively visualize full or subset of qualifying points
- [x] Allow downloading: individual files, current selection
- [x] Allow downloading all points that fall under criteria

## Upcoming Features

- [ ] Distribute slicing workload using Dask
- [ ] Download all displayed points, if none selected
- [ ] Mouse-over explanation
- [ ] How-to Documentation

## Long Term Plans

- [ ]  Extend data sources from simple FITS files to online catalogues of astronomical surveys using the openly available SQL interface for gathering daa.
