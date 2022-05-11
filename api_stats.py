from codecs import ignore_errors
from curses.ascii import HT
from re import S
import re
from uuid import UUID
from fastapi import FastAPI, Depends, Response, HTTPException, status
import sqlite3
import contextlib
from datetime import datetime
from pydantic import UUID4, BaseModel
import redis

class Game(BaseModel):
    user_id: UUID
    game_id: int
    timestamp: str
    guesses: int
    won: bool

stats = FastAPI()

# Input: Game Object
# Output: JSON representation on whether the game was added to the database or not
# We are assuming that the client sends the user_id with each request
@stats.post("/stats", status_code=status.HTTP_201_CREATED)
async def add_game(game: Game, response: Response):
    # Make sure the user exists
    con = sqlite3.connect('./database/users.db')
    cursor = con.cursor()
    try:
        result = cursor.execute("SELECT * FROM users WHERE user_id = ?",[game.user_id.bytes_le]).fetchall()
        if len(result) == 0:
            raise HTTPException
        con.close()
    except:
        con.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid user"
        )
    # Connect to corresponding database associated with user and insert game data
    con = sqlite3.connect(f'./database/games{(game.user_id.int % 3) + 1}.db')
    cursor = con.cursor()
    try:
        cursor.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?)",
            [game.user_id.bytes_le, game.game_id, game.timestamp, game.guesses, game.won])
        con.commit()
        con.close()
    except sqlite3.IntegrityError as e:
        con.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
    response.headers["Location"] = f"/stats?user_id={game.user_id}"
    return {"user_id": game.user_id, "game_id": game.game_id, "db_id": cursor.lastrowid}


# Input: Nothing
# Output: JSON representation on the top 10 win numbers and their corresponding usernames
@stats.get("/top_wins", status_code=status.HTTP_200_OK)
async def get_top_wins():
    r = redis.Redis()
    print(r.zrange("top_wins", 0, -1, withscores=True))
    wins_query = r.zrange("top_wins", 0, -1, withscores=True)
    topWins = {}
    for x in wins_query:
        topWins.update({x[0]:x[1]})
        
    con = sqlite3.connect('./database/users.db')
    cursor = con.cursor()
    topWins_List = list(topWins)
    top10Wins = {}
    # Collect the top 10 usernames from topWins_ordered
    for i in range(0,10):
        try:
            result = cursor.execute("SELECT username FROM users WHERE user_id = ?",[topWins_List[i]]).fetchall()
            top10Wins.update({result[0][0]:topWins[topWins_List[i]]})
            if len(result) == 0:
                raise HTTPException
        except HTTPException as httpE:
            con.close()
            httpE.status_code=status.HTTP_404_NOT_FOUND, detail="Invalid user"
        except IndexError as indexE:
            con.close()
            return top10Wins
    con.close()
    return top10Wins

# Input: Nothing
# Output: JSON representation on the top 10 streak numbers and their corresponding usernames
@stats.get("/top_streaks", status_code=status.HTTP_200_OK)
async def get_top_streaks():
    r = redis.Redis()
    print(r.zrange("top_streaks", 0, -1, withscores=True))
    streaks_query = r.zrange("top_streaks", 0, -1, withscores=True)
    topStreaks = {}
    for x in streaks_query:
        topStreaks.update({x[0]:x[1]})
        
    con = sqlite3.connect('./database/users.db')
    cursor = con.cursor()
    topStreaks_List = list(topStreaks)
    top10Streaks = {}
    # Collect the top 10 usernames from topStreaks_ordered
    for i in range(0,10):
        try:
            result = cursor.execute("SELECT username FROM users WHERE user_id = ?",[topStreaks_List[i]]).fetchall()
            top10Streaks.update({result[0][0]:topStreaks[topStreaks_List[i]]})
            if len(result) == 0:
                raise HTTPException
        except HTTPException as httpE:
            con.close()
            httpE.status_code=status.HTTP_404_NOT_FOUND, detail="Invalid user"
        except IndexError as indexE:
            con.close()
            return top10Streaks 
    con.close()
    return top10Streaks

@stats.get("/stats", status_code=status.HTTP_200_OK)
async def get_stats(user_id: UUID, response: Response):
    # Make sure user exists
    con = sqlite3.connect('./database/users.db')
    cursor = con.cursor()
    try:
        result = cursor.execute("SELECT * FROM users WHERE user_id = ?",[user_id.bytes_le]).fetchall()
        if len(result) == 0:
            raise HTTPException
        con.close()
    except:
        con.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid user"
        )
    
    # currentStreak
    # Checks for any current streaks based on today
    con = sqlite3.connect(f'./database/games{(user_id.int % 3) + 1}.db')
    cursor = con.cursor()
    try:
        current_streak_query = cursor.execute("SELECT streak FROM streaks WHERE user_id = ? AND ending = ?",
            [user_id.bytes_le, datetime.today().strftime('%Y-%m-%d')]).fetchall()
        if not current_streak_query:
            win_today_query = cursor.execute("SELECT * FROM games WHERE user_id = ? AND finished = ? AND won = 1",
                [user_id.bytes_le, datetime.today().strftime('%Y-%m-%d')]).fetchall()
            if not win_today_query:
                current_streak = 0
            else:
                current_streak = 1
        else:
            current_streak = current_streak_query[0][0]
        
        # maxStreak
        streak_query = cursor.execute("SELECT * FROM streaks WHERE user_id = ?", [user_id.bytes_le]).fetchall()
        if not streak_query:
            max_streak = [0,0]
        else:
            max_streak = max(streak_query, key=lambda x: x[1])
        
        # guesses
        games_query = cursor.execute("SELECT * FROM games WHERE user_id = ?", [user_id.bytes_le]).fetchall()
        guess_array = [0] * 7
        for x in games_query:
            if x[4] == 0:
                guess_array[6] +=1
            else:
                guess_array[x[3]-1] += 1
        guesses = {"1": guess_array[0], "2": guess_array[1], "3": guess_array[2], "4": guess_array[3],
            "5": guess_array[4], "6": guess_array[5], "fail": guess_array[6]}
        
        # gamesPlayed, gamesWon, winPercentage
        total_games = len(games_query)
        wins_query = cursor.execute("SELECT * FROM wins WHERE user_id = ?", [user_id.bytes_le]).fetchone()[1]
        
        # averageGuesses
        total_guess = 0
        for x in range(6):
            total_guess += guess_array[x] * (x+1)
        win_guess = 0
        for x in range(6):
            win_guess += guess_array[x]
        con.close()
        return {"currentStreak": current_streak, "maxStreak": max_streak[1], "guesses": guesses,
            "winPercentage":round(wins_query/total_games,2) , "gamesPlayed": total_games, "gamesWon": wins_query,
            "averageGuesses": round(total_guess/win_guess)}
    except:
        con.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error"
        )
