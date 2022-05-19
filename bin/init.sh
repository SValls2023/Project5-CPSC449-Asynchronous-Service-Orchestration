#!/bin/sh

sqlite3 ./DB/stats.db < ./DB/stats.sql
python3 create_words_db.py
python3 create_answer_db.py
mkdir ./DB/Shards
python3 create_shards.py
