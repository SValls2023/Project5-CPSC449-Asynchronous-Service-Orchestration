# we don't need traefik
# we can use the port name
# api = 5000, answersApi = 5100, trackApi = 5200, currentStateApi = 5300
# Updated ports wrt port names
# word = 5000, game = 5100, stat = 5200, track = 5300, main = 5400

import asyncio
import json
import httpx
import sqlite3
from uuid import UUID, uuid4
from fastapi import FastAPI, Depends, Response, HTTPException, status, Request
from datetime import datetime
app = FastAPI()

# user_id is the unique_id (byte formar)
# curr_row is the row_id
@app.post("/game/new", status_code=status.HTTP_201_CREATED)
def new_game(username: str):
    with httpx.Client() as client:
        # Part 1: Check the username from user_profiles db
        con = sqlite3.connect('./DB/Shards/user_profiles.db')
        cur = con.cursor()

        # Creates new id for the new user and commits to the users table
        user_id = cur.execute("SELECT unique_id FROM users WHERE username = ?", [username]).fetchall()
        curr_row = cur.execute("SELECT MAX(user_id) FROM users").fetchall()
        try:
            if len(user_id) == 0:
                curr_row = curr_row[0][0]; curr_row += 1
                user_id = uuid4()
                cur.execute("INSERT INTO users VALUES (?,?)", [curr_row, username, user_id])
            else:
                user_id = user_id[0][0]
                curr_row = curr_row[0][0]
            con.commit()
            con.close()
        except:
            con.close()
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error"
            )
         
        # Initialize Json game object  
        # Move status key into tracking microservice      
        curr = {"username": username, "status": "new", "unique_id":user_id}   
        d = datetime.now(); time = f"{d.year}{d.month}{d.day}"
        game_id = int(time)
        
        params = {"user_id": curr_row , "game_id": game_id}
        # Post new game or retrieve game in progress from track
        r = client.post('http://127.0.0.1:5300/new_game', params=params)
        # Update curr json with output of track
        curr.update(dict(r.json()))
        
        # Replace with update game from track
        #data = dict(r.json())
        #if int(data["counter"]) > 0:
        #    curr["status"] = "In-progress"
        #    curr.update(data)
        # Add condition that raises exception when more than 6 guesses is passed
       
        # Try getting restore game data and posting in return statement
    return curr


async def verify_guess(guess: str, data: dict):
    async with httpx.AsyncClient() as client:
        params = {"guess": guess}
        # /games/{answer_id}
        r = await client.get(f'http://127.0.0.1:5000/validate-guess', params=params)
        data.update(dict(r.json()))


@app.post("/game/{game_id}")
async def create_game(game_id: int, user_id: UUID, guess: str):
    data: dict = {}
    await asyncio.gather(
        verify_guess(guess, data)
    )
    return data
