#!/bin/bash

# cd to own containing directory
cd "${0%/*}"
cd SampleSystems

~/Documents/mac/ToolboxToolbox/fsnek -r \
    7.1.0.rdump \
    7.1.1.rdump \
    7.5.0.rdump \
    7.5.3.rdump \
    DT_8.1_1.rdump \
    7.5.5.rdump \
    DT_8.1_PPC.rdump \
    7.6.0.rdump \
    7.6.1.rdump \
    8.0.0.rdump \
    8.1.0.rdump \
    9.2.2.rdump \
    > ../resreport.txt
