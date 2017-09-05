""" Module for commonly used constants
"""
# common
NODATA = -9999
SCALE_FACTOR = 10000

# images
IMGBIT = 255
MASK_COLOR = (IMGBIT, 0, 0)
RESULT_MIN = 2012000

# VIIRS
SR_BANDS = (23, 24, 25)
QA_BANDS = (13, 14, 16, 18, 19)
VZA_BAND = 1

# download
_HTTP = 'https://e4ftl01.cr.usgs.gov/'
_FTP = 'ftp://ladsweb.nascom.nasa.gov/'
CHUNK = 1024*1024
