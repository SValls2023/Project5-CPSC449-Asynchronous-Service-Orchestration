# we don't need traefik
# we can use the port name
# api = 5000, answersApi = 5100, trackApi = 5200, currentStateApi = 5300
# Updated ports wrt port names
# word = 5000, game = 5100, stat = 5200, track = 5300, main = 5400

import asyncio
import json
import httpx
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



async def async_req(url, method='get'):
    async with httpx.AsyncClient() as client:
        if method == 'get':
            r = await client.get(url,timeout=60)
        else:
            r = await client.post(url)

    return r

def req(url, method='get'):
    with httpx.Client() as client:
        if method == 'get':
            r = httpx.get(url,timeout=60)
        else:
            r = httpx.post(url)
    return r

@app.post("/game/{game_id}")
async def guessword(user_id:uuid.UUID,guess: str,game_id: int,apiResponse: Response):
    try:
        jsonresponse = {}
        tasks = []
        #api call to check if word is in dictionary
        response = req("http://127.0.0.1:5000/words/{}".format(guess))
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            jsonresponse.update({"status":"invalid"})
            apiResponse.status_code = status.HTTP_400_BAD_REQUEST
            return jsonresponse
        #if the guess is a valid word in dcitionary
        elif response.status_code == status.HTTP_200_OK:
            answer_id = random.randint(0,200)
            answer_id = 10
            #api call to check the no.of.guesses using track api
            tasks.append(asyncio.create_task(async_req("http://127.0.0.1:5300/update_game?user_id={}&input_word={}".format(user_id,guess),"post")))
            #api call to: check if guess is correct answer
            tasks.append(asyncio.create_task(async_req("http://127.0.0.1:5100/games/{}?guess={}".format(answer_id,guess))))
            result_responses = await asyncio.gather(*tasks)
            response = result_responses[0]
            #if the guesses are remaining
            if(response.status_code == status.HTTP_200_OK):
                jsonresponse.update(response.json())
                guess_remaining = response.json()["remaining"]
                response = result_responses[1]
                if(response.status_code == status.HTTP_200_OK):
                    if(response.json()["status"] == "incorrect" and (guess_remaining)>0):
                        jsonresponse.update(response.json())
                    else:
                        #call stats api and return stats
                        statsresponse= req("http://127.0.0.1:5200/stats/games/{}/".format(user_id))
                        if(response.json()["status"] == "win"):
                            jsonresponse.update(response.json())
                            jsonresponse.update(statsresponse.json())
                        elif(response.json()["status"] == "incorrect" and guess_remaining==0):
                            jsonresponse.update({"status":"incorrect"})
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
        return(f"Error while requesting {exc.request.url!r}.")
