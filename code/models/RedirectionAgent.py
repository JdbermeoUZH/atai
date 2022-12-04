from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


class RedirectionAgent:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/GODEL-v1_1-base-seq2seq")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("microsoft/GODEL-v1_1-base-seq2seq")

    def _generate(self, instruction, knowledge, dialog):
        if knowledge != '':
            knowledge = '[KNOWLEDGE] ' + knowledge

        dialog = ' EOS '.join(dialog)
        query = f"{instruction} [CONTEXT] {dialog} {knowledge}"
        input_ids = self.tokenizer(f"{query}", return_tensors="pt").input_ids
        outputs = self.model.generate(input_ids, max_length=128, min_length=8, top_p=0.9, do_sample=True)
        output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        return output

    def small_talk_and_redirect_conversation(self, message) -> str:
        instruction = f'Instruction: given a dialog context, respond basic questions or small talk ' \
                      f'and always change the conversation to movies or films'
        knowledge = ''
        dialog = [
            'hi',
            'Hey! how is it going?',
            'All good, thanks, can you tell me a story?',
            'I really rather talk about movies',

            message
        ]

        return self._generate(instruction, knowledge, dialog)