#!/bin/bash
# $1 topic
# $2 interval(float)

python tools/knowledge/init.py  # download the dictionary
mkdir tools/knowledge/cookie  # cookie file
echo "operating explore.py"  # message
python tools/knowledge/explore.py $1 $2  # knowledge exploration
