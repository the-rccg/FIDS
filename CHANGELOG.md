# FIDS Changelog


## FIDS V0.3.0

### 2019-06-05

- Include Winding Number algorithm for comparison

### 2019-06-04

- Remove obsolete files
- Update contribution guidelines

### 2019-05-31

- Fix duplicate axis query bug
- Move to vectorized point-in-polygon algorithm
- Reduce download confirm to two clicks

### 2019-05-30

- cache timeout=0 for send_file for mac compability 

### 2019-05-27

- Fix undersampling error causing empty NumPy array values to be plotted
- Fix unicode encoding with type recasting
- First draft of iterative sample size adjustment
- Move colorbar title to the right of the colorbar
- Remove old hacks
- Update screenshot
- Update algorithm evaluations

### 2019-05-26

- Allow download of all in selection via one file download or flask streaming
- Add mouse-over descriptions
- Revamped download section to two buttons
- Further explanations

### 2019-05-16

- Adding Point-in-Polygon slicing to download all data in lasso or retangle selection
- Add algorithm evaluation notebooks for future reference and further analysis if weakpoints are discovered

### 2019-05-10

- Allow plotting combined columns
- Dynamically format column names for more readable information
- Add collapsable structures and further abstractions
- Uniformize component numbering

### 2019-05-09

- Add Contribution Guidelines
- Add Documentation

### 2019-05-08

- Implement collapsable and dynamically displayed axis formatter
- Rename reversed -> decreasing 
- Allow exponential formatting of axis
- Show slicing limits next to sliders for each column sliced on
- Restructure functions to data_selector.py
- Update screenshot

### 2019-05-07

- Add encodings to files
- Add and uniformize docstringsmore descriptions,
- Update screenshot 
- Hide debug fields
- Clearer slicing stdout and cosmetic adjustment

### 2019-05-06

- Fix naming in subsampling by moving to chararray for labels
- Recolor afte removign color axis
- Allow downloading all data points that fall into the criteria specified
- More readable comments and structure of HTML app setup
- Fix typos in comments

### 2019-05-04

- Reduced memory overhead from reducing to selected axis in slicing data
- Link into footer
- Rename data functions to make use clearer
- Deleted old beta files


## FIDS V0.2.0

### 2019-04-26

- implemented get_all_data on Zero selected sample size
- implemented faster type reading (removed implicit read of entire array)
- added debug elements (shutdown button with requiring confirmation)
- moved loads to functions for easier profiling

### 2019-04-19

- Implemented WebGL for larger Plots
- Fixed axis label and title collision problem
- Implemented documentation for FIDS

### 2019-04-06

- Move parse_datatype to io_tools instead of setup_dataset
- Slider Styling: extend padding and inherit width
- Added get_file_info.py
- Fixed get_sig_digits to work with inverted range

### 2019-04-04

- Added limiting parameter to prevent endless searches
- Added styling parameters
- Added type checking to fix sending errors (parse_datatpe)
- Fixed naming convention (slicer->slider)

## FIDS V0.1.0

### 2019-04-03

- Given directory, map all FITS files
- Allow display of FITS DataTables in 2D chart
    - Column on: X, Y, Color, Size
    - Including Name
- Allow show/hiding slicing columns
    - Slice on axes with slider
    - Filter for used bricks
    - Oversample by range overlap with brick
    - Dynamically determines max/min values with needed significant digits