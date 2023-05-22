#!/bin/bash

#HTCONDOR                                                                                                                   
if [ -z "$1" ] ; then
    echo "Need to get job number!"
    exit 0
fi
#source /nfs/dust/cms/user/bachjoer/pepper_jorn/pepper-master/example/environment.sh
cd ../data/$3
python3 extra_and_writetopandas.py  -id $1 -js $2 -tag $3 -exp $4
