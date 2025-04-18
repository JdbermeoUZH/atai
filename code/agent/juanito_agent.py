import os
import time
import json
import random

from knowledge_graphs.wikidata.WikiDataKG import WikiDataKG
from models.entity_prop_parser.EntityPropertyParser import EntityPropertyParser
from models.intent_classifier.InteractionTypeClassifier import InteractionTypeClassifier
from models.RedirectionAgent import RedirectionAgent
from agent.demo_agent import DemoBot
from regex_matchers.MediaQRegexMatcher import MediaQRegexMatcher
from regex_matchers.FactQRegexMatcher import FactQRegexMatcher
from regex_matchers.RecQRegexMatcher import RecQRegexMatcher
from utils.utils import get_args_config_file

# Load configurations
config_args = get_args_config_file(os.path.join('..', 'config.yaml'))
conversation_params = config_args['conversation_config']
wk_kg_params = conversation_params['knowledge_graphs']['wikidata']
crowd_sourcing_params = conversation_params['crowd_sourcing']
first_funnel_config = conversation_params['first_funnel_info']

url = config_args['chatroom_server']['url']  # url of the speakeasy server
listen_freq = conversation_params['listen_freq']


class JuanitoBot(DemoBot):
    def __init__(self, username, password):
        super().__init__(username, password)
        self.first_funnel_filter = InteractionTypeClassifier(
            train_examples_path=first_funnel_config['classifier_train_data'])

        self.redirection_agent = RedirectionAgent()

        self.entityParser = EntityPropertyParser(
            entity_exact_label_filepath=conversation_params['entity_parser']['match_ent_labels_filepath'],
            property_extended_label_filepath=conversation_params['entity_parser']['match_prop_labels_filepath'],
            model_type=conversation_params['entity_parser']['model_size'])

        self.wkdata_kg = WikiDataKG(
            kg_tuple_file_path=wk_kg_params['kg_filepath'],
            imdb2movienet_filepath=wk_kg_params['imdb2movinet_filepath'],
            entity_label_filepath=wk_kg_params['entity_labels_dict'],
            property_label_filepath=wk_kg_params['property_labels_dict'],
            property_extended_label_filepath=conversation_params['entity_parser']['match_prop_labels_filepath'],
            entity_emb_filepath=wk_kg_params['embeddings']['entity_emb_filepath'],
            entity_id_mapping=wk_kg_params['embeddings']['entity_id_mapping'],
            relation_emb=wk_kg_params['embeddings']['relation_emb'],
            relation_id_mapping=wk_kg_params['embeddings']['relation_id_mapping'],
            recomendation_rules_filepath=wk_kg_params['recommendations']['rec_rules_filepath']
        )

        self._template_answer = json.load(open(conversation_params['template_answer'], 'r'))
        self._template_rec_answer = json.load(open(conversation_params['recommendations']['rec_template_answer'], 'r'))
        self._media_q_regex_matcher = MediaQRegexMatcher()
        self._fact_q_regex_matcher = FactQRegexMatcher()
        self._rec_q_regex_matcher = RecQRegexMatcher()
        self._crowd_source_dict = json.load(open(crowd_sourcing_params['filepath'], 'r'))
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
                    all_messages = self.check_room_state(
                        room_id=room_id, since=0, session_token=self.session_token)['messages']

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

                                    if intent == "Conversation":
                                        self._respond_with_conversation(message['message'], room_id=room_id)

                                    elif intent == "Factual Question/Embedding/Crowdsourcing":
                                        self._respond_kg_question(message['message'], room_id=room_id)

                                    elif intent == "Media Question":
                                        self._respond_media_request(message['message'], room_id=room_id)

                                    elif intent == 'Recommendation Questions':
                                        self._respond_with_recommendation(message=message['message'], room_id=room_id)

                                except Exception as e:
                                    print(e)
                                    self.post_message(room_id=room_id, session_token=self.session_token,
                                                      message=self._sample_template_answer("overall_failure"))

            time.sleep(listen_freq)

    def _find_wikidata_entity_id_of_movies_in_string(self, message: str) -> list[str]:
        movie_wk_ent_id_list = []
        # Use entity linker to find named entities of interest and their respective wikidata ids
        spacy_ents, wkdata_ents = self.entityParser.return_wikidata_entities_w_entity_linkers(
            message, entities_of_interest=("WORK_OF_ART",), entity_filter=self.wkdata_kg.check_if_entity_is_movie)

        # Filter matched entities so far
        wkdata_ents = [wkdata_ent for wkdata_ent in wkdata_ents if
                       self.wkdata_kg.check_if_entity_is_movie(wkdata_ent)]

        movie_wk_ent_id_list += wkdata_ents

        # If no wikidata ent related to movies is detected, try to match the detected named entities to movies
        if len(movie_wk_ent_id_list) < 2:
            for ent in spacy_ents:
                # Try to match a wk_ent id
                movie_wk_ent_id_list.append(
                    self.wkdata_kg.get_wkdata_entid_based_on_label_match(ent.text, ent_type='movie'))

        if len(movie_wk_ent_id_list) < 2:
            # Try to find entities that match movie titles extracted with regex
            movie_list = self._rec_q_regex_matcher.match_string(message)
            movie_wk_ent_id_list = [self.wkdata_kg.get_wkdata_entid_based_on_label_match(extracted_str, ent_type='movie')
                               for extracted_str in movie_list]
            movie_wk_ent_id_list = [wkdata_ent for wkdata_ent in movie_wk_ent_id_list if wkdata_ent is not None]

        # Remove duplicates from the list
        movie_wk_ent_id_list = list(set(movie_wk_ent_id_list))

        return movie_wk_ent_id_list

    def _respond_with_conversation(self, message: str, room_id: str):
        self.post_message(room_id=room_id, session_token=self.session_token,
                          message=self.redirection_agent.small_talk_and_redirect_conversation(message))

    def _respond_kg_question(self, message: str, room_id: str):
        wk_ent_id = None
        wk_prop_id = None

        # Use phrasematcher on entire string to detect properties
        wk_prop_ids = self.entityParser.return_wikidata_properties(doc=message)

        # Only assign the entity if only one property is matched, otherwise it is too noisy
        if len(wk_prop_ids) == 1:
            wk_prop_id = wk_prop_ids[0]

        # Use spacy entity linkers to identify entities
        spacy_ents, wkdata_ents = self.entityParser.return_wikidata_entities_w_entity_linkers(
            doc=message, entities_of_interest=("PERSON", "WORK_OF_ART"),
            entity_filter=self.wkdata_kg.check_if_entity_movie_or_person)

        # If no entities were detected, then try to identify them via named entities detected
        if len(wkdata_ents) == 0 and len(spacy_ents) > 0:
            for ent in spacy_ents:
                # Try to match a wk_ent id
                wkdata_ents.append(
                    self.wkdata_kg.get_wkdata_entid_based_on_label_match(ent.text))

        # Filter matched entities so far
        wkdata_ents = [wkdata_ent for wkdata_ent in wkdata_ents if
                       self.wkdata_kg.check_if_entity_movie_or_person(wkdata_ent)]

        if len(wkdata_ents) == 1:
            wk_ent_id = wkdata_ents[0]

        # These are supposed to be simple questions. If more than one entity is mentioned, prompt the user
        #  to phrase an easier question
        elif len(wkdata_ents) > 1:
            self.post_message(room_id=room_id, session_token=self.session_token,
                              message=self._sample_template_answer('error_too_many_questions_fact_question'))
            return

        # Use regex pattern to match predicate and entity (works for simple patterns)
        if wk_prop_id is None or wk_ent_id is None:
            # Tell the user the search will take a bit longer
            self.post_message(room_id=room_id, session_token=self.session_token,
                              message=self._sample_template_answer('longer_wait'))

            entity_str, property_str = self._fact_q_regex_matcher.match_string(message)

            if wk_prop_id is None and property_str:
                wk_prop_id = self.wkdata_kg.get_wkdata_propid_based_on_label_match(property_str)

            if wk_ent_id is None and entity_str:
                wk_ent_id = self.wkdata_kg.get_wkdata_entid_based_on_label_match(entity_str, ent_type='person or movie')

        # If still no property was found with the regex and we have multiple from the PhraseMatcher,
        #  then pick one at random from the PhraseMatcher
        if wk_prop_id is None and len(wk_prop_ids) > 1:
            wk_prop_id = random.choice(wk_prop_ids)

        #################################################################################
        # By this point we should have found a property and an entity
        ################################################################################
        if wk_ent_id and wk_prop_id:
            entity_label = self.wkdata_kg.get_entity_label(wk_ent_id)
            property_label = self.wkdata_kg.get_property_label(wk_prop_id)

        else:
            # If not, we need to te the user we cannot answer the question and ask them to rephrase it
            self.post_message(room_id=room_id, session_token=self.session_token,
                              message=self._sample_template_answer('error_fact_question'))
            return

        # Try to answer with croud_sourcing data
        answered = self._using_crowd_sourced_data(
            room_id=room_id, entity_id=wk_ent_id, entity_label=entity_label,
            property_id=wk_prop_id, property_label=property_label)

        # If the question was answered with the crowdsourced dataset, stop
        if answered:
            return

        # If not answered with the dataset, retrieve answer from KG.
        # Get the object of the relation (wk_ent_id, wk_prop_id, object)
        answers = [os.path.basename(str(tuple_)) for tuple_ in self.wkdata_kg.kg.objects(
            self.wkdata_kg.namespaces.WD[wk_ent_id], self.wkdata_kg.namespaces.WDT[wk_prop_id])]

        # If the entity and property were identified but there is no object for it, answer it with embeddings
        if len(answers) == 0:
            # Tell the user the search will take a bit longer
            self.post_message(room_id=room_id, session_token=self.session_token,
                              message=self._sample_template_answer('longer_wait'))

            answered = self._respond_kg_question_using_embeddings(
                room_id=room_id, entity_id=wk_ent_id, entity_label=entity_label,
                property_id=wk_prop_id, property_label=property_label)

            if not answered:
                # Tell the user we do not know the answer
                self.post_message(
                    room_id=room_id, session_token=self.session_token,
                    message=self._sample_template_answer('error_dont_know_answer').format(
                        property=property_label, subject=entity_label)
                )

        # If there is a single object, we can query the objects label and answer the question directly
        elif len(answers) == 1:
            answer = answers[0]

            if answer.startswith('P') or answer.startswith('Q'):
                answer_label = self.wkdata_kg.get_entity_label(answers[0])
            else:
                answer_label = answer

            full_answer_str = self._sample_template_answer('fact_question').format(
                    property=property_label, subject=entity_label, object=answer_label)

            self.post_message(
                room_id=room_id, session_token=self.session_token,
                message=full_answer_str.encode('utf-8'))

        # If more than one entity is part of the answer, report it
        elif len(answers) > 1:
            answer_labels = ', '.join([self.wkdata_kg.get_entity_label(answer) for answer in answers])

            # Tell the user about the possible multiple answers:
            self.post_message(
                room_id=room_id, session_token=self.session_token,
                message=self._sample_template_answer('fact_question_multiple_answers').format(
                    property=property_label, subject=entity_label, objects=answer_labels))

    def _respond_kg_question_using_embeddings(
            self, room_id: str, entity_id: str, entity_label: str,
            property_id: str, property_label: str,
            top_k: int = 10, ptg_max_diff_top_k: float = 0.6, report_max: int = 4) -> bool:

        answer_labels = self.wkdata_kg.deduce_object_using_embeddings(
            entity_id, property_id, top_k, ptg_max_diff_top_k, report_max)

        if answer_labels:
            self.post_message(room_id=room_id, session_token=self.session_token,
                              message=self._sample_template_answer('embedding_question').format(
                                  property=property_label, subject=entity_label, objects=', '.join(answer_labels)))
            return True
        else:
            return False

    def _using_crowd_sourced_data(self, room_id: str, entity_id: str, entity_label: str,
                                  property_id: str, property_label: str) -> bool:
        # Check if the tuple (entity_id, property_id) are in the crowdsourced data
        if entity_id in self._crowd_source_dict.keys():
            if property_id in self._crowd_source_dict[entity_id].keys():
                answer_dict = self._crowd_source_dict[entity_id][property_id]

                # Give the answer to the user
                object_ = answer_dict['object']
                fleiss_kappa = answer_dict['inter_rater_agreement']
                n_support = answer_dict['support_votes']
                n_reject = answer_dict['reject_votes']

                if object_.startswith('Q'):
                    # Get the label of the object
                    object_ = self.wkdata_kg.get_entity_label(object_)

                transition_to_crowdsource = self._sample_template_answer('crowdsourced_answer')
                answer = f'The {property_label} of {entity_label} is {object_} - according to the crowd, ' \
                         f'who had an inter-rater agreement of {fleiss_kappa: 0.3f} in this batch. ' \
                         f'The answer distribution for this specific task was {n_support} support votes ' \
                         f'and {n_reject} reject votes.'

                self.post_message(room_id=room_id, session_token=self.session_token,
                                  message=transition_to_crowdsource)
                self.post_message(room_id=room_id, session_token=self.session_token,
                                  message=answer)

                return True

        return False

    def _respond_media_request(self, message: str, room_id: str):
        # Use entity linker to find named entities of interest and their respective wikidata ids
        spacy_ents, wkdata_ents = self.entityParser.return_wikidata_entities_w_entity_linkers(
            message, entities_of_interest=('PERSON',))

        # Try to get imdb_id of PERSON entities successfully linked to wikidata
        imdb_ids = []
        if len(wkdata_ents) > 0:
            for wk_ent_id in wkdata_ents:
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


        # If still no imdb ids where found, use regex patterns to extract relevant text and match to a KG entity label
        if len(imdb_ids) == 0:
            extracted_str = self._media_q_regex_matcher.match_string(message)
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
                              message=self._sample_template_answer('error_media_question'))

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

    def _respond_with_recommendation(self, message: str, room_id: str):
        movie_wk_ent_id = self._find_wikidata_entity_id_of_movies_in_string(message)

        if len(movie_wk_ent_id) == 0:
            self.post_message(room_id=room_id, session_token=self.session_token,
                              message=random.choice(self._template_rec_answer['movies_not_found']))
            return

        # Finding common criteria via queries takes some time, so notify the user of the wait
        self.post_message(room_id=room_id, session_token=self.session_token,
                          message=random.choice(self._template_rec_answer['longer_wait']))

        recs, movies_to_recommend = self.wkdata_kg.recommend_similar_movies_and_characateristics(movie_wk_ent_id)

        # If there is nothing to recommend, even though the films were identified, tell that to the user
        if recs == {} and len(movies_to_recommend) == 0:
            self.post_message(room_id=room_id, session_token=self.session_token,
                              message=random.choice(self._template_rec_answer['no_recommendation_of_criteria_or_movies']))
            return

        # If we reach this point, we have something to recommend to the user. Format the strings and post them
        movie_recommendation_str = ''
        criteria_recommendations_str = ''

        if len(movies_to_recommend) > 0:
            # Sample randomly the number of movies to recommend to have more variation during the interaction
            movies_to_recommend = movies_to_recommend[0:random.randint(2, len(movies_to_recommend))]
            movie_recommendation_template = random.choice(self._template_rec_answer['complement'])
            movie_recommendation_str = movie_recommendation_template.format(
                movie_list=', '.join(movies_to_recommend[:-1]) + f', and {movies_to_recommend[-1]}'
            )

        if recs != {}:
            sentence_start = random.choice(self._template_rec_answer['sentence_start'])
            sentence_subject = random.choice(self._template_rec_answer['subject'])
            criteria_recommendations = []
            for criteria, things_to_recommend in recs.items():
                rec_list = ', or '.join(things_to_recommend)
                criteria_recommendation = random.choice(
                    self._template_rec_answer[criteria]).format(rec_list=rec_list)
                criteria_recommendations.append(criteria_recommendation)

            criteria_recommendations = '; '.join(criteria_recommendations) if len(criteria_recommendations) > 1 else \
                criteria_recommendations[0]

            criteria_recommendations_str = f"{sentence_start} {sentence_subject} {criteria_recommendations}. "

        recommendation_str = criteria_recommendations_str + movie_recommendation_str

        self.post_message(
            room_id=room_id, session_token=self.session_token, message=recommendation_str.encode('utf-8')
        )

    def _sample_template_answer(self, interaction_type: str) -> str:
        return random.choice(self._template_answer[interaction_type])

    def _sample_template_rec_answer(self, interaction_type: str) -> str:
        return random.choice(self._template_answer[interaction_type])


if __name__ == '__main__':
    username_ = 'juandiego.bermeoortiz_bot'
    password_ = 'V2f80g-vpxEh7w'
    bot = JuanitoBot(username_, password_)



