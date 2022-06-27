#!/bin/bash

rm -rf ../code/receipes/saw-ntn
rm -rf ../code/receipes/suaw-ntn
cp -r generated/saw-ntn ../code/receipes/saw-ntn
cp -r generated/suaw-ntn ../code/receipes/suaw-ntn
cd ../code
python3.8 nt.py evaluate -s1 saw-ntn -s2 suaw-ntn --plot
