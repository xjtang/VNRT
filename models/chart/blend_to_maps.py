""" Module for generating maps from blended results

    Args:
        -l (lc): modis land cover map, to fill in blank pixels
        -R (recursive): recursive when seaching files
        --overwrite: overwrite or not
        ori: origin
        des: destination
        img: an example image to get the spatial reference

"""
import os
import argparse
import numpy as np

from osgeo import gdal

from ...common import (log, get_files, show_progress, split_doy, ordinal_to_doy,
                        doy_to_ordinal)
from ...common import constants as cons
from ...io import stackGeo, array2stack, yatsm2records, stack2array


def get_blend(ori, des, img, lc='NA', overwrite=False, recursive=False):
    """ generate map from blended results

    Args:
        ori (str): place to look for inputs
        des (str): output path and filename
        img (str): path to example image
        lc (str): MODIS land cover stack
        overwrite (bool): overwrite or not
        recursive (bool): recursive when searching file, or not

    Returns:
        0: successful
        1: error due to des
        2: error when reading inputs
        3: nothing is processed
        4: error in writing output

    """
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(os.path.basename(des)))
        return 1

    # get image spatial reference
    log.info('Reading spatial reference from: {}'.format(img))
    try:
        geo = stackGeo(img)
    except:
        log.error('Failed to read spatial reference from {}'.format(img))
        return 2

    # read MODIS lc stack
    if lc != 'NA':
        log.info('Reading MODIS LC: {}'.format(lc))
        try:
            lc_stack = stack2array(lc)
            lc_stack = np.kron(lc_stack,np.ones((2,2,1))).astype(lc_stack.dtype)
        except:
            log.error('Failed to read MODIS LC: {}'.format(lc))
            return 2

    # initialize output
    log.info('Initializing output...')
    result = np.zeros((geo['lines'], geo['samples'], 16), np.int8) + 255
    count = 0

    # generate results
    log.info('Start generating map...')
    for i in range(0, geo['lines']):
        try:
            # locate line cache file
            yatsm = get_files(ori, 'yatsm_lc_r{}.npz'.format(i), recursive)
            # read line cache
            if len(yatsm) > 0:
                _line = yatsm2records(os.path.join(yatsm[0][0], yatsm[0][1]))
                for j in range(0, len(_line)):
                    px = _line[j]['px'][0]
                    result[i, px, :] = blend2map(_line[j])
                for j in range(0, geo['samples']):
                    if sum(result[i, j, :] == 255) == 16:
                        result[i, j, :] = np.bincount(lc_stack[i,j,:]).argmax()
                count += 1
            else:
                log.warning('Found no blended file for line {}'.format(i + 1))
            progress = show_progress(i + 1, geo['lines'], 5)
            if progress >= 0:
                log.info('{}% done.'.format(progress))
        except:
            log.warning('Failed to process line {}.'.format(i + 1))
            continue

    # see if anything is processed
    if count == 0:
        log.error('Nothing is processed.')
        return 3

    # write output
    log.info('Writing output to: {}'.format(des))
    bands = ['Blended Land Cover Map {}'.format(x) for x in range(2001, 2017)]
    if array2stack(result, geo, des, bands, 255, gdal.GDT_Byte, overwrite,
                    'GTiff', ['COMPRESS=PACKBITS']) > 0:
        log.error('Failed to write output to {}'.format(des))
        return 4

    # done
    log.info('Process completed.')
    log.info('{}/{} lines successful.'.format(count, geo['lines']))
    return 0


def blend2map(ts):
    map = np.zeros(2016 - 2001 + 1, np.int8) + 254
    if ordinal_to_doy(ts[0]['start']) > 2001270:
        ts = np.append(ts[0], ts)
        ts[0]['start'] = doy_to_ordinal(2001001)
        ts[0]['end'] = ts[1]['start']
    if ordinal_to_doy(ts[-1]['end']) < 2016001:
        ts = np.append(ts, ts[0])
        ts[-1]['start'] = ts[-2]['end']
        ts[-1]['end'] = doy_to_ordinal(2016365)
    for x in ts:
        _start = list(split_doy(ordinal_to_doy(x['start'])))
        _end = list(split_doy(ordinal_to_doy(x['end'])))
        if _start[1] > 270:
            _start[0] += 1
        for y in range(_start[0], _end[0] + 1):
            if y in range(2001, 2017):
                map[y - 2001] = x['class']
    return map


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--lc', action='store', type=str, dest='lc',
                        default='NA', help='modis land cover')
    parser.add_argument('-R', '--recursive', action='store_true',
                        help='recursive or not')
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='origin')
    parser.add_argument('des', default='./', help='destination')
    parser.add_argument('img', default='./', help='example image')
    args = parser.parse_args()

    # print logs
    log.info('Start generating map...')
    log.info('Blended files in {}'.format(args.ori))
    log.info('Saving as {}'.format(args.des))
    log.info('Copy spatial reference from {}'.format(args.img))
    if args.lc != 'NA':
        log.info('MODIS Land Cover: {}'.format(args.lc))
    if args.recursive:
        log.info('Recursive seaching.')
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to generatet maps from blended results
    get_blend(args.ori, args.des, args.img, args.lc, args.overwrite,
                args.recursive)
