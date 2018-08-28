import numpy as np
cimport numpy as np

def compare(float[:,:,:] g, float px, float py, int x, int y, int dx, int dy):
    cdef float ox, oy
    ox, oy = g[x+dx,y+dy,:]
    ox += dx; oy += dy

    # found a better point
    if (ox*ox + oy*oy) < (px*px + py*py):
        return ox, oy
    else:
        return px, py

def sdf_sweep(float[:,:,:] g):
    cdef int wp2, hp2
    cdef float px, py
    wp2, hp2 = g.shape[:2]
    # sweep over grid
    for y in range(1, hp2-1):
        for x in range(1, wp2-1):
            px, py = g[x,y,:]
            px, py = compare(g, px, py, x, y, -1,  0)
            px, py = compare(g, px, py, x, y,  0, -1)
            px, py = compare(g, px, py, x, y, -1, -1)
            px, py = compare(g, px, py, x, y,  1, -1)
            g[x,y,0] = px; g[x,y,1] = py

        for x in range(wp2-2, 0, -1):
            px, py = g[x,y,:]
            px, py = compare(g, px, py, x, y, 1, 0)
            g[x,y,0] = px; g[x,y,1] = py

    for y in range(hp2-2, 0, -1):
        for x in range(wp2-2, 0, -1):
            px, py = g[x,y,:]
            px, py = compare(g, px, py, x, y,  1, 0)
            px, py = compare(g, px, py, x, y,  0, 1)
            px, py = compare(g, px, py, x, y, -1, 1)
            px, py = compare(g, px, py, x, y,  1, 1)
            g[x,y,0] = px; g[x,y,1] = py

        for x in range(1, wp2-1):
            px, py = g[x,y,:]
            px, py = compare(g, px, py, x, y, -1, 0)
            g[x,y,0] = px; g[x,y,1] = py

    return g
