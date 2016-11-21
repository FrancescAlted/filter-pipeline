Title:  About HDF5 filter pipeline performance
Author: Francesc Alted
Date:   November 21, 2016 

About HDF5 filter pipeline performance
======================================

TL;DR;

It has been found that the HDF5 filter pipeline requires an additional
memcpy() operation per chunk.  This adds a noticeable overhead, and most
importantly, could slowdown multithreaded operations.

Introduction
------------

HDF5 has a powerful filter capability that allows to apply different
algorithms to every chunk of a chunked dataset.  However, due to how
the API has been designed, this needs an additional memcpy() in order
to transfer the filtered data to the final containers.  Whereas
a memcpy() might seem to represent a small performance penalty it can be
as high as a 20%.

In the following sections I'll be presenting a series of benchmarks
demonstrating this effect, and will present an alternative API
that would get rid of the additional memcpy() that is currently
required.

bcolz and a comparison with HDF5
--------------------------------

bcolz (bcolz.blosc.org) is a simple dataset container written in Python.
As it comes with a single Blosc filter that can read and write directly
to final containers that are returned to users, I'll be using it for
comparison purposes with the filter pipeline in HDF5.

PyTables as a 'good enough' tool for HDF5 benchmarking
------------------------------------------------------

PyTables is a Python wrapper to the HDF5 library, and it will be used
as a replacement of C benchmarks because its performance is quite
similar for our purposes (except for multithreading, see below).

For example, for creating files (-w flag):

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

we can see that both PyTables and a pure C program have similar
performance.  And the same goes for reading (-r flag):

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
hyperthreading.  All the benchmarking scripts and code can be found in
[this repo](https://github.com/FrancescAlted/filter-pipeline).

The problem is not in chunking
------------------------------

To show that the memcpy() overhead at hand occurs only during filter
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

so, times for creation and read are pretty much comparable for this case.

The memcpy() overhead in HDF5 filter pipeline
---------------------------------------------

Here we are going to compare the HDF5 filter pipeline performance using
the Blosc filter with the bcolz package that also uses Blosc as (the
only) filter:

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
memcpy().  In the figure below there is a profile (made with valgrind)
showing how memcpy() is called a lot after the filter has finished (400
times, i.e. once per chunk):

![Figure1](https://github.com/FrancescAlted/filter-pipeline/blob/master/report/pytables-bench-blosc5-r.png)

Effect of memcpy() when using a filter that supports multithreading
-------------------------------------------------------------------

The 1 additional memcpy() call per chunk continues to affect with the
number of threads.  Here it is an example:

```
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 python pytables-bench.py -r
Time to read pytables-bench.h5:   0.497s (3.00 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=2 python pytables-bench.py -r
Time to read pytables-bench.h5:   0.417s (3.57 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=3 python pytables-bench.py -r
Time to read pytables-bench.h5:   0.352s (4.23 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=4 python pytables-bench.py -r
Time to read pytables-bench.h5:   0.330s (4.51 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=5 python pytables-bench.py -r
Time to read pytables-bench.h5:   0.310s (4.81 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=6 python pytables-bench.py -r
Time to read pytables-bench.h5:   0.308s (4.84 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=7 python pytables-bench.py -r
Time to read pytables-bench.h5:   0.324s (4.60 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=8 python pytables-bench.py -r
Time to read pytables-bench.h5:   0.359s (4.15 GB/s)
```

```
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 python bcolz-bench.py -r
Time to read bcolz-bench.bcolz:   0.427s (3.49 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=2 python bcolz-bench.py -r
Time to read bcolz-bench.bcolz:   0.317s (4.70 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=3 python bcolz-bench.py -r
Time to read bcolz-bench.bcolz:   0.256s (5.82 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=4 python bcolz-bench.py -r
Time to read bcolz-bench.bcolz:   0.268s (5.56 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=5 python bcolz-bench.py -r
Time to read bcolz-bench.bcolz:   0.294s (5.08 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=6 python bcolz-bench.py -r
Time to read bcolz-bench.bcolz:   0.326s (4.57 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=8 python bcolz-bench.py -r
Time to read bcolz-bench.bcolz:   0.353s (4.22 GB/s)
```

so, one can see that Blosc achieves best performance with less threads
(3 vs 6) while continues to get a 15% of performance advantage (at 
maximum speeds).

Perhaps more interestingly, the pure C benchmark (using the same HDF5
and Blosc libraries) shows much worse scalability than PyTables:

```
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 ./c-bench -r
Time to read c-bench.h5:   0.537s (2.77 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=2 ./c-bench -r
Time to read c-bench.h5:   0.614s (2.43 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=3 ./c-bench -r
Time to read c-bench.h5:   0.684s (2.18 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=4 ./c-bench -r
Time to read c-bench.h5:   0.715s (2.08 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=5 ./c-bench -r
Time to read c-bench.h5:   0.812s (1.83 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=6 ./c-bench -r
Time to read c-bench.h5:   0.891s (1.67 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=7 ./c-bench -r
Time to read c-bench.h5:   0.966s (1.54 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=8 ./c-bench -r
Time to read c-bench.h5:   0.903s (1.65 GB/s)
```

Why the performance of the C-based benchmark drops as we add more
threads into the task is still unknown, as both the C and PyTables
benchmarks use the very same Blosc filter.  This deserves more study
indeed.

In-memory operation
-------------------

HDF5 can operate with in-memory data (via the 'H5FD_CORE' driver).  This
allows to get rid of any I/O overhead and is useful to see the actual
overhead of the different filters.
  
Let's see how HDF5 performs in this case:

```
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 python pytables-bench.py blosc -m
Time to create pytables-bench.h5: 0.395s (3.77 GB/s)
Time to read pytables-bench.h5:   0.493s (3.02 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=2 python pytables-bench.py blosc -m
Time to create pytables-bench.h5: 0.362s (4.11 GB/s)
Time to read pytables-bench.h5:   0.397s (3.76 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=3 python pytables-bench.py blosc -m
Time to create pytables-bench.h5: 0.299s (4.98 GB/s)
Time to read pytables-bench.h5:   0.342s (4.36 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=4 python pytables-bench.py blosc -m
Time to create pytables-bench.h5: 0.301s (4.95 GB/s)
Time to read pytables-bench.h5:   0.336s (4.43 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=5 python pytables-bench.py blosc -m
Time to create pytables-bench.h5: 0.272s (5.47 GB/s)
Time to read pytables-bench.h5:   0.315s (4.73 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=6 python pytables-bench.py blosc -m
Time to create pytables-bench.h5: 0.275s (5.42 GB/s)
Time to read pytables-bench.h5:   0.344s (4.33 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=7 python pytables-bench.py blosc -m
Time to create pytables-bench.h5: 0.275s (5.43 GB/s)
Time to read pytables-bench.h5:   0.301s (4.96 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=8 python pytables-bench.py blosc -m
Time to create pytables-bench.h5: 0.271s (5.51 GB/s)
Time to read pytables-bench.h5:   0.309s (4.82 GB/s)
```

and now, bcolz using the in-memory containers:

```
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=1 python bcolz-bench.py  -m
Time to create None: 0.254s (5.87 GB/s)
Time to read None:   0.397s (3.75 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=2 python bcolz-bench.py  -m
Time to create None: 0.188s (7.94 GB/s)
Time to read None:   0.268s (5.56 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=3 python bcolz-bench.py  -m
Time to create None: 0.131s (11.37 GB/s)
Time to read None:   0.221s (6.74 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=4 python bcolz-bench.py  -m
Time to create None: 0.105s (14.15 GB/s)
Time to read None:   0.212s (7.03 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=5 python bcolz-bench.py  -m
Time to create None: 0.091s (16.42 GB/s)
Time to read None:   0.248s (6.02 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=6 python bcolz-bench.py  -m
Time to create None: 0.094s (15.85 GB/s)
Time to read None:   0.269s (5.55 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=7 python bcolz-bench.py  -m
Time to create None: 0.112s (13.30 GB/s)
Time to read None:   0.300s (4.97 GB/s)
francesc@francesc:~/filter-pipeline$ BLOSC_NTHREADS=8 python bcolz-bench.py  -m
Time to create None: 0.088s (16.92 GB/s)
Time to read None:   0.336s (4.44 GB/s)
```

So, we can see that, due to the absence of the memcpy() calls, bcolz
can perform up to a 40% faster than HDF5 for reads (peaks of 7 GB/s vs
5 GB/s).  On its part, writes in bcolz can be up to 3x faster than HDF5
(17 GB/s vs 5.5 GB/s).

The reason for this (rather huge) latter difference is currently
unknown, but it would be nice to do some profiling for the writes and
see where the bottleneck for HDF5 is (I don't think the additional
memcpy() would be the only responsible for that).

Proposal for getting rid of the memcpy() overhead in the pipeline
-----------------------------------------------------------------

The current API for the filter pipeline goes like this:

```
size_t XXX_filter(unsigned flags, size_t cd_nelmts,
                  const unsigned cd_values[], size_t nbytes,
                  size_t *buf_size, void **buf)
```

so, clearly the outcome of the filter has to be malloc'ed internally.
With that, a copy would be needed to populate the user data passed
in read functions (e.g. `H5Dread()`).

The proposal is to add a new API that would allow to pass the
destination buffer.  Something along these lines:

```
size_t XXX_filter2(unsigned flags, size_t cd_nelmts,
                   const unsigned cd_values[], size_t nbytes,
                   size_t *inbuf_size, void **inbuf,
                   size_t *outbuf_size, void **outbuf)
```

Then, in the situations that allow that (e.g. `H5Dread()`) HDF5 would
automatically pass the destination buffer to the `XXX_filter2()`
function.  In case this is not possible, then passing `0` and `NULL`
to `outbut_size` and `outbuf` respectively would indicate that the
user should malloc the destination herself.

Probably adding this new API would represent a fairly large rewrite of
the HDF5 filter pipeline, but if HDF5 would like to continue considered
a high performance library for I/O, this would be a most welcome
addition.
