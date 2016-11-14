from __future__ import print_function

import sys
from time import time
import numpy as np
import bcolz


N = int(1e8)
a = np.arange(N, dtype=np.int32).reshape(100, 100, 100, 100)

def create_bcolz(dirname, codec):
    if codec != "None":
        cparams = bcolz.cparams(clevel=9, cname=codec, shuffle=1)
    else:
        cparams = bcolz.cparams(clevel=0)
    ca = bcolz.carray(a, rootdir=dirname, mode='w', cparams=cparams,
                      chunklen=1)
    ca.flush()
    return ca


tinfo = bcolz.blosc_version()
blosc_cnames = bcolz.blosc_compressor_list()
print("-=" * 38)
print("bcolz version:     %s" % bcolz.__version__)
tinfo = bcolz.blosc_version()
print("Blosc version:     %s (%s)" % (tinfo[0], tinfo[1]))

if __name__ == "__main__":
    dirname = sys.argv[0].replace(".py", ".bcolz")
    codec = sys.argv[1]
    if (len(sys.argv) > 2):
        print("Working in-memory!")
        inmemory = True
    else:
        inmemory = False

    t0 = time()
    ca = create_bcolz(dirname, codec)
    t = time() - t0
    print("Time to create %s: %.3fs (%.2f GB/s)" % (
        dirname, time() -t0, a.size * a.itemsize / (2**30 * t)))
    #cratio = ca.nbytes / float(ca.cbytes)
    #print("Compression ratio:   %.2fx" % cratio)

    t0 = time()
    if inmemory:
        bca = ca[:]
    else:
        bca = bcolz.open(dirname, mode='r')[:]
    t = time() - t0
    print("Time to read %s:   %.3fs (%.2f GB/s)" % (
        dirname, time() -t0, a.size * a.itemsize / (2**30 * t)))
