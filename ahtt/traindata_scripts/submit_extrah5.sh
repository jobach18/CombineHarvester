#!/bin/bash
if [ -z "$1" ]
then
	echo "usage: $1: #JOBS, $2: TAG, $3: Exp-s or Exp-b"
else
	cp template_extra/* ../data/$2/
	cd ../data/$2/
	condor_submit JOBS=$1 TAG=$2 EXP=$3 condor_extra.sub 
fi
