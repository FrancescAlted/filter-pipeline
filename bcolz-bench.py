from __future__ import print_function

import os
import shutil
import argparse
import sys
from time import time
import numpy as np
import bcolz


N = int(4e8)
shape = (400, 100, 100, 100)

def create_bcolz(arr, dirname):
    cparams = bcolz.cparams(clevel=5, cname='lz4')
    ca = bcolz.carray(arr, rootdir=dirname, mode='w', cparams=cparams,
                      chunklen=1)
    ca.flush()
    return ca


tinfo = bcolz.blosc_version()
blosc_cnames = bcolz.blosc_compressor_list()
print("-=" * 38)
print("bcolz version:     %s" % bcolz.__version__)
tinfo = bcolz.blosc_version()
print("Blosc version:     %s (%s)" % (tinfo[0], tinfo[1]))
print("-=" * 38)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r", "--read-only", action="store_true",
        help="Read only bench.",
    )
    parser.add_argument(
        "-w", "--write-only", action="store_true",
        help="Write only bench.",
    )
    parser.add_argument(
        "-m", "--in-memory", action="store_true",
        help="In-memory bench (incompatible with -r).",
    )
    args = parser.parse_args()

    dirname = sys.argv[0].replace(".py", ".bcolz")
    if args.in_memory:
        print("Working in-memory!")
        dirname = None

    if not args.read_only:
        if dirname and os.path.isdir(dirname):
            shutil.rmtree(dirname)
        arr = np.arange(N, dtype=np.int32).reshape(shape)
        t0 = time()
        ca = create_bcolz(arr, dirname)
        t = time() - t0
        print("Time to create %s: %.3fs (%.2f GB/s)" % (
            dirname, time() -t0, N * 4 / (2**30 * t)))
        #cratio = ca.nbytes / float(ca.cbytes)
        #print("Compression ratio:   %.2fx" % cratio)

    if not args.write_only:
        t0 = time()
        if args.in_memory:
            bca = ca[:]
        else:
            bca = bcolz.open(dirname, mode='r')[:]
        t = time() - t0
        print("Time to read %s:   %.3fs (%.2f GB/s)" % (
            dirname, time() -t0, N * 4 / (2**30 * t)))
