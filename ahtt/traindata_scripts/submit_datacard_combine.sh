#!/bin/bash



###########################################################
#PARAMETERS:
#	masses, widths in the grid for which to calculate the Likelihood 
#	use the TAG variable to define the folder in ../data/ 
#	where the results will be stored
###########################################################
masses='m365,m380,m400,m425,m450,m475,m500,m525,m550,m575,m600,m625,m650,m675,m700,m725,m750,m775,m800,m825,m850,m875,m900,m925,m950,m975,m1000'
#masses='m500, m600'
#widths='w1p0,w2p5,w5p0,w10p0,w25p0'
widths='w2p5'
pairs="${masses};${widths};${masses};${widths}"
#N_JOB=400
TAG="allmasses_w2p5"

mkdir ./../data/${TAG}
mkdir ./../data/${TAG}/condor
mkdir ./../data/${TAG}/condor/errors
mkdir ./../data/${TAG}/condor/outputs
mkdir ./../data/${TAG}/condor/logs
cp template/condor.sub ./../data/${TAG}/
cp template/datacard_combine_local.sh ./../data/${TAG}/
sed -i -e "s|DIRE|${TAG}|g"  ./../data/${TAG}/condor.sub
sed -i -e "s|TAGGED|${TAG}|g"  ./../data/${TAG}/datacard_combine_local.sh
cd ../data/${TAG}/ 

#prepare the pairs array into an array with all permutations
# Split the pairs by semicolons
IFS=';' read -ra pair_arr <<< "$pairs"
# Get the length of the subarrays
for section in "${pair_arr[@]}"; do
    IFS=',' read -ra elements <<< "$section"
    element_count=${#elements[@]}
    subarray_length+=($element_count)
done

IFS=',' read -ra massarr <<< "$masses"
IFS=',' read -ra warr <<< "$widths"
# Create the expanded array
mixed_points=()
for ((i = 0; i < subarray_length[0]; i++)); do
    for ((j = 0; j < subarray_length[1]; j++)); do
	    for ((k = 0; k < subarray_length[2]; k++)); do
		    for ((l = 0; l < subarray_length[3]; l++)); do
			mixed_points+=("${massarr[i]};${warr[j]};${massarr[k]};${warr[l]}")
		done 
	done
    done
done
length=${#mixed_points[@]}
N_JOB=$((length / 2))
echo "gonna submit ${N_JOB} jobs"
# Convert the datapoints into the desired format
converted_points=()
for datapoint in "${mixed_points[@]}"; do
    IFS=';' read -ra values <<< "$datapoint"
    converted_points+=("A_${values[0]}_${values[1]},H_${values[2]}_${values[3]}")
done
# Get the length of the array
array_length=${#converted_points[@]}

# Calculate the subarray size
subarray_size=$(( array_length / N_JOB ))
remainder=$(( array_length % N_JOB ))
# Create the subarrays
subarrays=()
start=0
for ((i = 0; i < N_JOB; i++)); do
    mkdir subfold_${i}
    cp condor.sub subfold_${i}/
    cp datacard_combine_local.sh subfold_${i}/
    cd subfold_${i}
    subarray=()
    end=$(( start + subarray_size ))
    if [ $i -lt $remainder ]; then
        end=$(( end + 1 ))
    fi
    for ((j = start; j < end; j++)); do
        subarray+=("${converted_points[j]}")
    done
    for entry in "${subarray[@]}"; do
	    subarray+=";$entry"
    done
    subarray+=("${subarray:1}")
    pwd
    #echo ${subarray}
    #echo ${TAG}
    sed -i -e "s|PAIRS|${subarray}|g"  datacard_combine_local.sh
    sed -i -e "s|SUBFOLD|subfold_${i}|g"  condor.sub
    sed -i -e "s|SUBFOLD|subfold_${i}|g"  datacard_combine_local.sh
    #condor_submit PAIRS=${subarray} TAGS=${TAG} condor.sub 
    condor_submit  condor.sub 
    cd ..
    start=$end
done
