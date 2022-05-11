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
import aioredis
import redis

class Session(BaseModel):
    user_id: UUID
    game_id: int

    
# track_cli = Redis()
track = FastAPI()


# Input: User ID, Game ID
# Output: Indicate a succesful response, or an error as the user already exists
@track.post("/new_game", status_code=status.HTTP_201_CREATED)
async def new_game(sess:Session, response: Response):
    # Make sure user exists
    con = sqlite3.connect('./database/users.db')
    cursor = con.cursor()
    try:
        result = cursor.execute("SELECT * FROM users WHERE user_id = ?",
        	[sess.user_id.bytes_le]).fetchall()
        if len(result) == 0:
            con.close()
            raise HTTPException
    except:
        con.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid user"
        )
  
    con = sqlite3.connect(f'./database/games{(sess.user_id.int % 3) + 1}.db')
    cursor = con.cursor()
    try:
        game = cursor.execute("SELECT * FROM games WHERE user_id = ? and game_id = ?", [sess.user_id.bytes_le,sess.game_id]).fetchall()
        if len(game) != 0:
            con.close()
            raise HTTPException
    except:
        con.close()
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="You already played this game!"
            )
    r = redis.Redis(decode_responses=True)
    user_id = sess.user_id.bytes_le
    r.delete(user_id)
    r.rpush(user_id, sess.game_id)
    r.rpush(user_id, 0)
    response.headers["Location"] = f"/restore_game?user_id={sess.user_id}"
    return {"user_id": sess.user_id, "game_id": sess.game_id, "guesses" : 0}    
    

# Input: user_id and new guess word
# For a new guess, record the guess and update the number of guesses remaining
# Output an error if the number of guesses exceeds 6
@track.post("/update_game", status_code=status.HTTP_200_OK)
async def update_game(user_id: UUID, input_word: str, response: Response):
    guess_word = input_word.lower()
    user_id = user_id.bytes_le
    r = redis.Redis(decode_responses=True)
    user_guess_info = r.lrange(user_id, 0, -1)
    if len(user_guess_info) > 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No more! You reached your 6 allowed guesses."
        )
    r.rpush(user_id, input_word)
    r.lset(user_id, 1, int(user_guess_info[1])+1)
    return {"input": guess_word}



# Input: new guess from the user
# Output: Return information about the current game state of the user
@track.post("/restore_game", status_code=status.HTTP_200_OK)
async def update_game(user_id: UUID, response: Response):
    # Make sure user exists
    con = sqlite3.connect('./database/users.db')
    cursor = con.cursor()
    try:
        result = cursor.execute("SELECT * FROM users WHERE user_id = ?",
        	[user_id.bytes_le]).fetchall()
        if len(result) == 0:
            con.close()
            raise HTTPException
    except:
        con.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid user"
        )
    user_id = user_id.bytes_le
    r = redis.Redis(decode_responses=True)
    user_guess_info = r.lrange(user_id, 0, -1)
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
    return {"current_game_id": user_guess_info[0], "guesses_left":7-int(user_guess_info[1]), "guesses": guess_dict}
