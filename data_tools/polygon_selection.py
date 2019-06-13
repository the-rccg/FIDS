# -*- coding: utf-8 -*- 
import numpy as np
from numba import jit


# Algorithms


@jit(nopython=True, parallel=True)
def vec_point_in_polygon(x, y, poly):
    """
    x, y -- x and y coordinates of point, as 1D NumPy Array
    poly -- 2D collection of shape [(x, y), (x, y), ...]
    -------------------------------------------------
    VecPNPOLY - Vectorized Point Inclusion in Polygon Test
    by RCCG (github.com/the-rccg)
    adapted from W. Randolph Franklin (WRF), see: https://wrf.ecse.rpi.edu/Research/Short_Notes/pnpoly.html
    """
    num = poly.shape[0]  # Number of vertices
    i = 0                # First Vertex
    j = num - 1          # Previous Vertex
    # Explicit first lop
    c = np.logical_and(
        np.logical_xor((poly[i][1] > y), (poly[j][1] > y)),
        (x < poly[i][0] + (poly[j][0]-poly[i][0]) * (y-poly[i][1]) / (poly[j][1]-poly[i][1]))
    )
    for i in range(1, num):
        j = i-1
        c = np.logical_xor(
            c,
            np.logical_and(
                np.logical_xor((poly[i][1] > y), (poly[j][1] > y)),
                (x < poly[i][0] + (poly[j][0]-poly[i][0]) * (y-poly[i][1]) / (poly[j][1]-poly[i][1]))
            )
        )
    return c


@jit(nopython=True, parallel=True, nogil=True, fastmath=True)
def point_in_polygon(x, y, poly):
    """
    x, y -- x and y coordinates of point, as 1D NumPy Array
    poly -- 2D collection of shape [(x, y), (x, y), ...]
    -------------------------------------------------
    PNPOLY - Point Inclusion in Polygon Test
    W. Randolph Franklin (WRF) 
    source:  https://wrf.ecse.rpi.edu/Research/Short_Notes/pnpoly.html
    adapted by RCCG (github.com/the-rccg)
    """
    num = poly.shape[0]  # Number of vertices
    i = 0            # First Vertex
    j = num - 1      # Previous Vertex
    # Explicit first lop
    c = ((poly[i][1] > y) != (poly[j][1] > y)) and \
                (x < poly[i][0] + (poly[j][0] - poly[i][0]) * (y - poly[i][1]) /
                                (poly[j][1] - poly[i][1]))
    # Loop over vertices
    for i in range(1, num):
        j = i-1
        if ((poly[i][1] > y) != (poly[j][1] > y)) and \
                (x < poly[i][0] + (poly[j][0] - poly[i][0]) * (y - poly[i][1]) /
                                (poly[j][1] - poly[i][1])):
            c = not c
    return c


@jit(nopython=True, parallel=True, nogil=True, fastmath=True)
def points_in_polygon(x, y, vertices):
    flags = np.empty(x.shape[0], dtype=np.bool_)
    for i in range(x.shape[0]):
        flags[i] = point_in_polygon(x[i], y[i], vertices)
    return flags


# Convenience Functions


#@jit(nopython=True, parallel=True)
def get_data_in_polygon(xaxis_name, yaxis_name, vertices, return_data):
    """ Return all data in/or on polygon from bricks

    Iteratively appends data from bricks
    """
    flags = points_in_polygon(
        return_data[xaxis_name],
        return_data[yaxis_name],
        vertices
    )
    return_data = {col: return_data[col][flags] for col in return_data.keys()}
    return return_data


from .data_selector import reduce_cols, get_axis_data, adjust_axis_type
def get_data_in_selection(xaxis_name, yaxis_name, vertices, return_data, axis_name_list,
                          xaxis_type='linear', yaxis_type='linear',
                          xaxis_two_name='', xaxis_operator='', yaxis_two_name='', yaxis_operator=''):
    """ Return data in the selected area
    
    Adjust for Combined Axes, Scaled Axes, and Polygon Selection
    """
    # 1. Combined column fix: get_axis_data -> [axis_name, axis_values]
    disp_xaxis_name, xaxis_data = get_axis_data(return_data, xaxis_name, xaxis_operator, xaxis_two_name)
    disp_yaxis_name, yaxis_data = get_axis_data(return_data, yaxis_name, yaxis_operator, yaxis_two_name)
    # 2. Scaling fix: adjust_axis_type -> [axis_type, axis_name, axis_values]
    xaxis_data = adjust_axis_type(xaxis_type, disp_xaxis_name, xaxis_data)[-1]
    yaxis_data = adjust_axis_type(yaxis_type, disp_yaxis_name, yaxis_data)[-1]
    # 3. Get those in Polygon
    flags = points_in_polygon(xaxis_data, yaxis_data, vertices)
    # Reduce Data
    return_data = reduce_cols(return_data, axis_name_list, selection=flags)
    return return_data


# Support Functions


def reduce_vertices(prel_vertices):
    """ Remove redundant vertices from list 
    
    Sometimes duplicates were created in plotly -- legacy, the bug seems to be resolved
    """
    vertices = []
    for idx in range(1, len(prel_vertices)-2):
        if   (prel_vertices[idx][0] == prel_vertices[idx+1][0]) \
              and (prel_vertices[idx-1][0] == prel_vertices[idx][0]):
            continue
        elif (prel_vertices[idx][1] == prel_vertices[idx+1][1]) \
              and (prel_vertices[idx-1][1] == prel_vertices[idx][1]):
            continue
        else:
            vertices.append(prel_vertices[idx])
    vertices.append(prel_vertices[-1])
    return vertices
