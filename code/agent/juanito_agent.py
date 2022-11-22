import os
import re
import time
import json
import random

from knowledge_graphs.WikiDataKG import WikiDataKG
from models.EntityParser import EntityParser
from models.InteractionTypeClassifier import InteractionTypeClassifier
from demo_agent import DemoBot
from utils.utils import get_args_config_file
from regex_matchers.MediaQRegexMatcher import MediaQRegexMatcher

# Load configurations
config_args = get_args_config_file(os.path.join('..', 'config.yaml'))
conversation_params = config_args['conversation_config']
wk_kg_params = conversation_params['knowledge_graphs']['wikidata']
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
            kg_tuple_file_path=wk_kg_params['kg_filepath'],
            imdb2movienet_filepath=wk_kg_params['imdb2movinet_filepath'],
            entity_label_filepath=wk_kg_params['entity_labels_dict'],
            property_label_filepath=wk_kg_params['property_labels_dict']
        )
        self._template_answer = json.load(open(conversation_params['template_answer'], 'r'))
        self._media_q_regex_matchers = MediaQRegexMatcher()
        print('Ready to go!')

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

                                try:
                                    # Add message to list of messages of the agent
                                    self.chat_state[room_id]['messages'][message['ordinal']] = message

                                    # Classify the intent or type of interaction requested in the message
                                    intent = self.first_funnel_filter(message['message'])

                                    ##### You should call your agent here and get the response message #####
                                    if intent == "Conversation":
                                        response = self._respond_with_conversation()

                                    elif intent == "Factual Question/Embedding/Crowdsourcing":
                                        response = self._respond_KG_question()

                                    elif intent == "Media Question":
                                        self._respond_media_request(message['message'], room_id=room_id)
                                        response = None

                                    elif intent == 'Recommendation Questions':
                                        response = self._respond_with_recommendation()

                                    else:
                                        response = "Sorry I don't really understand what you mean," \
                                                   " could you please phrase it in simpler terms?"

                                    if response:
                                        self.post_message(room_id=room_id, session_token=self.session_token,
                                                          message=response)

                                except Exception as e:
                                    print(e)
                                    self.post_message(room_id=room_id, session_token=self.session_token,
                                                      message=self._sample_template_answer("failure"))

            time.sleep(listen_freq)

    def _respond_with_conversation(self, message: str, room_id: str):
        print("Use conversational model")
        return "Use conversational model"

    def _respond_KG_question(self, message: str, room_id: str):
        wk_ent_id = None
        wk_pred_id = None
        # TODO: Use regex pattern to match predicate and entity

        # If it fails, try to identify with property and entities with pretrained entity linkers

        # If it fails, ask for rephrasing of the question

        # Query the graph for an answer

        # If the no answer is found, answer it with embeddings
        self._respond_KG_question_using_embeddings(message=message, room_id=room_id,
                                                   entity_id=wk_ent_id, predicate_id=wk_pred_id)

        # If more than one answer is found, answer it with crowd source data
        self._respond_KG_question_using_crowd_kg(message=message, room_id=room_id, entity_id=wk_ent_id,
                                                 predicate_id=wk_pred_id)

        # If still no answer is found, pull data from the entity and use a QA model
        print("Answer question using the KGs available")
        return "Answer question using the KGs available"

    def _respond_KG_question_using_embeddings(self, message: str, room_id: str, entity_id: str, predicate_id: str):
        response = "Use emebddings"
        print(response)
        return response

    def _respond_KG_question_using_crowd_kg(self, message: str, room_id: str, entity_id: str, predicate_id: str):
        response = "Use crowd kg"
        print(response)
        return response

    def _respond_media_request(self, message: str, room_id: str):
        # Use entity linker to find named entities of interest and their respective wikidata ids
        spacy_proc_doc, spacy_ents, wkdata_ents = self.entityParser.return_wikidata_entities(
            message, entities_of_interest=('PERSON',))

        # Try to get imdb_id of PERSON entities successfully linked to wikidata
        imdb_ids = []
        if len(list(wkdata_ents.keys())) > 0:
            for wk_ent_id in wkdata_ents.keys():
                imdb_id = self.wkdata_kg.get_imdb_id(wk_ent_id=wk_ent_id)
                if imdb_id:
                    # add imdb_id to the list
                    imdb_ids.append(imdb_id)

        # If no entities where linked to wikidata or no imdb_ids were found, then try to match named entities detected
        if len(imdb_ids) == 0 and len(spacy_ents) >= 1:
            for ent in spacy_ents:
                # Try to match a wk_ent id
                wk_ent_id = self.wkdata_kg.get_wkdata_entid_based_on_label_match(ent.text, ent_type='person')
                imdb_id = self.wkdata_kg.get_imdb_id(wk_ent_id=wk_ent_id) if wk_ent_id else None
                if imdb_id is not None:
                    imdb_ids.append(imdb_id)

        # Tell the user the search will take a bit longer
        self.post_message(room_id=room_id, session_token=self.session_token,
                          message=self._sample_template_answer('longer wait'))

        # If still no imdb ids where found, use regex patterns to extract relevant text and match to a KG entity label
        if len(imdb_ids) == 0:
            extracted_str = self._media_q_regex_matchers.match_string(spacy_proc_doc.text)
            wk_ent_id = self.wkdata_kg.get_wkdata_entid_based_on_label_match(extracted_str, ent_type='person') \
                if extracted_str else None
            imdb_id = self.wkdata_kg.get_imdb_id(wk_ent_id=wk_ent_id) if wk_ent_id else None
            if imdb_id is not None:
                imdb_ids.append(imdb_id)

        if len(imdb_ids) > 0:
            self._display_imdb_ids(imdb_ids, room_id)
        else:
            # If it was not possible to find an image, sample an error message of type media request
            self.post_message(room_id=room_id, session_token=self.session_token,
                              message=self._sample_template_answer('media_question'))

    def _display_imdb_ids(self, imdb_ids: list, room_id: str) -> None:
        # Display images of movienet_ids found
        movienet_ids = [self.wkdata_kg.get_movinet_id(imdb_id) for imdb_id in imdb_ids
                        if self.wkdata_kg.get_movinet_id(imdb_id) is not None]
        if len(movienet_ids) == 1:
            self.post_message(room_id=room_id, session_token=self.session_token, message=f'image:{movienet_ids[0]}')

        else:
            self.post_message(room_id=room_id, session_token=self.session_token,
                              message='I found these photos of the people you mentioned ')
            for movienet_id in movienet_ids:
                self.post_message(room_id=room_id, session_token=self.session_token, message=f'image:{movienet_id}')

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
    #bot._respond_media_request("Show me a picture of Julia Roberts", 'roomid')
    bot.listen()

