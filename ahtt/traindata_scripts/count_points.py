import os
import glob


directory = '/nfs/dust/cms/user/bachjoer/ml-workspace/learn_likelihood/CMSSW_10_2_13/src/CombineHarvester/ahtt/data/highmass/'
extension = '.tar.gz'

print(os.listdir(directory))

file_pattern = f'{directory}/**/*.{extension}'
file_paths = glob.glob(file_pattern, recursive=True)
print(file_paths)

print(f' there are {len(file_paths)} files that end with exp-s.root')
