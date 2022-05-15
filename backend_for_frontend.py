# we don't need traefik
# we can use the port name
# api = 5000, answersApi = 5100, trackApi = 5200, currentStateApi = 5300

import asyncio
import json
import httpx
from uuid import UUID
from fastapi import FastAPI, Depends, Response, HTTPException, status, Request
from datetime import datetime
app = FastAPI()


@app.post("/game/new", status_code=status.HTTP_201_CREATED)
def new_game(username: str):
    with httpx.Client() as client:
        params = {"username": username}
        # try:
        r = client.get('http://127.0.0.1:5200/user-data', params=params)
        # except httpx.RequestError as exc:
        #     raise
        curr = {"status": "new"}
        curr.update(dict(r.json()))
        d = datetime.now()
        time = f"{d.year}{d.month}{d.day}"
        curr["game_id"] = int(time)
        params = {"user_id": curr.get("user_uuid"), "game_id": curr.get("game_id")}
        r = client.post('http://127.0.0.1:5300/start-new-game', params=params)
        # if r.status_code != httpx.codes.CREATED:
        #     return r.raise_for_status()
        data = dict(r.json())
        if int(data["counter"]) > 0:
            curr["status"] = "In-progress"
            curr.update(data)
            counter = int(curr.pop("counter"))
            curr["remain"] = 6 - counter
            params = {"answer_guess": curr.get("list")[counter - 1]}
            r = client.get('http://127.0.0.1:5100/validate-answer', params=params)
            # if r.status_code != httpx.codes.OK:
            #     return r.raise_for_status()
            curr.update(dict(r.json()))
    return curr


async def verify_guess(guess: str, data: dict):
    async with httpx.AsyncClient() as client:
        params = {"guess": guess}
        r = await client.get(f'http://127.0.0.1:5000/validate-guess', params=params)
        data.update(dict(r.json()))


@app.post("/game/{game_id}")
async def create_game(game_id: int, user_id: UUID, guess: str):
    data: dict = {}
    await asyncio.gather(
        verify_guess(guess, data)
    )
    return data
