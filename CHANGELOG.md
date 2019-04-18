# FIDS Changelog


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

## Dash V0.1.0

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