from __future__ import print_function

import sys
from time import time
import numpy as np
import tables


N = int(1e8)
a = np.arange(N, dtype=np.int32).reshape(100, 100, 100, 100)

def create_hdf5(fname, codec, inmemory):
    if codec != 'None':
        filters = tables.Filters(complevel=9, complib="%s" % codec)
    else:
        filters = None
    if inmemory:
        f = tables.open_file(fname, "w", pytables_sys_attrs=False, driver="H5FD_CORE")
        f.create_carray(f.root, 'carray', filters=filters, obj=a,
                        chunkshape=(1, 100, 100, 100))
        return f
    else:
        with tables.open_file(fname, "w", pytables_sys_attrs=False) as f:
            f.create_carray(f.root, 'carray', filters=filters, obj=a,
                            chunkshape=(1, 100, 100, 100))
        return None

def read_hdf5(fname):
    with tables.open_file(fname, "r") as f:
        return f.root.carray[:]


print("-=" * 38)
print("PyTables version:     %s" % tables.__version__)
tinfo = tables.which_lib_version("blosc")
blosc_date = tinfo[2].split()[1]
print("Blosc version:       %s (%s)" % (tinfo[1], blosc_date))
blosc_cinfo = tables.blosc_get_complib_info()
blosc_cinfo = [
    "%s (%s)" % (k, v[1]) for k, v in sorted(blosc_cinfo.items())
    ]

if __name__ == "__main__":
    fname = sys.argv[0].replace(".py", ".h5")
    codec = sys.argv[1]
    if (len(sys.argv) > 2):
        inmemory = sys.argv[2]
        print("Working in-memory!")
    else:
        inmemory = False

    t0 = time()
    f = create_hdf5(fname, codec, inmemory)
    t = time() - t0
    print("Time to create %s: %.3fs (%.2f GB/s)" % (
        fname, t, a.size * a.itemsize / (2**30 * t)))
    #nbytes = N * 4; cbytes = f.get_filesize()
    #cratio = nbytes / float(cbytes)
    #print("Compression ratio:   %.2fx" % cratio)

    t0 = time()
    if inmemory:
        h5a = f.root.carray[:]
        f.close()
    else:
        h5a = read_hdf5(fname)
    t = time() - t0
    print("Time to read %s:   %.3fs (%.2f GB/s)" % (
        fname, time() - t0, a.size * a.itemsize / (2**30 * t)))
