#!/usr/bin/env python

"""Utility to benchmark creation and reading of datasets with filters.

:Author: Francesc Alted
:Contact:  francesc@hdfgroup.org
:Created:  2016-11-14

Help to use this script can be get with::

  $ python pytables-bench.py -h

"""

from __future__ import print_function

import os
import argparse
import sys
from time import time

import numpy as np
import tables


N = int(4e8)
shape = (400, 100, 100, 100)
chunkshape = (1, 100, 100, 100)


def create_hdf5(arr, fname, method, inmemory):
    if method not in ('cont', 'nofilter'):
        filters = tables.Filters(complevel=5, complib="blosc:lz4")
    else:
        filters = None
    if inmemory:
        f = tables.open_file(fname, "w", pytables_sys_attrs=False, driver="H5FD_CORE")
        if method == 'cont':
            f.create_array(f.root, 'carray', obj=arr)
        else:
            f.create_carray(f.root, 'carray', filters=filters, obj=arr,
                            chunkshape=chunkshape)
        return f
    else:
        with tables.open_file(fname, "w", pytables_sys_attrs=False) as f:
            if method == 'cont':
                f.create_array(f.root, 'carray', obj=arr)
            else:
                f.create_carray(f.root, 'carray', filters=filters, obj=arr,
                                chunkshape=chunkshape)
        return None

def read_hdf5(fname):
    with tables.open_file(fname, "r") as f:
        return f.root.carray[:]


print("-=" * 38)
print("PyTables version:     %s" % tables.__version__)
print("HDF5 version:        %s" % tables.which_lib_version("hdf5")[1])
tinfo = tables.which_lib_version("blosc")
blosc_date = tinfo[2].split()[1]
print("Blosc version:       %s (%s)" % (tinfo[1], blosc_date))
blosc_cinfo = tables.blosc_get_complib_info()
blosc_cinfo = [
    "%s (%s)" % (k, v[1]) for k, v in sorted(blosc_cinfo.items())
    ]
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
    parser.add_argument(
        "method", nargs="?",
        help=("The method to write the dataset.  I can be:"
              "  * cont: Contiguous dataset, so no chunked"
              "  * nofilter: Chunked, but no filter is applied"
              "  * blosc: Chunked and Blosc filter is applied")
        )
    args = parser.parse_args()

    fname = sys.argv[0].replace(".py", ".h5")
    if not args.read_only and args.method not in ('cont', 'nofilter', 'blosc'):
        raise RuntimeError("method can only be 'cont', 'nofilter' or 'blosc'")
    if args.method == 'cont':
        print("Using Dataset with no chunks!")

    if not args.read_only:
        if os.path.isfile(fname):
            os.remove(fname)
        arr = np.arange(N, dtype=np.int32).reshape(shape)
        t0 = time()
        f = create_hdf5(arr, fname, args.method, args.in_memory)
        t = time() - t0
        print("Time to create %s: %.3fs (%.2f GB/s)" % (
            fname, t, N * 4 / (2**30 * t)))
        #nbytes = N * 4; cbytes = f.get_filesize()
        #cratio = nbytes / float(cbytes)
        #print("Compression ratio:   %.2fx" % cratio)

    if not args.write_only:
        t0 = time()
        if args.in_memory:
            h5a = f.root.carray[:]
            f.close()
        else:
            h5a = read_hdf5(fname)
        t = time() - t0
        print("Time to read %s:   %.3fs (%.2f GB/s)" % (
            fname, time() - t0, N * 4 / (2**30 * t)))
