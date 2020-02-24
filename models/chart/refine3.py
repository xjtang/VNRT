""" Module for refining classification results

    Args:
        --overwrite: overwrite or not
        ori: origin
        lc: MODIS land cover
        des: destination

"""
import os
import argparse
import numpy as np

from osgeo import gdal

from ...common import log, get_files, show_progress
from ...io import stack2array, stackGeo, array2stack


def refine_results(ori, lc, des, overwrite=False):
    """ refine classification results

    Args:
        ori (str): path and filename of classification results
        lc (str): path and filename of MODIS land cover maps
        des (str): place to save output map
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error when reading inputs
        3: error during processing
        4: error writing output

    """
    m2c = [0,2,2,4,4,5,10,10,9,9,10,11,12,13,12,16,16,25,0,0,0,0,0,0,0,0,0,0,0]
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(os.path.basename(des)))
        return 1

    # read input image
    log.info('Reading input maps...')
    try:
        r = stack2array(ori)
        lc = stack2array(lc)
        lc = np.kron(lc, np.ones((2,2,1))).astype(lc.dtype)
    except:
        log.error('Failed to read input maps.')
        return 2

    # read geo info
    log.info('Reading geo information...')
    try:
        geo = stackGeo(ori)
    except:
        log.error('Failed to read geo info.')
        return 2

    # refine classification results
    log.info('Refining maps...')
    try:
        (lines, samples, nband) = r.shape
        for i in range(0,lines):
            for j in range(0, samples):
                p = r[i, j, :]
                p_class = np.unique(p)[0]

                plc = lc[i, j, 0:16]
                plc_label = np.bincount(plc).argmax()
                plcn = len(np.unique(plc))

                # deel with unclassified
                if max(p == 0) == 1:
                    uclc = plc[p == 0]
                    p_label = m2c[np.bincount(uclc).argmax()]
                    # mostly uc
                    if sum(p == 0) > 10:
                        p[p == 0] = p_label
                    # uc in the beginning
                    elif (p[0] == 0):
                        if p_label in [13, 25]:
                            p[p == 0] = p_label
                        else:
                            p[p == 0] = p[p != 0][0]
                    # uc in the end
                    elif p[-1] == 0:
                        if p_label in [13, 25]:
                            p[p == 0] = p_label
                        else:
                            p[p == 0] = p[p != 0][-1]
                    # single uc
                    elif sum(p == 0) < 3:
                        for k in range(0, len(p)):
                            if p[k] == 0:
                                p[k] = p[k - 1]
                    r[i, j, :] = p

                # fix short plantation in beginning
                if p[3] != 18:
                    if p[0] == 18:
                        p[0] = p[3]
                    if p[1] == 18:
                        p[1] = p[3]
                    if p[2] == 18:
                        p[2] = p[3]
                    r[i, j, :] = p

                # urban barren fix
                if sum((p == 13) & (plc == 16)) >= 5:
                    p[(p == 13) & (plc == 16)] = 16
                    r[i, j, :] = p
                # urban grassland fix
                if sum((p == 13) & (plc == 10)) >= 5:
                    p[(p == 13) & (plc == 10)] = 10
                    r[i, j, :] = p

                # urban check 2
                if sum((p == 13) & (plc != 13)) >= 8:
                    if plc_label == 10:
                        p[(p == 13) & (plc != 13)] = 10
                    elif plc_label == 12:
                        p[(p == 13) & (plc != 13)] = 12
                    r[i, j, :] = p

                # fix urban to ag
                if (p[0] == 13) & (p[-1] == 12):
                    plc_short = np.bincount(plc[p == 13]).argmax()
                    p[p == 13] = m2c[plc_short]
                    r[i, j, :] = p

            progress = show_progress(i, lines, 5)
            if progress >= 0:
                log.info('{}% done.'.format(progress))
    except:
        log.error('Failed to refine results.')
        return 3

    # write output
    log.info('Writing output...')
    try:
        array2stack(r, geo, des, 'NA', 255, gdal.GDT_Int16, overwrite, 'GTiff',
                    ['COMPRESS=LZW'])
    except:
        log.error('Failed to write output to {}'.format(des))
        return 4

    # done
    log.info('Process completed.')
    return 0


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='classification results')
    parser.add_argument('lc', default='./', help='MODIS land cover maps')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start comparing...')
    log.info('Classification results: {}'.format(args.ori))
    log.info('MODIS land cover: {}'.format(args.lc))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to refine classification results
    refine_results(args.ori, args.lc, args.des, args.overwrite)