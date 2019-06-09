# FIDS Changelog

## FIDS V0.3.x

### 2019-06-09   (V0.3.1)

- Restructuring project for easier extension building (e.g. introduce .io_tools)
- Fix display of "x.0" slider issue through explicit recasting
- Allow adding zero to slider based on percentage distance to limits

### 2019-06-08   (V0.3.0)

- Allow selection of data on combined and rescaled axes
- Improve speed by ordering fractions in slicing, other small changes
- $\texttt{params_to_link}$ now adjusts for combined axes


## FIDS V0.2.x

### 2019-06-05  (V0.2.14)

- Include Winding Number algorithm for comparison

### 2019-06-04  (V0.2.13)

- Remove obsolete files
- Update contribution guidelines

### 2019-05-31  (V0.2.12)

- Fix duplicate axis query bug
- Move to vectorized point-in-polygon algorithm
- Reduce download confirm to two clicks

### 2019-05-30  (V0.2.11)

- Cache timeout=0 for send_file for mac compability 

### 2019-05-27  (V0.2.10)

- Fix undersampling error causing empty NumPy array values to be plotted
- Fix unicode encoding with type recasting
- First draft of iterative sample size adjustment
- Move colorbar title to the right of the colorbar
- Remove old hacks
- Update screenshot
- Update algorithm evaluations

### 2019-05-26  (V0.2.9)

- Allow download of all in selection via one file download or flask streaming
- Add mouse-over descriptions
- Revamped download section to two buttons
- Further explanations

### 2019-05-16  (V0.2.8)

- Adding Point-in-Polygon slicing to download all data in lasso or retangle selection
- Add algorithm evaluation notebooks for future reference and further analysis if weakpoints are discovered

### 2019-05-10  (V0.2.7)

- Allow plotting combined columns
- Dynamically format column names for more readable information
- Add collapsable structures and further abstractions
- Uniformize component numbering

### 2019-05-09  (V0.2.6)

- Add Contribution Guidelines
- Add Documentation

### 2019-05-08  (V0.2.5)

- Implement collapsable and dynamically displayed axis formatter
- Rename reversed -> decreasing 
- Allow exponential formatting of axis
- Show slicing limits next to sliders for each column sliced on
- Restructure functions to data_selector.py
- Update screenshot

### 2019-05-07  (V0.2.4)

- Add encodings to files
- Add and uniformize docstringsmore descriptions,
- Update screenshot 
- Hide debug fields
- Clearer slicing stdout and cosmetic adjustment

### 2019-05-06  (V0.2.3)

- Fix naming in subsampling by moving to chararray for labels
- Recolor afte removign color axis
- Allow downloading all data points that fall into the criteria specified
- More readable comments and structure of HTML app setup
- Fix typos in comments

### 2019-05-04  (V0.2.1)

- Reduced memory overhead from reducing to selected axis in slicing data
- Link into footer
- Rename data functions to make use clearer
- Deleted old beta files

### 2019-04-26  (V0.2.0)

- Implemented get_all_data on Zero selected sample size
- Implemented faster type reading (removed implicit read of entire array)
- Added debug elements (shutdown button with requiring confirmation)
- Moved loads to functions for easier profiling


## FIDS V0.1.x

### 2019-04-19  (V0.1.3)

- Implemented WebGL for larger Plots
- Fixed axis label and title collision problem
- Implemented documentation for FIDS

### 2019-04-06  (V0.1.2)

- Move parse_datatype to io_tools instead of setup_dataset
- Slider Styling: extend padding and inherit width
- Added get_file_info.py
- Fixed get_sig_digits to work with inverted range

### 2019-04-04  (V0.1.1)

- Added limiting parameter to prevent endless searches
- Added styling parameters
- Added type checking to fix sending errors (parse_datatpe)
- Fixed naming convention (slicer->slider)

### 2019-04-03  (V0.1.0)

- Given directory, map all FITS files
- Allow display of FITS DataTables in 2D chart
    - Column on: X, Y, Color, Size
    - Including Name
- Allow show/hiding slicing columns
    - Slice on axes with slider
    - Filter for used bricks
    - Oversample by range overlap with brick
    - Dynamically determines max/min values with needed significant digits