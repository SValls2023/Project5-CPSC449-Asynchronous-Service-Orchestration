from re import S
from fastapi import FastAPI, Depends, Response, HTTPException, status
import sqlite3
import contextlib
from datetime import datetime
from uuid import uuid4
import httpx


main = FastAPI()


# Query users db and look for user id(uuid)
# If it exists, choose a new game_id that user hasn't played
# Else: generate new user, and choose a new game_id
# Also add new username to users table from the users db and games table from the games db
# !!!!!!!!!!!!Fix game_id timestamp across microservices (using game date instead)!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!Post username to db!!!!!!!!!!!!!!!!!!!!!
@main.post("/game/new", status_code=status.HTTP_200_OK)
async def check_user(username: str, response: Response):
    # Checks if user is in db
    con = sqlite3.connect('./database/users.db')
    cursor = con.cursor()
    params = {}
    new_game = 0
    user_id = uuid4()
    try:
        result = cursor.execute("SELECT user_id FROM users WHERE username = ?",[username]).fetchall()	
        # Assign user_id and game_id for new user
        # Consider randomizing game_id from a range of all positive integers
        if len(result) == 0:
            params = {'user_id': user_id , 'game_id': 0}
            new_game = httpx.post('http://localhost:9999/api/track/new', params=params)
        else:
        # Choose new game_id
        # Find max game_id and increment by 1
            curr_user = result[0][0]
            for i in range(1,4):
                con = sqlite3.connect(f'./database/games{i}.db')
                cursor = con.cursor()   
                game = cursor.execute("SELECT game_id FROM games WHERE user_id = ?",[curr_user]).fetchall()
                if len(game) != 0:
                    curr_game = max(game); new_game = curr_game[0][0] + 1
                    # Post new game to the endpoint
                    params = {'user_id': user_id, 'game_id': new_game}
                    new_game = httpx.post('http://localhost:9999/api/track/new', params=params)
                else:
                    continue
            con.close()
    except:
        con.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error"
        )
    # Commit username to db
    return {"status": "new", "user_id": user_id, "game_id": new_game}
        

# Input: user word
# Output: JSON representation on whether the word was added to the database or not
@main.post("/game/{game_id}", status_code=status.HTTP_201_CREATED)
async def add_word(user_word: str, response: Response):
    pass
