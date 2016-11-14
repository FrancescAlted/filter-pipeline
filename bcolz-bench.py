from __future__ import print_function

import sys
from time import time
import numpy as np
import bcolz


N = int(1e8)
a = np.arange(N, dtype=np.int32).reshape(100, 100, 100, 100)

def create_bcolz(dirname, codec):
    if codec != "None":
        cparams = bcolz.cparams(clevel=5, cname=codec)
    else:
        cparams = bcolz.cparams(clevel=0)
    ca = bcolz.carray(a, rootdir=dirname, mode='w', cparams=cparams,
                      chunklen=1)
    ca.flush()

def read_bcolz(dirname):
    return bcolz.open(dirname, mode='r')[:]


tinfo = bcolz.blosc_version()
blosc_cnames = bcolz.blosc_compressor_list()
print("-=" * 38)
print("bcolz version:     %s" % bcolz.__version__)
tinfo = bcolz.blosc_version()
print("Blosc version:     %s (%s)" % (tinfo[0], tinfo[1]))

if __name__ == "__main__":
    fname = sys.argv[0].replace(".py", ".bcolz")
    codec = sys.argv[1]
    t0 = time()
    create_bcolz(fname, codec)
    t = time() - t0
    print("Time to create %s: %.3fs (%.2f GB/s)" % (
        fname, time() -t0, a.size * a.itemsize / (2**30 * t)))

    t0 = time()
    bca = read_bcolz(fname)
    t = time() - t0
    print("Time to read %s:   %.3fs (%.2f GB/s)" % (
        fname, time() -t0, a.size * a.itemsize / (2**30 * t)))
