#!/bin/bash

# bash script to merge image with masks

# Input Arguments:
#		-p searching pattern
#		-n number of jobs
#		-R recursive
#		--overwrite overwrite
#		ori: origin
#		mask: mask source
#		des: destination

# default values
pattern=S30*tif
njob=1
overwrite=''
recursive=''

# parse input arguments
while [[ $# > 0 ]]; do
	InArg="$1"
	case $InArg in
		-p)
			pattern=$2
			shift
			;;
		-n)
			njob=$2
			shift
			;;
		-R)
			recursive='-R '
			;;
		--overwrite)
			overwrite='--overwrite '
			;;
		*)
      ori=$1
      mask=$2
			des=$3
			break
	esac
	shift
done

# submit jobs
echo 'Total jobs to submit is' $njob
for i in $(seq 1 $njob); do
    echo 'Submitting job no.' $i 'out of' $njob
    qsub -j y -N HLS_$i -V -b y cd /projectnb/landsat/users/xjtang/documents/';' python -m SIPH.models.hls.mask_merge ${overwrite}${recursive}-p $pattern -b $i $njob $ori $mask $des
done
