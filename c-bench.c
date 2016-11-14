/*
    To compile this program:

    h5cc blosc_filter.c c-bench.c -o c-bench -lblosc

    To run:

    $ ./c-bench
    Blosc version info: 1.3.0 ($Date:: 2014-01-11 #$)
    Success!
    $ h5ls -v c-bench .h5
    Opened "example.h5" with sec2 driver.
    dset                     Dataset {100/100, 100/100, 100/100}
        Location:  1:800
        Links:     1
        Chunks:    {1, 100, 100} 40000 bytes
        Storage:   4000000 logical bytes, 126002 allocated bytes, 3174.55% utilization
        Filter-0:  blosc-32001 OPT {2, 2, 4, 40000, 4, 1, 2}
        Type:      native float

*/

#include <time.h>
#include <stdio.h>
#include "hdf5.h"
#include "blosc_filter.h"

#define SIZE 100 * 100 * 100 * 100
#define SHAPE {100, 100, 100, 100}
#define CHUNKSHAPE {1, 100, 100, 100}

int main() {
  static int data[SIZE];
  static int data_out[SIZE];
  const hsize_t shape[] = SHAPE;
  const hsize_t chunkshape[] = CHUNKSHAPE;
  char* version, * date;
  int r, i;
  unsigned int cd_values[7];
  int return_code = 1;
  clock_t start, end;
  double cpu_time_used;

  hid_t fid, sid, dset, plist = 0;

  for (i = 0; i < SIZE; i++) {
    data[i] = i;
  }

  /* Register the filter with the library */
  r = register_blosc(&version, &date);
  printf("Blosc version info: %s (%s)\n", version, date);

  start = clock();
  fid = H5Fcreate("c-bench.h5", H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
  sid = H5Screate_simple(4, shape, NULL);
  plist = H5Pcreate(H5P_DATASET_CREATE);

  /* Chunked layout required for filters */
  r = H5Pset_chunk(plist, 4, chunkshape);

  /* 0 to 3 (inclusive) param slots are reserved. */
  //cd_values[4] = 0;       /* compression level */
  cd_values[4] = 9;       /* compression level */
  cd_values[5] = 1;       /* 0: shuffle not active, 1: shuffle active, 2: bitshuffle active */
  cd_values[6] = BLOSC_BLOSCLZ; /* the actual compressor to use */

  /* Set the filter with 7 params */
  r = H5Pset_filter(plist, FILTER_BLOSC, H5Z_FLAG_OPTIONAL, 7, cd_values);
  //dset = H5Dcreate(fid, "dset", H5T_NATIVE_INT32, sid, H5P_DEFAULT, plist, H5P_DEFAULT);
  dset = H5Dcreate(fid, "dset", H5T_NATIVE_INT32, sid, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);

  r = H5Dwrite(dset, H5T_NATIVE_INT32, H5S_ALL, H5S_ALL, H5P_DEFAULT, &data);
  H5Dclose(dset);
  H5Sclose(sid);
  H5Fclose(fid);

  end = clock();
  cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
  printf("Time to create an HDF5 file: %.3fs (%.2f GB/s)\n", cpu_time_used,
         SIZE * sizeof(int) / (cpu_time_used * (1<<30)));

  start = clock();
  fid = H5Fopen("c-bench.h5", H5F_ACC_RDONLY, H5P_DEFAULT);
  dset = H5Dopen1(fid, "dset");

  r = H5Dread(dset, H5T_NATIVE_INT32, H5S_ALL, H5S_ALL, H5P_DEFAULT, &data_out);

  H5Dclose(dset);
  H5Fclose(fid);
  end = clock();
  cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
  printf("Time to read an HDF5 file: %.3fs (%.2f GB/s)\n", cpu_time_used,
         SIZE * sizeof(int) / (cpu_time_used * (1<<30)));

//  for (i = 0; i < SIZE; i++) {
//    if (data[i] != data_out[i]) printf("Data written and read are not equal!");
//  }

  fprintf(stdout, "Success!\n");

  return_code = 0;

  return return_code;
}
