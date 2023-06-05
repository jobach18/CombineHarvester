#!/bin/bash

# Check if the number of arguments is provided
if [ $# -eq 0 ]; then
  echo "Please provide the number of entries as an argument."
  exit 1
fi

# Get the number of entries
gones=$1

# Calculate the step size for evenly spreading the entries
step=$(awk -v gones=$gones 'BEGIN { print 3 / (gones - 1) }')

# Prepare the array
array=()

# Populate the array with evenly spread values between 0 and 3
for ((i = 0; i < gones; i++)); do
  value=$(awk -v i=$i -v step=$step 'BEGIN { printf "%.1f", i * step }')
  array+=("$value")
done

# Print the array
echo "${array[@]}"

