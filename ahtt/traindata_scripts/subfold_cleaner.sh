#!/bin/bash

root_folder="/nfs/dust/cms/user/bachjoer/ml-workspace/learn_likelihood/CMSSW_10_2_13/src/CombineHarvester/ahtt/data/$1/"

# Find all directories starting with "subfold_" in the root folder
directories=$(find "$root_folder" -type d -name 'subfold_*')
echo $directories

# Iterate through each directory and delete the specified files
for dir in $directories; do
  echo "Processing directory: $dir"
  cd "$dir" || continue
  subdirectories=$(find $dir -type d -name 'A_*')
  for subdir in $subdirectories; do
	  cd $subdir
	      rm *.txt
	      rm *.root
	      rm *.json
	      rm twin_*
          cd ..
    	  done
done

