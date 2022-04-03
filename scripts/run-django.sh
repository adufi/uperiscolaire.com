#!/bin/bash

source venv/bin/activate
source scripts/.ubuntu.env.sh
python project/manage.py runserver 0.0.0.0:$1