# CombineHarvester

Full documentation: http://cms-analysis.github.io/CombineHarvester

## Quick start

This pacakge requires HiggsAnalysis/CombinedLimit to be in your local CMSSW area. We follow the release recommendations of the combine developers which can be found [here](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/#setting-up-the-environment-and-installation). The CombineHarvester framework is compatible with the CMSSW 8_1_X and 10_2_X series releases.

If you just need the core CombineHarvester/CombineTools subpackge, then the following scripts can be used to clone the repository with a sparse checkout for this one only:

    git clone via ssh:
    bash <(curl -s https://raw.githubusercontent.com/cms-analysis/CombineHarvester/master/CombineTools/scripts/sparse-checkout-ssh.sh)
    git clone via https:
    bash <(curl -s https://raw.githubusercontent.com/cms-analysis/CombineHarvester/master/CombineTools/scripts/sparse-checkout-https.sh)

A new full release area can be set up and compiled in the following steps:

    export SCRAM_ARCH=slc7_amd64_gcc700
    scram project CMSSW CMSSW_10_2_13
    cd CMSSW_10_2_13/src
    cmsenv
    git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
    # IMPORTANT: Checkout the recommended tag on the link above
    git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester
    scram b

Previously this package contained some analysis-specific subpackages. These packages can now be found [here](https://gitlab.cern.ch/cms-hcg/ch-areas). If you would like a repository for your analysis package to be created in that group, please create an issue in the CombineHarvester repository stating the desired package name and your NICE username. Note: you are not obliged to store your analysis package in this central group.


## Learning Likelihood of bachjoer
This specific branch is used as a tool to extract training data from the Combine tool to build a network that learns the likelihood function as a function of the parameter space. 
The goal of this project is speedup of limit setting procedure in the case of higher dimensional contours. 
We work with the CMS heavy Higgs analysis blinded data and we'll figure out along the project if this is expandable to different analysis within the top group of CMS, CMS as a whole or could even be used as a general tool. 
The scripts are contained in the  ahtt folder, where the heavy Higgs analysis scripts are located. These call the combine code with the correct configuration for systematics, Monte Carlo data etc. 

The folder /ahtt/traindata_scripts contains the scripts to run a wide selection of parameter points parallelized on the htCondor machines on DESY NAF. 
If not explicitly differently specified, all these scripts need to be called while in their specific directories.
To do that, edit the submit_datacard_combine.sh script. The variable "masses" and "widths" specifies the mass and width points that one wants to submit.
The script takes these and submits Combine jobs for all possible commutations of these masses and widths (for heavy scalar Higgs H and heavy pseudoscalar Higgs A). This is in theory easily expandable to other parameters as well, having CP configurations of the aforementioned particles in mind in particular. 
The files in ahtt/traindata_scripts/template/ are the ones called in this submit script and contain the call to build the datacard, validate it and run the combine fit. Do not fiddle with these if not necessary. 
The submit_datacard_combine.sh script takes no input during submit. 
The second step is called via ahtt/traindata_scripts/submit_extrah5.sh and extracts the info gained by running combine into pandas dataframes. 
This script is called with the arguments (in that order):
Jobs TAG Expectation
 such that a call could look like:

	bash submit_extrah5.sh 100 "tag1" "exp-s" 

to run the extraction into h5 files with 100 jobs in parallel, for the data generated in the data/tag1/ folder for the combine results with the expected signal (combine info exp-s). 
The python script ahtt/traindata_scripts/concat_h5.py is run with the inputs -tag -exp and concatenates the resulting h5 files from step 2 into one larg "full.h5" file. 

### The ML Module
The path ahtt/ml/ contains the code to built and test ML models to learn the negative log likelihood. 
The network.py file contains the classes 
	1. Model:
		contains the instructions for a pytorch DNN, so far only simple fully connected architectures are implemented. This might change in the future. 
		A model is initialized by passing the size of the input vector and the number of hidden nodes. 
		Currently, one hidden layer with n_hidden nodes gets initialized. This is hard-coded, so changes in the architecture need to be done in the construct of this class.
		A rectified linear Unit is used for activation and a single output node gives the regression output 
	2. Dataset:
		A pytorch dataset, initialized by passing the x and y values as torch tensors or np arrays. 
	3. Trainer
		This class does the magic, holds an instance of Model and Dataset and fulfills the task of training.
		Currently is initialized by passing an instance of a Dataset a Model and a loss function defined by a python function with y_target and y_dnnoutput as arguments. 
		Trainer.train(n_epochs, lr) is the function which actually trains the torch model, with the specified number of epochs and learning rate lr.  

