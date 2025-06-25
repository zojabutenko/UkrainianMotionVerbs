import stanza
from tqdm import tqdm
import json, re


def extract_prep(nlp, sentence, verb):
    """
    Function to extract the noun, preposition, and subject from a sentence
    given a verb. It uses the Stanza library for dependency parsing.
    :param nlp: Stanza NLP pipeline
    :param sentence: The sentence to analyze
    :param verb: The verb to find the noun, preposition, and subject for
    :return: A tuple containing the noun, preposition, and subject
    """

    doc = nlp(sentence)
    noun = None
    prep = None
    subj = None
    noun_id = None
    verb_id = None

    # First loop: Find the first occurrence of the verb
    for sent in doc.sentences:
        for word in sent.words:
            if word.text == verb:
                verb_id = word.id
                break
        if verb_id:
            break
    
    noun_case = None
    noun_lemma = None

    # Second loop: Find the noun (object) and subject related to the verb
    for sent in doc.sentences:
        for word in sent.words:
            if word.head == verb_id and word.deprel == 'obl':
                noun_id = word.id
                noun = word.text
                noun_lemma = word.lemma
                if word.feats:
                    m = re.search('Case=([A-Za-z]+)', word.feats)
                    if m:
                      noun_case = m.group(1)
            if word.head == verb_id and word.deprel == 'nsubj':
                subj = word.text

    # Third loop: Find the preposition related to the noun
    for sent in doc.sentences:
        for word in sent.words:
            if word.head == noun_id and word.deprel == 'case':
                prep = word.text
                break  # Stop after finding the first preposition

    
    # Return a tuple containing the noun, preposition, and subject.
    # If no noun, preposition, or subject is found, their values will be None.
    return noun, prep, subj, noun_case, noun_lemma


def load_verb_prefix_map(filepath='verb_prefix_map.json'):
    with open(filepath, 'r', encoding='utf-8') as f:
        return dict(json.load(f))
    

def extract_prefix(verb_lemma, verb_map):
    """
    :param verb_lemma: str - the prefixed verb to look up
    :param verb_map: dict - loaded verb_prefix_map
    :return: (prefix, base_verb) or (None, None)
    """
    result = verb_map.get(verb_lemma)
    
    return tuple(result) if result else (None, None)


def main():
    output_file = 'extracted_dependencies.txt'

    nlp = stanza.Pipeline(lang='uk', processors='tokenize,pos,lemma,depparse')

    file_path = 'all_found_contexts.txt'

    with open(file_path, 'r') as file:
        lines = file.readlines()
        data = [x.split('\t') for x in lines]


    with open(output_file, 'w') as output:
        for d in tqdm(data):
            lemma = d[3].strip()  # Assuming the verb is in the 4th column (index 3)
            verb = d[2].strip()
            sentence = d[0].strip()
            id = d[1].strip()
            obj, prep, subj, obj_case, obj_lemma = extract_prep(nlp, sentence, verb)
            prefix, stem = extract_prefix(lemma, load_verb_prefix_map())

            output.write(f"{sentence}\t{id}\t{verb}\t{lemma}\t{prefix}\t{stem}\t{subj}\t{prep}\t{obj}\t{obj_case}\t{obj_lemma}\n")
    

if __name__ == '__main__':
    main()
