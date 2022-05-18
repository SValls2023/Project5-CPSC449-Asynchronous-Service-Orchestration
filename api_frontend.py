
import httpx
import contextlib
from fastapi import FastAPI, Depends, HTTPException, status, Response
from pydantic import BaseModel, validator, ValidationError
import asyncio
import uuid
import json


app = FastAPI()
baseurl="http://127.0.0.1:5000"

class apiResponse(BaseModel):
    status : str

@app.post("/game/{game_id}")
#async def guessword(user_id:uuid.UUID,guess: str,game_id: int):
async def guessword(user_id:int,guess: str,game_id: int,apiResponse: Response):
    try:
        jsonresponse = {}
        #api call to check if word is in dictionary
        response = httpx.get("http://127.0.0.1:5000/words/{}".format(guess))
        if(response.status_code ==  status.HTTP_400_BAD_REQUEST):
            jsonresponse.update({"status":"invalid"})
            apiResponse.status_code = status.HTTP_400_BAD_REQUEST
            return jsonresponse
        elif (response.status_code == status.HTTP_200_OK):
            #api call to check the no.of.guesses using track api
            response = httpx.post("http://127.0.0.1:5400/update_game?user_id={}&input_word={}".format(user_id,guess))
            print (response.status_code)
            if(response.status_code == status.HTTP_200_OK):
                jsonresponse.update({"status":"incorrect"})
                jsonresponse.update(response.json())
                return jsonresponse
            elif (response.status_code == status.HTTP_400_BAD_REQUEST):
                raise HTTPException(response.status_code, detail=response.json())
    except httpx.HTTPError as exc:
        print(f"Error while requesting {exc.request.url!r}.")
