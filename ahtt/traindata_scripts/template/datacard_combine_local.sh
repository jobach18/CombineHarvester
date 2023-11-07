#!/bin/bash
#bash script that takes at $1 the datapoint as an input and produced the datacard and runs combine on that card
#$2 input is the tag of the run
tag="TAGGED"
pairs="PAIRS"
echo "inputs:"
echo ${pairs[@]}
source /nfs/dust/cms/user/afiqaize/cms/sft/condor/condorUtil.sh
source /afs/desy.de/user/b/bachjoer/.bashrc 
#conda activate train
#cmsenv
cd /nfs/dust/cms/user/bachjoer/ml-workspace/learn_likelihood/CMSSW_10_2_13/src/CombineHarvester/ahtt/data/${tag[@]}/SUBFOLD/
cmsenv
pwd 
channels='ee,em,mm,e3j,e4pj,m3j,m4pj'
years='2016pre,2016post,2017,2018'
ntoy='0'
idxs='..25'
#exps='exp-b,exp-s,exp-01,exp-10'
exps='exp-s'
keeps='eff_b,eff_e,eff_m_id,eff_m_iso,eff_trigger,fake,JEC,JER,MET,QCDscale,hdamp,tmass,EWK,alphaS,PDF_PCA_0,L1,EWQCD,pileup,lumi,norm,UEtune,CR_ERD,CR_QCD'
drops='Type3,FlavorQCD_201,TT_norm'
NGPOINTS='20'
NGINT='1,1.5;1,1.5'

#python3 /nfs/dust/cms/user/bachjoer/ml-workspace/learn_likelihood/CMSSW_10_2_13/src/CombineHarvester/ahtt/scripts/submit_twin.py --mode 'datacard,validate' --point "${pairs}" --sushi-kfactor --lnN-under-threshold --year "${years}" --channel "${channels}" --tag "${tag}" --keep "${keeps}" --drop "${drops}" --local 
 ../../../scripts/submit_twin.py --mode 'datacard,validate' --point "${pairs}" --sushi-kfactor --lnN-under-threshold --year "${years}" --channel "${channels}" --tag "${tag}" --keep "${keeps}" --drop "${drops}" --local --exclude-process "EtaT"  
#python3 /nfs/dust/cms/user/bachjoer/ml-workspace/learn_likelihood/CMSSW_10_2_13/src/CombineHarvester/ahtt/scripts/submit_twin.py --mode contour --point "${pairs}" --tag "${tag}" --g-values '1.0,1.0' --fc-expect "${exps}" --n-toy 0 --fc-single-point --extra-option='--saveNLL --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --saveSpecifiedNuis=all' --local 
../../../scripts/submit_twin.py --mode 'nll' --point "${pairs}" --tag "${tag}" --nll-expect "${exps}" --n-toy 0 --nll-parameter "g1,g2" --nll-npoint "${NGPOINTS},${NGPOINTS}" --nll-interval=${NGINT} --extra-option="--saveSpecifiedNuis=all" --local  --exclude-process "EtaT"
# ../../../scripts/submit_twin.py --mode contour --point "${pairs}" --tag "${tag}" --g-values '1.0,1.0' --fc-expect "${exps}" --n-toy 0 --fc-single-point --extra-option='--saveNLL --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --saveSpecifiedNuis=all' --local 
