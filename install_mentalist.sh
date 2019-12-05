#!/usr/bin/env bash

conda init bash
source activate julia
julia -e 'using Pkg; Pkg.add("Distributed")'
julia -e 'using Pkg; Pkg.add("ArgParse")'
julia -e 'using Pkg; Pkg.add("BioSequences")'
julia -e 'using Pkg; Pkg.add("JSON")'
julia -e 'using Pkg; Pkg.add("DataStructures")'
julia -e 'using Pkg; Pkg.add("JLD")'
julia -e 'using Pkg; Pkg.add("GZip")'
julia -e 'using Pkg; Pkg.add("Blosc")'
julia -e 'using Pkg; Pkg.add("FileIO")'
julia -e 'using Pkg; Pkg.add("TextWrap")'
julia -e 'using Pkg; Pkg.add("LightXML")'
git clone https://github.com/WGS-TB/MentaLiST.git
conda deactivate
