import numpy as np
from numba import jit

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

#@jit(nopython=True, parallel=True)
def get_data_in_polygon(xaxis_name, yaxis_name, vertices, return_data):
    """ Return all data in/or on polygon from bricks

    Iteratively appends data from bricks
    """
    flags = vec_point_in_polygon(return_data[xaxis_name], return_data[yaxis_name], vertices)
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
