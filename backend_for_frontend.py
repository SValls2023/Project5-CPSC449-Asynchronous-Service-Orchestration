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
