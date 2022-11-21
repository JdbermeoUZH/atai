import os
import time
import json
import random
import getpass

from knowledge_graphs.WikiDataKG import WikiDataKG
from models.EntityParser import EntityParser
from models.InteractionTypeClassifier import InteractionTypeClassifier
from demo_agent import DemoBot
from utils.utils import get_args_config_file

# Load configurations
config_args = get_args_config_file(os.path.join('..', 'config.yaml'))
conversation_params = config_args['conversation_config']
first_funnel_config = conversation_params['first_funnel_info']

url = config_args['chatroom_server']['url']  # url of the speakeasy server
listen_freq = conversation_params['listen_freq']


class JuanitoBot(DemoBot):
    def __init__(self, username, password):
        super().__init__(username, password)
        self.first_funnel_filter = InteractionTypeClassifier(
            train_examples_path=first_funnel_config['classifier_train_data'])
        self.entityParser = EntityParser(model_type=conversation_params['entity_parser']['model_size'])
        self.wkdata_kg = WikiDataKG(
            kg_tuple_file_path=conversation_params['knowledge_graphs']['wikidata_kg_filepath'],
            imdb2movienet_filepath=conversation_params['knowledge_graphs']['wikidata_kg_filepath']
        )
        self._template_answer = json.load(open(conversation_params['template_answer'], 'r'))

    def listen(self):
        while True:
            # check for all chatrooms
            current_rooms = self.check_rooms(session_token=self.session_token)['rooms']
            for room in current_rooms:
                # ignore finished conversations
                if room['remainingTime'] > 0:
                    room_id = room['uid']
                    if not self.chat_state[room_id]['initiated']:
                        # send a welcome message and get the alias of the agent in the chatroom
                        self.post_message(
                            room_id=room_id, session_token=self.session_token,
                            message='Hi, how are you doing? If you have any questions about movies, please let me know')
                        self.chat_state[room_id]['initiated'] = True
                        self.chat_state[room_id]['my_alias'] = room['alias']

                    # check for all messages
                    all_messages = self.check_room_state(room_id=room_id, since=0, session_token=self.session_token)['messages']

                    # you can also use ["reactions"] to get the reactions of the messages: STAR, THUMBS_UP, THUMBS_DOWN

                    for message in all_messages:
                        if message['authorAlias'] != self.chat_state[room_id]['my_alias']:

                            # check if the message is new
                            if message['ordinal'] not in self.chat_state[room_id]['messages']:
                                # Add message to list of messages of the agent
                                self.chat_state[room_id]['messages'][message['ordinal']] = message

                                # Classify the intent or type of interaction requested in the message
                                intent = self.first_funnel_filter(message['message'])

                                if intent == "Conversation":
                                    response = self._respond_with_conversation()

                                elif intent == "Factual Question/Embedding/Crowdsourcing":
                                    response = self._respond_KG_question()

                                elif intent == "Media Question":
                                    self._respond_media_request(message['message'], room_id=room_id)

                                elif intent == 'Recommendation Questions':
                                    response = self._respond_with_recommendation()

                                else:
                                    response = "Sorry I don't really understand what you mean," \
                                               " could you please phrase it in simpler terms?"
                                #print('\t- Chatroom {} - new message #{}: \'{}\' - {}'.format(room_id, message['ordinal'], message['message'], self.get_time()))

                                ##### You should call your agent here and get the response message #####
                                self.post_message(room_id=room_id, session_token=self.session_token, message=response)
            time.sleep(listen_freq)

    def _respond_with_conversation(self):
        print("Use conversational model")
        return "Use conversational model"

    def _respond_KG_question(self):
        print("Answer question using the KGs available")
        return "Answer question using the KGs available"

    def _respond_media_request(self, message: str, room_id: str):
        ent_imdb_id = None
        movienet_id = None
        # Use entity linker to find named entities of interest and their respective wikidata ids
        spacy_proc_doc, spacy_ents, wkdata_ents = self.entityParser.return_wikidata_entities(
            message, entities_of_interest=('PERSON', 'WORK_OF_ART'))

        # If one entity is returned with a wikidata ID, then pull it's IMDB id
        if len(wkdata_ents) == 1:
            # Check the detected entity is in fact contained in the graph
            ent_wk_id = list(wkdata_ents.keys())[0]
            if self.wkdata_kg.check_if_entity_in_kg(wk_ent_id=ent_wk_id):
                # Get IMDB ID of the entity
                ent_imdb_id = self.wkdata_kg.get_imdb_id(ent_wk_id)

        # If no entities where linked to wikidata, then compare entities detected to all nodes in KG. Pick one with high enough similarity

        # If not one a single one matched, then try matching a known regex pattern and rerun the search

        # If it fails, sample an error message of media request

        if ent_imdb_id:
            # Map the IMDB id to Movinet's ID
            movienet_id = self.wkdata_kg.get_movinet_id(ent_imdb_id)

        if movienet_id:
            self.post_message(room_id=room_id, session_token=self.session_token, message=f'image:{movienet_id}')
        else:
            self.post_message(room_id=room_id, session_token=self.session_token,
                              message=self._sample_template_answer('media_question'))

    def _respond_with_recommendation(self):
        print("Recommend a collection of movies using the KG")
        return "Recommend a collection of movies using the KG"

    def _sample_template_answer(self, interaction_type: str) -> str:
        return random.choice(self._template_answer[interaction_type])

if __name__ == '__main__':
    username = 'juandiego.bermeoortiz_bot'
    password = 'V2f80g-vpxEh7w'
    #password = getpass.getpass('Password of the demo bot:')
    bot = JuanitoBot(username, password)

    a = bot._respond_media_request("I want to see a picture of Julia Roberts")

    bot.listen()

