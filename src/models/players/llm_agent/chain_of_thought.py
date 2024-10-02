import json
from typing import List, Tuple, Optional

from src.models.players.llm_agent.prompt_utils import parse_base_prompt
from src.models.players.llm_agent.prompts import *
from src.models.players.base import BasePlayer
from src.utils.openai_api import generate_text
from src.models.players.llm_agent.params import max_retries, print_chain_of_thought


def reason_and_choose_action(other_players: List[BasePlayer], player: BasePlayer, game_state_dict) -> Tuple[
        int, Optional[int]]:
    """Reasons about the next action to take in 3 steps
    1. Comes up with a plan conditioned in the current game state and the previous player interactions
    2. Analyses the plan in order to find potential flaws and updates it accordingly
    3. Given the final plan outputs a json dict with the action and the target

    The decision in conditioned on:
    - The game state (the player wont see other players cards)
    - The game and chat history
    - The player persona (e.g. shy players will play less aggressively)

    """
    print(f"{str(player)} is thinking which action to take...")

    available_actions = player.available_actions()

    available_actions_text = "\n".join(
        [f"{ind}: {str(action)}" for ind, action in
         enumerate(available_actions)])

    available_targets_text = "\n".join([
        f"{ind} - {str(player)}"
        for ind, player in enumerate(other_players)
        if player.is_active
    ])
    parsed_base_prompt = parse_base_prompt(game_state_dict, player)
    parsed_planning_prompt = action_planning_prompt.format(
        AVAILABLE_ACTIONS=available_actions_text,
        AVAILABLE_TARGETS=available_targets_text)
    plan = generate_text(parsed_base_prompt, parsed_planning_prompt)

    if print_chain_of_thought:
        print(plan)

    print(f"{str(player)} keeps thinking...")

    parsed_critic_prompt = action_plan_critic_prompt.format(
        AVAILABLE_ACTIONS=available_actions_text,
        AVAILABLE_TARGETS=available_targets_text, PLAN=plan)
    updated_plan = generate_text(parsed_base_prompt, parsed_critic_prompt)

    if print_chain_of_thought:
        print(updated_plan)

    print(f"{str(player)} has made a decision!")
    well_formed_output = False
    retry_n, target_action, target_player = 0, 0, 0
    while not well_formed_output and retry_n < max_retries:
        try:
            parsed_action_parser_prompt = action_parser_prompt.replace(
                "{AVAILABLE_ACTIONS}", available_actions_text).replace(
                "{AVAILABLE_TARGETS}", available_targets_text).replace(
                "{PLAN}", updated_plan)

            action_dict = generate_text(parsed_base_prompt,
                                        parsed_action_parser_prompt)

            action_dict = json.loads(action_dict)
            target_action = available_actions[
                min(int(action_dict["action"]), len(available_actions) - 1)]
            target_player = None if action_dict["target"] is None else int(action_dict["target"])
            well_formed_output = True
        except:  # will capture either generation of json parsing errors
            retry_n += 1
            print(f"Something failed during generation, retrying... (retry {retry_n})")
    return target_action, target_player
