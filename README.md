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
- uvicorn api_track:track --reload
- uvicorn backend_for_frontend:app --reload
#### Using Procfile:
foreman start

#### Using Services
Go to the url: 'http://127.0.0.1:5400/docs'

For the first endpoint...

Enter a username, Example: 'ProfAvery'

You should be presented with a JSON object that include your username, user_id, and game_id...

For the second endpoint...

Enter UUID that corresponds to the username along with the guess

The JSON object will show the status of your current game 
