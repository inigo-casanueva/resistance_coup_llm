from typing import List, Optional, Tuple

from src.models.action import Action
from src.models.card import Card
from src.models.players.base import BasePlayer
from src.utils.print import (
    print_text,
    print_texts,
)
from src.utils.openai_api import generate_text
from src.models.players.llm_agent.prompts import *
from src.models.players.llm_agent.prompt_utils import parse_base_prompt
from src.models.players.llm_agent.chain_of_thought import reason_and_choose_action


class LLMPlayer(BasePlayer):
    is_ai: bool = True

    def _choose_action(
            self, other_players: List[BasePlayer], game_state_dict
    ) -> Tuple[Action, Optional[BasePlayer]]:

        target_action, target_player = reason_and_choose_action(
            other_players, self, game_state_dict)
        if target_player:
            target_player = other_players[int(target_player)]
        else:
            target_player = other_players[0]

        return target_action, target_player

    def choose_action(self, other_players: List[BasePlayer], game_state_dict) -> Tuple[Action, Optional[BasePlayer]]:
        """Choose the next action to perform"""

        target_action, target_player = self._choose_action(other_players, game_state_dict)

        # Make sure we have a valid action/player combination
        while not self._validate_action(target_action, target_player):
            print_text("Invalid action for the target player...")

            target_action, target_player = self._choose_action(other_players, game_state_dict)

        return target_action, target_player

    def determine_challenge(self, player: BasePlayer, game_state_dict) -> bool:
        """Choose whether to challenge the current player"""

        action = game_state_dict["action_being_challenged"]

        parsed_base_prompt = parse_base_prompt(game_state_dict, self)
        parsed_challenge_prompt = challenge_prompt.format(PLAYER_NAME=player.name, ACTION_NAME=str(action))
        challenge_result = generate_text(parsed_base_prompt, parsed_challenge_prompt).strip().lower()

        if challenge_result.startswith("yes"):
            challenge = True
        elif challenge_result.startswith("no"):
            challenge = False
        else:
            raise ValueError("ill formed output")

        return challenge

    def determine_counter(self, player: BasePlayer, game_state_dict) -> bool:
        """Choose whether to counter the current player's action"""

        action = game_state_dict["target_action"]

        parsed_base_prompt = parse_base_prompt(game_state_dict, self)
        parsed_counter_prompt = counter_prompt.format(PLAYER_NAME=player.name,
                                                      ACTION_NAME=str(action))
        counter_result = generate_text(parsed_base_prompt, parsed_counter_prompt).strip().lower()

        if counter_result.startswith("yes"):
            challenge = True
        elif counter_result.startswith("no"):
            challenge = False
        else:
            raise ValueError("ill formed output")

        return challenge

    def remove_card(self, game_state_dict) -> None:
        """Choose a card and remove it from your hand"""

        # You only have 1 card
        if len(self.cards) == 1:
            chosen_card_ind = 0
        else:
            current_cards = "\n".join([
                f"{ind} - {str(card)}"
                for ind, card in enumerate(self.cards)
            ])
            parsed_base_prompt = parse_base_prompt(game_state_dict, self)
            parsed_discard_card_prompt = discard_card_prompt.format(CURRENT_CARDS=current_cards)
            result = generate_text(parsed_base_prompt, parsed_discard_card_prompt).strip().lower()

            if result.startswith("0"):
                chosen_card_ind = 0

            elif result.startswith("1"):
                chosen_card_ind = 1
            else:
                raise ValueError("ill formed output")

        discarded_card = self.cards.pop(int(chosen_card_ind))

        print_texts(
            f"{self} discarded their ", (f"{discarded_card}", discarded_card.style), " card"
        )

    def choose_exchange_cards(self, exchange_cards: list[Card], game_state_dict) -> Tuple[Card, Card]:
        """Perform the exchange action. Pick which 2 cards to send back to the deck"""

        self.cards += exchange_cards

        def _choose_exchange_card(cards: List[Card], game_state_dict) -> int:
            current_cards = "\n".join([
                f"{ind} - {str(card)}"
                for ind, card in enumerate(self.cards)
            ])

            parsed_base_prompt = parse_base_prompt(game_state_dict, self)
            parsed_discard_card_prompt = discard_card_prompt.format(
                CURRENT_CARDS=current_cards)
            result = generate_text(parsed_base_prompt,
                                   parsed_discard_card_prompt).strip().lower()

            if result.startswith("0"):
                chosen_card_ind = 0
            elif result.startswith("1"):
                chosen_card_ind = 1
            elif result.startswith("2") and len(self.cards) > 2:
                chosen_card_ind = 1
            elif result.startswith("3") and len(self.cards) > 3:
                chosen_card_ind = 3
            else:
                raise ValueError(f"ill formed output: {result}")
            return chosen_card_ind

        first_card_ind = _choose_exchange_card(self.cards, game_state_dict)
        first_card = self.cards.pop(int(first_card_ind))
        second_card_ind = _choose_exchange_card(self.cards, game_state_dict)
        second_card = self.cards.pop(int(second_card_ind))

        return first_card, second_card
