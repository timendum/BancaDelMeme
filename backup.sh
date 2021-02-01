#!/bin/bash
cd /home/ambrogio/bancaDelMeme
DBDIR=./db/
BACKUP_DIR=./db/backup
mkdir -p BACKUP_DIR
today=$(date "+%Y-%m-%d-%H-%M-%S")
find "$BACKUP_DIR" -type f -mtime +31 -delete
sqlite3 $DBDIR/db.sqlite3 ".backup $BACKUP_DIR/$today.sqlite3"
gzip -f $BACKUP_DIR/$today.sqlite3
rclone sync $BACKUP_DIR  megabckp: