from codecs import ignore_errors
from curses.ascii import HT
from re import S
import re
from uuid import UUID, uuid4
from fastapi import FastAPI, Depends, Response, HTTPException, status
import sqlite3
import contextlib
from datetime import datetime
from pydantic import UUID4, BaseModel
from redis import Redis
import asyncio
#import aioredis
import redis

#class Session(BaseModel):
#    user_id: int
#    game_id: int


# track_cli = Redis()
track = FastAPI()

# Sample UUIDs for testing
#c97f5995-0551-40d4-85e2-4f6313385e44  user_id = 99998  username = donald64
#e1345bbb-ae9c-42a1-bc7a-273913552f7d  user_id = 99999  username = terrylarry
#fea11f5d-02b4-4dc9-a0ba-619990486cba  user_id = 100000 username = christina22


# Input: User ID, Game ID
# Output: Indicate a succesful response, or an error as the user already exists
@track.post("/new_game", status_code=status.HTTP_201_CREATED)
async def new_game(user_id: int, game_id: int, response: Response):
    # Make sure user exists
    # TO DO: Correct hashing scheme for shards
    con = sqlite3.connect('./DB/Shards/user_profiles.db')
    cursor = con.cursor()
    try:
        unique_id = cursor.execute("SELECT unique_id FROM users WHERE user_id = ?",
        	[user_id]).fetchone()[0]
        if len(unique_id) == 0:
            con.close()
            raise HTTPException
    except:
        con.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid user"
        )

    con = sqlite3.connect(f'./DB/Shards/stats{(user_id % 3) + 1}.db')
    cursor = con.cursor()
    try:
        game = cursor.execute("SELECT * FROM games WHERE user_id = ? AND game_id = ?", [user_id,game_id]).fetchall()
        if len(game) != 0:
            con.close()
            raise HTTPException
        con.close()
    except:
        con.close()
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="You already played this game!"
            )
    r = redis.Redis(decode_responses=True)
    unique_id = str(unique_id)
    r.delete(unique_id)
    r.rpush(unique_id, game_id)
    r.rpush(unique_id, 0)
    response.headers["Location"] = f"/restore_game?unique_id={unique_id}"
    # Modify this to return json format from the project 5 example
    return {"unique_id": unique_id, "game_id": game_id}


# Input: uniquw_id and new guess word
# For a new guess, record the guess and update the number of guesses remaining
# Output an error if the number of guesses exceeds 6
@track.post("/update_game", status_code=status.HTTP_200_OK)
async def update_game(user_id: int, input_word: str, response: Response):
    # Make sure user exists
    con = sqlite3.connect('./DB/Shards/user_profiles.db')
    cursor = con.cursor()
    try:
        unique_id = cursor.execute("SELECT unique_id FROM users WHERE user_id = ?",
        	[user_id]).fetchone()[0]
        if len(unique_id) == 0:
            con.close()
            raise HTTPException
    except:
        con.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid user"
        )
    unique_id = str(unique_id)
    guess_word = input_word.lower()
    r = redis.Redis(decode_responses=True)
    user_guess_info = r.lrange(unique_id, 0, -1)
    if len(user_guess_info) > 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No more! You reached your 6 allowed guesses."
        )
    r.rpush(unique_id, input_word)
    r.lset(unique_id, 1, int(user_guess_info[1])+1)
    return {"input": guess_word}



# Input: new guess from the user
# Output: Return information about the current game state of the user
@track.post("/restore_game", status_code=status.HTTP_200_OK)
async def update_game(user_id: int, response: Response):
    # Make sure user exists
    con = sqlite3.connect('./DB/Shards/user_profiles.db')
    cursor = con.cursor()
    try:
        unique_id = cursor.execute("SELECT unique_id FROM users WHERE user_id = ?",
        	[user_id]).fetchone()[0]
        if len(unique_id) == 0:
            con.close()
            raise HTTPException
    except:
        con.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid user"
        )
    unique_id = str(unique_id)
    r = redis.Redis(decode_responses=True)
    user_guess_info = r.lrange(unique_id, 0, -1)
    print(user_guess_info)
    if len(user_guess_info) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User is not playing any game"
        )
    guess_dict = {}
    for i in range(2,8):
        try:
            guess_dict.update({i-1:user_guess_info[i]})
        except IndexError:
            break
    return {"current_game_id": user_guess_info[0], "guesses_left":6-int(user_guess_info[1]), "guesses": guess_dict}
