#!/usr/bin/env bash
set -Eeuo pipefail
script_dir=$(realpath "$(dirname "${BASH_SOURCE[0]}")")
cd $script_dir

screen -S mememain -X quit
screen -S memesub -X quit
screen -S memecalc -X quit
screen -S memeteleg -X quit

# crontab
# cd ~/bancaDelMeme/src && ../bin/python buyabler.py

/bin/sleep 1
screen -d -m -S mememain /bin/bash
screen -S mememain -X stuff "cd ./src/^M"
screen -S mememain -X stuff "../bin/python3 main.py^M"

/bin/sleep 1
screen -d -m -S memesub /bin/bash
screen -S memesub -X stuff "cd ./src/^M"
screen -S memesub -X stuff "../bin/python3 submitter.py^M"

/bin/sleep 1
screen -d -m -S memecalc /bin/bash
screen -S memecalc -X stuff "cd ./src/^M"
screen -S memecalc -X stuff "../bin/python3 calculator.py^M"

/bin/sleep 1
screen -d -m -S memeteleg /bin/bash
screen -S memeteleg -X stuff "cd ./src/^M"
screen -S memeteleg -X stuff "../bin/python3 telegram_bot.py^M"
