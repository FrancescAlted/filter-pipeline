Title:  About HDF5 filter pipeline performance
Author: Francesc Alted
Date:   November 21, 2016 

About HDF5 filter pipeline performance
======================================

TL;DR;

It has been found that the HDF5 filter pipeline requires an additional
memcpy operation per chunk.  This adds a noticeable overhead, specially
on read operations, and most importantly, slowdown multithreaded
operations.

Introduction
------------

HDF5 has a powerful filter capability that allows to apply different
algorithms to every chunk of a chunked dataset.  However, due to how
the API has been designed, this needs an additional memcpy() in order
to transfer the filtered data to the final containers.  Whereas
a memcpy() might seem to represent a small performance penalty, it has
important implications when trying to accelerate the filter operation
with multithreading.

In the following sections I'll be presenting a series of benchmarks
demonstrating this effect, and then will present an alternative API
that would get rid of the additional memcpy() that is currently
required.

bcolz and a comparison with HDF5
--------------------------------

bcolz (bcolz.blosc.org) is a simple dataset container written in Python.
As it comes with a single Blosc filter that can read and write directly
to final containers that are returned to users, I'll be using it for
comparison purposes with the filter implementation in HDF5.

PyTables as a 'good enough' tool for HDF5 benchmarking
------------------------------------------------------

PyTables is a Python wrapper to part of the functionality of the HDF5
library, and it will be used as a replacement of C benchmarks because
its performance is quite similar for our purposes.

For example, for creating files (-w flag) we see similar performance:

```
francesc@francesc:~/filter-pipeline$ rm c-bench.h5; BLOSC_NTHREADS=1 ./c-bench -w
HDF5 library version: 1.8.17
Blosc version info: 1.11.1 ($Date:: 2016-09-03 #$)
Time to create c-bench.h5: 0.542s (2.75 GB/s)
Success!
francesc@francesc:~/filter-pipeline$ rm pytables-bench.h5 ; BLOSC_NTHREADS=1 python pytables-bench.py blosc -w
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
PyTables version:     3.3.1-dev0
HDF5 version:        1.8.17
Blosc version:       1.11.1 (2016-09-03)
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
Time to create pytables-bench.h5: 0.543s (2.74 GB/s)
francesc@francesc:~/filter-pipeline$ ll -h *.h5
-rw-rw-r-- 1 francesc francesc 26M Nov 21 11:02 c-bench.h5
-rw-rw-r-- 1 francesc francesc 26M Nov 21 11:16 pytables-bench.h5
```

and the same goes for reading (-r flag):

```
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 ./c-bench -r
HDF5 library version: 1.8.17
Blosc version info: 1.11.1 ($Date:: 2016-09-03 #$)
Time to read c-bench.h5:   0.508s (2.93 GB/s)
Success!
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 python pytables-bench.py blosc -r
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
PyTables version:     3.3.1-dev0
HDF5 version:        1.8.17
Blosc version:       1.11.1 (2016-09-03)
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
Time to read pytables-bench.h5:   0.494s (3.02 GB/s)
```

Hardware and software used
--------------------------

Most of the benchmarks presented here are made in a Ubuntu 16.04 server
with an Intel Xeon E3-1245 v5 @ 3.50GHz with 4 physical cores with
hyperthreading.  Also, some profilings will be presented on a Ubuntu
16.04 laptop with an Intel i5-3380M @ 2.90GHz.  All the benchmarking
scripts and code can be found in [this repo](https://github.com/FrancescAlted/filter-pipeline).

The problem is not in chunking
------------------------------

To show that the memcpy() overhead at hand occurs during filter
operation, look at the time that it takes to create and read a
contiguous dataset in comparison with a chunked dataset with no filters:

```
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 python pytables-bench.py cont -w
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
PyTables version:     3.3.1-dev0
HDF5 version:        1.8.17
Blosc version:       1.11.1 (2016-09-03)
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
Using Dataset with no chunks!
Time to create pytables-bench.h5: 0.424s (3.51 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 python pytables-bench.py cont -r
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
PyTables version:     3.3.1-dev0
HDF5 version:        1.8.17
Blosc version:       1.11.1 (2016-09-03)
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
Using Dataset with no chunks!
Time to read pytables-bench.h5:   0.264s (5.65 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 python pytables-bench.py nofilter -w
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
PyTables version:     3.3.1-dev0
HDF5 version:        1.8.17
Blosc version:       1.11.1 (2016-09-03)
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
Time to create pytables-bench.h5: 0.416s (3.58 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 python pytables-bench.py nofilter -r
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
PyTables version:     3.3.1-dev0
HDF5 version:        1.8.17
Blosc version:       1.11.1 (2016-09-03)
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
Time to read pytables-bench.h5:   0.256s (5.81 GB/s)
```

so, times for creation and read are pretty much comparable.

The memcpy() overhead in HDF5 filter pipeline
---------------------------------------------

Here we are going to compare the HDF5 filter pipeline performance using
the Blosc filter with the bcolz package that also uses Blosc as a
filter:

```
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 python pytables-bench.py blosc -w
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
PyTables version:     3.3.1-dev0
HDF5 version:        1.8.17
Blosc version:       1.11.1 (2016-09-03)
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
Time to create pytables-bench.h5: 0.532s (2.80 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 python bcolz-bench.py -w
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
bcolz version:     1.1.1.dev16
Blosc version:     1.11.1 ($Date:: 2016-09-03 #$)
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
Time to create bcolz-bench.bcolz: 0.275s (5.41 GB/s)
```

Here we see that HDF5 takes quite more time (almost 2x) to create
a dataset.  Of course, not all the overhead is coming from the
additional memcpy() in the HDF5 filter pipeline, although part of it is.

But as HDF5 is mostly a WORM (Write Once, Read Multiple) library, we
are more interested in seeing the kind of overhead that the HDF5 filter
pipeline introduces:

```
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 python pytables-bench.py blosc -r
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
PyTables version:     3.3.1-dev0
HDF5 version:        1.8.17
Blosc version:       1.11.1 (2016-09-03)
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
Time to read pytables-bench.h5:   0.488s (3.05 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 python bcolz-bench.py -r
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
bcolz version:     1.1.1.dev16
Blosc version:     1.11.1 ($Date:: 2016-09-03 #$)
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
Time to read bcolz-bench.bcolz:   0.411s (3.63 GB/s)
```

so, the HDF5 filter pipeline is showing a 20% of slowdown compared with
a package using a filter pipepline that does not require the additional
memcpy().  ![Figure1][Figure1] is a profile (made with valgrind) showing how
memcpy() is called a lot after the filter has finished.

[Figure1]: 

