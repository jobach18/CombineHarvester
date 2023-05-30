#!/bin/bash

# Root folder path
root_folder=$1

# Count variable
count=0

# Recursively search for files ending with "exp-s.root" and count them
find "$root_folder" -type f -name "*exp-s.root" -print | while read -r file; do
    count=$((count + 1))
done

# Print the total count of files
echo "Total files ending with 'exp-s.root': $count"

