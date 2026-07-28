# script to set up conda environment on CRC servers
conda create -n "HFStudy" python=3.11.0
source activate base
conda activate HFTests
conda install git-lfs
pip install -r requirements.txt
