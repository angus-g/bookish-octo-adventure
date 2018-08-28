import sdf

from PIL import Image
from PIL.ImageOps import invert
import math
import numpy as np
import sys

# generate a signed distance field from an image

def sdf_brute(img):
    sdf = Image.new('L', img.size)
    # stencil size for calculation
    spread = 32

    for x in range(w):
        for y in range(h):
            # get region
            # brute force closest "on" pixel
            r = img.crop((x-spread/2, y-spread/2, x+spread/2 + 1, y+spread/2 + 1))
            # originally, infinite distance
            dist = None
            # is the target pixel in?
            target = r.getpixel((spread//2, spread//2)) > 255/2

            # loop over all pixels in region
            for xx in range(spread+1):
                for yy in range(spread+1):
                    # this pixel is in the same state as the target
                    if (r.getpixel((xx,yy)) > 255/2) == target:
                        continue

                    # calculate new (squared) distance and update
                    local_dist = (xx-spread/2)**2 + (yy-spread/2)**2
                    if dist is None:
                        # first time, just save the value
                        dist = local_dist
                    else:
                        # otherwise, choose the minimum
                        dist = min(dist, local_dist)

            if dist is None:
                # infinite distance (normalised to 1)
                dist = 1.0
            else:
                # get actual distance and normalise by maximum possible distance
                dist = math.sqrt(dist) / math.sqrt(2*(spread/2)**2)

            # use negative distance for values inside
            # this gives us the range [-1,1]
            if target:
                dist *= -1

            # rescale [-1,1] -> [-0.5,0.5] -> [0,1] and convert to integer
            dist = int(255 * (dist/2 + 0.5))

            # calculate actual distance and normalise
            sdf.putpixel((x, y), (dist,))

        print('{}/{}'.format(x,w))

    return sdf

def sdf_sweep_init(img):
    w, h = img.size
    # init grid
    g1 = np.empty((w+2,h+2,2), dtype='f4')
    g1[...] = np.inf
    g2 = np.empty((w+2,h+2,2), dtype='f4')
    g2[...] = np.inf
    
    # leave a 1 point gutter
    for y in range(1,h+1):
        for x in range(1,w+1):
            p = img.getpixel((x-1,y-1))[0]
            if p < 128:
                g1[x,y,:] = 0, 0
            else:
                g2[x,y,:] = 0, 0

    print('ready to run sdf')
    g1 = sdf.sdf_sweep(g1)[1:-1,1:-1]
    print('sdf 1 done')
    g2 = sdf.sdf_sweep(g2)[1:-1,1:-1]
    print('sdf 2 done')

    print(np.min(g1), np.max(g1), np.min(g2), np.max(g2))

    d1 = np.sqrt(np.einsum('ijk,ijk->ij', g1, g1))
    d2 = np.sqrt(np.einsum('ijk,ijk->ij', g2, g2))

    return d1 / d1.max() - d2 / d2.max()

img = invert(Image.open(sys.argv[1]))
sdf = sdf_sweep_init(img)
i = Image.fromarray(np.uint8(255*(sdf/2 + 0.5)).T)
i.save('sdf.png')
