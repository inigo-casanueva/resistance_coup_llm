from typing import List
from src.models.players.base import BasePlayer
from src.models.players.llm_agent.prompts import base_prompt, coup_rules, personas


def parse_game_state(game_state_dict, parsing_player) -> str:
    """Generate text with the game state information to be fed to the LLM"""
    players = game_state_dict["players"]
    deck = game_state_dict["deck"]
    treasury_coins = game_state_dict["treasury"]
    current_player_index = game_state_dict["current_player_index"]
    current_player = players[current_player_index]

    game_state_text = f"### CURRENT GAME STATE:\n"

    active_players = [player for player in players if player.is_active]
    current_active_player_idx = 0
    for ind, player in enumerate(active_players):
        if str(player) == str(current_player):
            current_active_player_idx = ind
        if str(player) == str(parsing_player):
            card_text = " and ".join([str(card) for card in player.cards])
        else:
            if len(player.cards) == 2:
                card_text = "two face down cards"
            else:
                card_text = "one face down card"

        game_state_text += f"- {ind} | Name: {str(player)} | coins: {player.coins} | cards: {card_text}\n"

    game_state_text += (f"\n\n Board state:\ndeck: {len(deck)} cards\ntreasury: {treasury_coins} coins\n"
                        f"Current Player: {current_active_player_idx} - {current_player}")

    return game_state_text


def get_player_index(players: List[BasePlayer], player_name: str) -> int:
    for i, player in enumerate(players):
        if player_name == str(player):
            return i
    raise ValueError


def parse_game_history(game_history: List, n_turns: int = 10) -> str:
    """Generate text with the game history over the last n_turns to be fed to the LLM"""
    game_history_string = ""
    for turn in game_history[-n_turns:]:
        game_history_string += "## NEW TURN ##\n"
        for event in turn:
            game_history_string += f"- {event}\n"
    return game_history_string


def parse_chat_history(chat_history: List) -> str:
    if len(chat_history) == 0:
        return "No conversation yet."
    else:
        return chat_history[-1]


def parse_base_prompt(game_state_dict: dict, player) -> str:
    """Parse the base prompt to include the information about the current player and game state

    This includes:
    - The game rules
    - The game state (the player wont see other players cards)
    - The game and chat history
    - The player index, name and persona
    """
    game_state_text = parse_game_state(game_state_dict, player)
    game_history_text = parse_game_history(game_state_dict["game_history"])
    game_conversation = parse_chat_history(game_state_dict["chat_history"])
    player_index = get_player_index(game_state_dict["players"], str(player))
    persona = personas[player_index]

    parsed_base_prompt = base_prompt.format(COUP_RULES=coup_rules,
                                            PLAYER_INDEX=player_index,
                                            PLAYER_NAME=str(player),
                                            GAME_STATE=game_state_text,
                                            GAME_HISTORY=game_history_text,
                                            GAME_CONVERSATION=game_conversation,
                                            PERSONA=persona)

    return parsed_base_prompt
