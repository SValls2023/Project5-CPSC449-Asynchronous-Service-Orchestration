# we don't need traefik
# we can use the port name
# api = 5000, answersApi = 5100, trackApi = 5200, currentStateApi = 5300
# Updated ports wrt port names
# word = 5000, game = 5100, stat = 5200, track = 5300, main = 5400

import asyncio
import json
import httpx
import sqlite3
import random
import uuid
from fastapi import FastAPI, Depends, Response, HTTPException, status, Request
from pydantic import BaseModel, validator, ValidationError
from datetime import datetime


app = FastAPI()

# REPLACE USER_ID WITH UNIQUE_ID not for string tho
@app.post("/game/new", status_code=status.HTTP_201_CREATED)
def new_game(username: str):
    with httpx.Client() as client:
        # Creates new users and feteches current user's data
        user = client.get("http://127.0.0.1:5300/user?username={}".format(username))
        user = dict(user.json())

        # Pass parameters into the track service
        new_game = client.post("http://127.0.0.1:5300/new_game?user_id={}&game_id={}".format(user["curr_row"],user["game_id"]))

        # Retrieve parameters fro current user's game
        if user["status"] == "in-progress":
            restore_game = client.post("http://127.0.0.1:5300/restore_game?user_id={}".format(user["curr_row"]))
            restore_game = dict(restore_game.json())

            curr_game = {"remaining": restore_game["guesses_left"], "guesses": restore_game["guesses"], "letters": {"correct": [], "present": []}}
            user.update(curr_game)
        user.update(dict(new_game.json()))
        user.pop("curr_row")

    return user


@app.get("/print")
async def print(user_id:int):
    sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))
    sqlite3.register_adapter(uuid.UUID, lambda u: memoryview(u.bytes_le))
    con = sqlite3.connect("./DB/Shards/user_profiles.db", detect_types=sqlite3.PARSE_DECLTYPES)
    db = con.cursor()
    cur = db.execute("SELECT unique_id FROM users where user_id=(?)",[user_id]).fetchone()
    return cur[0]


@app.post("/game/{game_id}")
#async def guessword(user_id:uuid.UUID,guess: str,game_id: int):
async def guessword(user_id:uuid.UUID,guess: str,game_id: int,apiResponse: Response):
    try:
        jsonresponse = {}
        #api call to check if word is in dictionary
        response = httpx.get("http://127.0.0.1:5000/words/{}".format(guess))
        if(response.status_code ==  status.HTTP_400_BAD_REQUEST):
            jsonresponse.update({"status":"invalid"})
            apiResponse.status_code = status.HTTP_400_BAD_REQUEST
            return jsonresponse
        #if the guess is a valid word in dcitionary
        elif (response.status_code == status.HTTP_200_OK):
            #api call to check the no.of.guesses using track api
            response = httpx.post("http://127.0.0.1:5300/update_game?user_id={}&input_word={}".format(user_id,guess))
            #print (response.status_code)
            #if the guesses are remaining
            if(response.status_code == status.HTTP_200_OK):
                jsonresponse.update(response.json())
                guess_remaining = response.json()["remaining"]
                answer_id = random.randint(0,200)
                answer_id = 10
                #api call to check if guess is correct answer
                response = httpx.get("http://127.0.0.1:5100/games/{}?guess={}".format(answer_id,guess))
                if(response.status_code == status.HTTP_200_OK):
                    if(response.json()["status"] == "incorrect" and (guess_remaining-1)>0):
                        jsonresponse.update(response.json())
                    else:
                        #call stats api and return stats
                        statsresponse= httpx.get("http://127.0.0.1:5200/stats/games/{}/".format(user_id),timeout=60.0)
                        if(response.json()["status"] == "win"):
                            jsonresponse.update(response.json())
                            jsonresponse.update(statsresponse.json())
                        elif(response.json()["status"] == "incorrect" and (guess_remaining-1)<=0):
                            jsonresponse.update(statsresponse.json())
                    return jsonresponse
                else:
                    raise HTTPException(response.status_code, detail=response.json())

            #if no more guesses are left
            elif (response.status_code == status.HTTP_400_BAD_REQUEST):
                jsonresponse.update({"status":"no more guesses allowed"})
                apiResponse.status_code = status.HTTP_400_BAD_REQUEST
                return jsonresponse
                #raise HTTPException(response.status_code, detail=response.json())
    except httpx.HTTPError as exc:
        print(f"Error while requesting {exc.request.url!r}.")
