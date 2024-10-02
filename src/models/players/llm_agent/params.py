# hparams for the llm based agents
llm_model = "gpt-4o-mini"
print_chain_of_thought = True  # turn off to not show the CoT process of the agents
max_retries = 5  # Max failed generation retries before returning default values
conversation_turns = 8  # Number of turns in the conversation between players
