# Project5-CPSC449-Asynchronous-Service-Orchestration
### Databases (Executables located in DB/):
Create Dictionary: execute python3 create_words_db.py in the terminal

Create Game Database: execute python3 create_answer_db.py in the terminal

Initialize database: execute create_stats_db.sh in the terminal

Create folder called Shards before executing create_shards.py

Create shards: execute create_shards.py in the terminal

### Starting services:
#### Standalone:
- uvicorn api_dict:app --reload
- uvicorn api_game:app --reload
- uvicorn api_stats:app --reload
#### Using Procfile:
foreman start
