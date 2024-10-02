import os

from autogen import ConversableAgent, GroupChatManager
from autogen.agentchat.groupchat import GroupChat
from openai import InternalServerError

from src.models.players.llm_agent.prompts import *
from src.models.players.llm_agent.prompt_utils import parse_base_prompt, get_player_index
from src.models.players.llm_agent.params import max_retries, conversation_turns, llm_model

openai_key = os.environ.get("OPENAI_API_KEY")
llm_config = {"model": llm_model, "api_key": openai_key}


def generate_players_chat(game_state_dict: dict) -> GroupChat:
    """Players will engage in a multi turn conversation plotting, bantering, bluffing and planning their next move

    The conversation is conditioned in the current game state and in the events of the previous turns

    Each player will have a different "persona" meaning that will interact differently with each other
    """
    players = game_state_dict["players"]
    chatting_agents = []
    for i, player in enumerate(players):
        parsed_base_prompt = parse_base_prompt(game_state_dict, player)
        system_prompt = parsed_base_prompt + chat_prompt
        player_index = get_player_index(game_state_dict["players"], str(player))
        persona_name = persona_names[player_index]
        agent = ConversableAgent(
            name=f"{str(player)}-{persona_name}",
            system_message=system_prompt,
            llm_config=llm_config,
            human_input_mode="NEVER",
        )
        chatting_agents.append(agent)

    group_chat = GroupChat(
        agents=chatting_agents,
        messages=[],
        max_round=conversation_turns,
        allow_repeat_speaker=False,
        speaker_selection_method="random",
    )

    group_chat_manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
    )

    chat_result = ""
    retry_n = 0
    while not chat_result and retry_n < max_retries:
        try:
            chat_result = chatting_agents[0].initiate_chat(
                group_chat_manager,
                summary_method="reflection_with_llm",
                message="Lets talk about the game!"
            )
        except InternalServerError:
            retry_n += 1
            print(f"Chat failed. The model might have produced invalid content. Retrying... (retry {retry_n}).")
            # Note: The generation fails quite often due to invalid content. This might be due to the bantering
            # persona producing inappropriate content
    return chat_result
