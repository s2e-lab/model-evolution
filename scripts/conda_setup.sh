# script to set up conda environment on CRC servers

conda create -n "HFTests" python=3.12.0
source activate base
conda activate HFTests
conda install git-lfs
pip install -r requirements.txt

#pip install datasets
#pip install GitPython
#pip install h5py
#pip install huggingface_hub
#pip install joblib
#pip install keras
#pip install numpy
#pip install pandas
#pip install requests
#pip install tensorflow
#pip install torch
#pip install tqdm
#pip install transformers
#pip install onnx
#pip install langchain
#pip install langchain-community
#pip install langchain-core
#pip install langchain-text-splitters
#pip install sentence-transformers
#pip install madml
#pip install hf-transfer
