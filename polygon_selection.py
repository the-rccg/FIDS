import numpy as np
from numba import jit

@jit(nopython=True, parallel=True)
def isPointInPath(x, y, poly):
    """
    x, y -- x and y coordinates of point
    poly -- a list of tuples [(x, y), (x, y), ...]
    -------------------------------------------------
    PNPOLY - Point Inclusion in Polygon Test
    W. Randolph Franklin (WRF) 
    source:  https://wrf.ecse.rpi.edu/Research/Short_Notes/pnpoly.html
    """
    num = len(poly)  # Number of vertices
    i = 0            # First Vertex
    j = num - 1      # Previous Vertex
    c = False
    # Loop over vertices
    for i in range(num):
        if ((poly[i][1] > y) != (poly[j][1] > y)) and \
                (x < poly[i][0] + (poly[j][0] - poly[i][0]) * (y - poly[i][1]) /
                                (poly[j][1] - poly[i][1])):
            c = not c
        j = i
    return c


@jit(nopython=True, parallel=True)
def get_even_odd_flags(x, y, vertices):
    """ Allow vector x/y coordinate to be calculated """
    flags = np.empty(len(x), dtype=np.bool_)
    for i in range(len(x)):
        flags[i] = isPointInPath(x[i], y[i], vertices)
    return flags



#@jit(nopython=True, parallel=True)
def get_data_in_polygon(xaxis_name, yaxis_name, vertices, return_data):
    """ Return all data in/or on polygon from bricks

    Iteratively appends data from bricks
    """
    flags = get_even_odd_flags(return_data[xaxis_name], return_data[yaxis_name], vertices)
    return_data = {col:return_data[col][flags] for col in return_data.keys()}
    return return_data

# Reduce vertices: Sometime dupliates were created
def reduce_vertices(prel_vertices):
    """ Remove redundant vertices from list """
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
