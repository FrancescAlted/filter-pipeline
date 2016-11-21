/*
    To compile this program:

    h5cc blosc_filter.c c-bench.c -o c-bench -lblosc

    To run:

    $ ./c-bench -w
    Blosc version info: 1.11.1 ($Date:: 2016-09-03 #$)
    Time to create c-bench.h5: 0.397s (0.94 GB/s)
    Success!

    $ h5ls -v c-bench.h5
    Opened "c-bench.h5" with sec2 driver.
    dset                     Dataset {100/100, 100/100, 100/100, 100/100}
        Location:  1:800
        Links:     1
        Chunks:    {1, 100, 100, 100} 4000000 bytes
        Storage:   400000000 logical bytes, 2681398 allocated bytes, 14917.59% utilization
        Filter-0:  blosc-32001 OPT {2, 2, 4, 4000000, 9, 1, 0}
        Type:      native int

*/

#include <time.h>
#include <stdio.h>
#include <string.h>
#include "hdf5.h"
#include "blosc_filter.h"

#define SIZE 400 * 100 * 100 * 100
#define SHAPE {400, 100, 100, 100}
#define CHUNKSHAPE {1, 100, 100, 100}

int main(int argc, char* argv[]) {
  char mode[32];
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
  hid_t fid, sid, dset, plist;
  char usage[256];

  strncpy(usage, "Usage: c-bench [-r|-w] [nofilter] ", 32);
  if (argc < 2) {
    printf("%s\n", usage);
    exit(1);
  }

  strcpy(mode, argv[1]);
  //printf("mode: %s\n", mode);
  if ((strcmp(mode, "-w") != 0) && (strcmp(mode, "-r") != 0)) {
    printf("%s\n", usage);
    exit(2);
  }

  cd_values[6] = BLOSC_LZ4;  /* the default codec (you can change it with BLOSC_COMPRESSOR env var) */
  if ((argc == 3) && (strcmp(argv[2], "nofilter") == 0)) {
    cd_values[6] = -1;  /* no codec */
  }

  for (i = 0; i < SIZE; i++) {
    data[i] = i;
  }

  /* Register the filter with the library */
  r = register_blosc(&version, &date);
  printf("Blosc version info: %s (%s)\n", version, date);

  if (strcmp(mode, "-w") == 0) {
      start = clock();
      fid = H5Fcreate("c-bench.h5", H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
      sid = H5Screate_simple(4, shape, NULL);
      plist = H5Pcreate(H5P_DATASET_CREATE);

      /* Chunked layout required for filters */
      r = H5Pset_chunk(plist, 4, chunkshape);

      /* 0 to 3 (inclusive) param slots are reserved. */
      cd_values[4] = 5;       /* compression level */
      cd_values[5] = 1;       /* 0: shuffle not active, 1: shuffle active, 2: bitshuffle active */

      if (cd_values[6] == -1) {
        dset = H5Dcreate(fid, "dset", H5T_NATIVE_INT32, sid, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
      }
      else {
        r = H5Pset_filter(plist, FILTER_BLOSC, H5Z_FLAG_OPTIONAL, 7, cd_values);
        dset = H5Dcreate(fid, "dset", H5T_NATIVE_INT32, sid, H5P_DEFAULT, plist, H5P_DEFAULT);
      }

      r = H5Dwrite(dset, H5T_NATIVE_INT32, H5S_ALL, H5S_ALL, H5P_DEFAULT, &data);
      H5Dclose(dset);
      H5Sclose(sid);
      H5Fclose(fid);

      end = clock();
      cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
      printf("Time to create c-bench.h5: %.3fs (%.2f GB/s)\n", cpu_time_used,
             SIZE * sizeof(int) / (cpu_time_used * (1<<30)));
  }

  if (strcmp(mode, "-r") == 0) {
      start = clock();
      fid = H5Fopen("c-bench.h5", H5F_ACC_RDONLY, H5P_DEFAULT);
      dset = H5Dopen1(fid, "dset");

      r = H5Dread(dset, H5T_NATIVE_INT32, H5S_ALL, H5S_ALL, H5P_DEFAULT, &data_out);

      H5Dclose(dset);
      H5Fclose(fid);
      end = clock();
      cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
      printf("Time to read c-bench.h5:   %.3fs (%.2f GB/s)\n", cpu_time_used,
             SIZE * sizeof(int) / (cpu_time_used * (1<<30)));
  }

  fprintf(stdout, "Success!\n");
  return_code = 0;

  return return_code;
}
