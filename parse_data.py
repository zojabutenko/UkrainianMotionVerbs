# file to open corpus and parse sentences
import bz2
import tarfile
import re
from tqdm import tqdm
import pymorphy2
import argparse


def read_archive(filepath):
    if filepath.endswith('.tar.gz'):
        with tarfile.open(filepath, 'r:gz') as tar:
            for member in tar.getmembers():
                if member.isfile():
                    f = tar.extractfile(member)
                    if f:
                        for line in f:
                            yield line.decode('utf-8').strip()
    elif filepath.endswith('.bz2'):
        with bz2.open(filepath, 'rt') as bzf:
            for line in bzf:
                yield line.strip()
    else:
        with open(filepath, 'rt', encoding='utf-8') as f:
            for line in f:
                yield line.strip()


def find_verbs(line, verbs, lemmatized=False):
    """
    Function to find motion verbs from a txt file in a given sentence. 
    If a verb is found, it returns the index of the token and the sentence. Otherwise returns None.
    """
    if lemmatized:
        tokens = line.split(' ')
        for id, token in enumerate(tokens):
            if token in verbs:
                return id, line
    else:
        tokens = line.split(' ')
        lemmatized_tokens = [pymorphy2.MorphAnalyzer(lang='uk').parse(token)[0].normal_form for token in tokens]
        for id, token in enumerate(lemmatized_tokens):
            if token in verbs:
                return id, token, line
    return None


def parse_verblist(filepath):
    """
    Function to parse a file containing verbs and return a list of verbs.
    """
    verbs = []
    with open(filepath, 'r') as f:
        for line in f:
            # check if line contains multiple verbs
            if ',' in line:
                # Split the line by commas and strip whitespace
                split_verbs = [verb.strip() for verb in line.split(',')]
                verbs.extend(split_verbs)
                continue
            # If the line contains a single verb, strip whitespace
            verb = line.strip()
            if verb:  # Check if the line is not empty
                verbs.append(verb)
    return verbs


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--domain', type=str, choices=['web', 'fiction'], default='web',
                           help='Domain to parse: web or fiction')
    args = argparser.parse_args()

    domain = args.domain  
    output_file = 'all_found_contexts.txt'


    verbs_path = 'verbs_list.txt'
    verbs = parse_verblist(verbs_path)
    print(f'Parsed {len(verbs)} verbs from {verbs_path}')
    contexts = []

    if domain == 'fiction':
        filepath_lemmatized = 'fiction.lemmatized.shuffled.txt.bz2'
        filepath_tokenized = 'fiction.tokenized.shuffled.txt.bz2'
        lemmatized_data = read_archive(filepath_lemmatized)
        tokenized_data = read_archive(filepath_tokenized)

        counter = 0
        for i in lemmatized_data:
            counter += 1
            if counter >= 1000:
                break
            
            lemmatized_line = next(lemmatized_data)
            tokenized_line = next(tokenized_data)


            found_context = find_verbs(lemmatized_line, verbs, lemmatized=True)
            if found_context:
                id = found_context[0]
                try:
                    lemmatized_token = lemmatized_line.split(' ')[id]
                    token = tokenized_line.split(' ')[id]
                except IndexError:
                    print(f'IndexError: {id} for line: {lemmatized_line}, {tokenized_line}')
                    continue
                                
                contexts.append((tokenized_line, lemmatized_line, id, lemmatized_token, token))

    elif domain == 'web':
        filepath = 'ukr-ua_web_2019_1M/ukr-ua_web_2019_1M-sentences.txt'
        with open(filepath, 'r', encoding='utf-8') as f:
            sentences = f.readlines()
        
        sentences = [re.search(r'(\d+)\t(.+)', s).groups() for s in sentences]

        with open(output_file, 'a') as f:
            for id, sentence in tqdm(sentences):
                found_context = find_verbs(sentence, verbs, lemmatized=False)
                if found_context:
                    id, lem_token, line = found_context
                    token = sentence.split(' ')[id]
                    
                    context = (sentence, id, token, lem_token)
                    context = [str(item) for item in context]
                    f.write('\t'.join(context) + '\n')
            


if __name__ == '__main__':
    main()
