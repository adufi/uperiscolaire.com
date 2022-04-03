#!/bin/bash

gnome-terminal --tab -e 'source scripts/run-django.sh 8001'
gnome-terminal --tab -e 'source scripts/run-node.sh'
source scripts/.ubuntu.env.sh

