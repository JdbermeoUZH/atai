# Install miniconda
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
~/miniconda3/bin/conda init bash

# Reinitialize or source
export PATH="$HOME/miniconda3/bin:$PATH"
source "$HOME/miniconda3/bin/activate"

# Copy content from s3
aws s3 sync s3://jdbermeo/ATAI_def/ ./

# Create conda env
conda update conda -y
conda create --name ATAI_aws
conda activate ATAI_aws

# Install libraries
conda install -c anaconda scikit-learn -y
conda install -c conda-forge spacy -y
python -m spacy download en_core_web_sm
pip install spacy-entity-linker
python -m spacy_entity_linker "download_knowledge_base"
python -m spacy download en_core_web_trf
pip install rdflib
pip install thefuzz[speedup]
pip install spacyfishing
pip install classy-classification
