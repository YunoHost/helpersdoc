#!/bin/bash

cd yunohost
git pull
git reset --hard origin/stable
cd -
python2.7 helper_doc.py
