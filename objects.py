import discord
from typing import List, Dict, Optional
from enum import Enum

class State(Enum):
    ''' The current state of the game
    
    === State ===
    null = Game has not yet started
    started = The game has started and players may join
    setup = The game has been setup and no more players may join
    day = A player has died and it's day time
    night = It's night time and all roles but citizens must act
    '''
    null = 1
    started = 3
    day = 4
    night = 5

class Player:
    ''' A player in a game of Mafia 

    === Attributes ===
    - ID: A player's Discord ID, its a private variable 
    - is_alive: the status of this player
    - role: the role of this player
    '''
    ID: int
    role: str
    is_alive: bool
    is_protected: bool
    has_acted: bool

    def __init__(self, ID: int) -> None:
        ''' Initializes this player. Everyone is initially a villager'''
        self.ID = ID
        self.role = "None"
        self.is_alive = True
        self.is_protected = False

class Game:
    '''
    This is a representation of a Game of Mafia

    === Attributes === 
    - server_id: The server that the Game is currently playing in
    - dead: All the dead players in this Game
    - state: Current state of the game
    - player_atlas: dictionary of all players split by their roles
    '''
    leader: Player
    server_id: int
    dead: List[Player]
    state = None
    player_atlas: dict()

    def __init__(self, server_id) -> None:
        self.server_id = server_id
        self.dead = list()
        self.state = State.null
        self.player_atlas = dict()
        self.player_atlas["none"] = []
        self.player_atlas["mafiosi"] = []
        self.player_atlas["medics"] = []
        self.player_atlas["detectives"] = []
        self.player_atlas["citizens"] = [] 

    def get_player(self, player_ID: int) -> Player:
        # returns the Player object with the <player_id> from <self.player_atlas>
        for role in self.player_atlas:
            for player in self.player_atlas[role]:
                if player.ID == player_ID:
                    return player
        return None

    def kill_player(self, player_ID: int) -> None:
        # kill a player and add to dead list
        player = get_player(player_ID)
        self.player_atlas[player.role].remove(player)
        self.dead.append(player)

    def can_act(self, player_ID: int, player_role: str) -> bool:
        # return true if player can perform specific action ie. kill/protect/inspect
        player = get_player(player_ID)

        if player.role == player_role and self.state == State.night:
            return True
        else:
            return False

    def reset_acts(self) -> None:
        for role in self.player_atlas:
            for player in self.player_atlas[role]:
                player.has_acted = False

    def all_night_acts_complete(self) -> bool:
        # return true if all players except citizens have acted
        for player in self.player_atlas["mafiosi"]:
            if not player.has_acted:
                return False

        for player in self.player_atlas["medics"]:
            if not player.has_acted:
                return False

        for player in self.player_atlas["detectives"]:
            if not player.has_acted:
                return False

        self.state = State.day
        self.reset_acts()

        return True

    def all_day_acts_complete(self) -> bool:
        # return true if everyone has voted to lynch
        for player in self.player_atlas["citizens"]:
            if not player.has_acted:
                return False

        self.state = State.night
        self.reset_acts()

        return True
