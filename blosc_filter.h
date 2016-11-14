/*
 * Dynamically loaded filter plugin for HDF5 blosc filter.
 * Copyright (C) 2016  The THG Group
 * Author: Francesc Alted
 * Date: 2016-09-27
 *
 */


#ifndef PLUGIN_BLOSC_H
#define PLUGIN_BLOSC_H

#ifdef __cplusplus
extern "C" {
#endif

#include "H5PLextern.h"
#include "blosc.h"

/* Version numbers */
#define BLOSC_PLUGIN_VERSION_MAJOR    1    /* for major interface/format changes  */
#define BLOSC_PLUGIN_VERSION_MINOR    0   /* for minor interface/format changes  */
#define BLOSC_PLUGIN_VERSION_RELEASE  0    /* for tweaks, bug-fixes, or development */

#define BLOSC_PLUGIN_VERSION_STRING   "1.0.0-dev"  /* string version.  Sync with above! */
#define BLOSC_PLUGIN_VERSION_DATE     "2016-09-03 #$"    /* date version */

/* Filter revision number, starting at 1 */
/* #define FILTER_BLOSC_VERSION 1 */
#define FILTER_BLOSC_VERSION 2  /* multiple compressors since Blosc 1.3 */

/* Filter ID registered with the HDF Group */
#define FILTER_BLOSC 32001

/* Register the filter with the HDF5 library. */
#if defined(_MSC_VER)
__declspec(dllexport)
#endif	/* defined(_MSC_VER) */

BLOSC_EXPORT H5PL_type_t H5PLget_plugin_type(void);
BLOSC_EXPORT const void* H5PLget_plugin_info(void);

BLOSC_EXPORT int register_blosc(char **version, char **date);

BLOSC_EXPORT herr_t blosc_set_local(hid_t dcpl, hid_t type, hid_t space);

BLOSC_EXPORT size_t blosc_filter(unsigned flags, size_t cd_nelmts,
                                 const unsigned cd_values[], size_t nbytes,
                                 size_t* buf_size, void** buf);

#ifdef __cplusplus
}
#endif

#endif    // PLUGIN_BLOSC_H
