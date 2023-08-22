#!/bin/bash

#HTCONDOR                                                                                                                   
if [ -z "$1" ] ; then
    echo "Need to get job number!"
    exit 0
fi
source /nfs/dust/cms/user/afiqaize/cms/sft/condor/condorUtil.sh
source /afs/desy.de/user/b/bachjoer/.bashrc 
conda activate train
#source /nfs/dust/cms/user/bachjoer/pepper_jorn/pepper-master/example/environment.sh
cd /nfs/dust/cms/user/bachjoer/ml-workspace/learn_likelihood/CMSSW_10_2_13/src/CombineHarvester/ahtt/data/$3
cmsenv
python3 extra_and_writetopandas_NP.py  -id $1 -js $2 -tag $3 -exp $4 -m "nll"
