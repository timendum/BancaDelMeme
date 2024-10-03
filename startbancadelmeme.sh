#!/usr/bin/env bash
set -Eeuo pipefail
script_dir=$(realpath "$(dirname "${BASH_SOURCE[0]}")")
cd $script_dir

trap "screen -S mememain -X quit" INT QUIT
trap "screen -S memesub -X quit" INT QUIT
trap "screen -S memecalc -X quit" INT QUIT
trap "screen -S memeteleg -X quit" INT QUIT


# crontab
# cd ~/bancaDelMeme/src && ../bin/python buyabler.py

/bin/sleep 1
screen -d -m -S mememain /bin/bash
screen -S mememain -X stuff "cd ./src/^M"
screen -S mememain -X stuff "../venv/bin/python3 main.py^M"

/bin/sleep 1
screen -d -m -S memesub /bin/bash
screen -S memesub -X stuff "cd ./src/^M"
screen -S memesub -X stuff "../venv/bin/python3 submitter.py^M"

/bin/sleep 1
screen -d -m -S memecalc /bin/bash
screen -S memecalc -X stuff "cd ./src/^M"
screen -S memecalc -X stuff "../venv/bin/python3 calculator.py^M"
