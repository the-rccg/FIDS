# Unreleased

## Dash V0.1.0
- Given directory, map all FITS files
- Allow display of FITS DataTables in 2D chart
    - Column on: X, Y, Color, Size
    - Including Name
- Allow show/hiding slicing columns
    - Slice on axes with slider
    - Filter for used bricks
    - Oversample by range overlap with brick
    - Dynamically determines max/min values with needed significant digits

### Known Bugs:
- All values in sliders starting with 0 are not displayed
- AttributeError in sending ranges