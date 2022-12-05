import os
import getpass

from agent.juanito_agent import JuanitoBot
from utils.utils import get_args_config_file


# Load configurations
config_args = get_args_config_file(os.path.join('..', 'config.yaml'))
conversation_params = config_args['conversation_config']
wk_kg_params = conversation_params['knowledge_graphs']['wikidata']
crowd_sourcing_params = conversation_params['crowd_sourcing']
first_funnel_config = conversation_params['first_funnel_info']

url = config_args['chatroom_server']['url']  # url of the speakeasy server
listen_freq = conversation_params['listen_freq']


if __name__ == '__main__':
    username_ = 'juandiego.bermeoortiz_bot'
    password_ = 'V2f80g-vpxEh7w'
    bot = JuanitoBot(username_, password_)

    password = getpass.getpass('Connect the instance to the Speakeasy server: [press enter]')
    bot.connect()

    reconnection_listening_attempts = 0

    try:
        bot.listen()
    except Exception as e:
        print(e)
        reconnection_listening_attempts += 1
        if reconnection_listening_attempts > 5:
            raise e
        bot.connect()
        bot.listen()

