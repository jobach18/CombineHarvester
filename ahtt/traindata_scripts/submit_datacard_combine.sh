#!/bin/bash
masses='m400,m500,m650,m800,m1000'
widths='w1p0,w2p5,w5p0,w10p0,w25p0'
pairs="${masses};${widths};${masses};${widths}"
N_JOB=10
TAG="try"

mkdir ./../${TAG}
mkdir ./../${TAG}/condor
mkdir ./../${TAG}/condor/errors
mkdir ./../${TAG}/condor/outputs
mkdir ./../${TAG}/condor/logs
cp template/condor.sub ./../${TAG}/
sed -i -e "s|SUBMITDIR|${TAG}|g"  ./../condor.sub
cp template/datacard_combine_local.sh ./../${TAG}/
cd ./../${TAG}/ 

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
    condor_submit PAIRS=subarray TAG=${TAG} condor.sub 
    start=$end
done
