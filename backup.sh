#!/bin/bash
DBDIR=./src/db/
cd $DBDIR
BACKUP_DIR=./src/db/backup
mkdir -p BACKUP_DIR
today=$(date "+%Y-%m-%d-%H-%M-%S")
find "$BACKUP_DIR" -type f -mtime +31 -delete
sqlite3 db.sqlite3 ".backup $BACKUP_DIR/$today.sqlite3"
gzip -f $BACKUP_DIR/$today.sqlite3
rclone sync $BACKUP_DIR  megabckp: