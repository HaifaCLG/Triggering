import json

SECOND_LANG = 'Arabic'
SHARED_OTHER='4'
EN_TO_SECOND = 1
SECOND_TO_ENG = 2
SHARED = {'4': 'Shared Other', '6': 'Shared Arabic', '7': 'Shared English'}
LANGS={'0':'Arabizi','1':'English','2':'French','3':'Arabic','4':'Other'}
MIXED = 3
SHARED_ENG='7'
SHARED_AR='6'
class Corpus:
    def __init__(self, corpus_path: str, corpus_name: str):

        self._path = corpus_path
        self._corpus_name = corpus_name
        self._corpus = dict()
        self._cs = {'Both Directions': 0,
                    f'English->{SECOND_LANG}': 0,
                    f'{SECOND_LANG}->English': 0}
        self._shared_count = {'Shared Other': 0, 'Shared English': 0, f'Shared {SECOND_LANG}': 0}
        self._num_of_tokens = 0
        self._langs_count = {'Arabizi': 0,'English': 0, 'French': 0,'Arabic':0,'Other':0}
        self._num_of_sentences = 0
        self._shared_exp_num = 0

    def load_corpus(self):
        with open(self._path, 'r', encoding="utf8") as f:
            self._corpus = json.load(f)

    def count_cs(self, cs_instances: list[int]):
        for instance in cs_instances:
            if instance == EN_TO_SECOND:
                self._cs[f'English->{SECOND_LANG}'] += 1
                self._cs['Both Directions'] += 1
            elif instance == SECOND_TO_ENG:
                self._cs[f'{SECOND_LANG}->English'] += 1
                self._cs['Both Directions'] += 1

    @staticmethod
    def join_same(langs: list[str], label: str, second_label=''):
        new_list = list()
        for i in range(len(langs)):
            if i and langs[i] in {label, second_label} and langs[i - 1] in {label, second_label}:
                continue
            else:
                new_list.append(langs[i])
        return new_list

    def count_shared_expression(self, langs: list[str]):
        new_langs = self.join_same(langs, SHARED_ENG, SHARED_OTHER)
        new_langs = self.join_same(new_langs, SHARED_AR, SHARED_OTHER)
        for ind in range(len(new_langs)):
            if new_langs[ind] in SHARED.keys():
                self._shared_count[SHARED[new_langs[ind]]] += 1
                if ind and ((new_langs[ind - 1] == SHARED_ENG and new_langs[ind] == SHARED_AR) or
                            (new_langs[ind - 1] == SHARED_AR and new_langs[ind] == SHARED_ENG)):
                    self._shared_exp_num += 1

    def count_lang_tokens(self, langs: list[str]):
        for ind in range(len(langs)):
            if langs[ind] in LANGS.keys():
                self._langs_count[LANGS[langs[ind]]] += 1

    def count_all(self):
        self.load_corpus()
        for conv in self._corpus.keys():
            for i in range(len(self._corpus[conv])):
                utterance = self._corpus[conv][i]
                self._num_of_sentences += 1
                self.count_cs(utterance['cs'])
                self._num_of_tokens += len(utterance['langs'])
                self.count_lang_tokens(utterance['langs'])
                self.count_shared_expression(utterance['langs'])


    def write_report(self, report_path: str):
        self.count_all()
        text = self._corpus_name + ' Report\n\n'
        text += f'Number of sentences in corpus: {self._num_of_sentences}\n\n'
        text += f'Number of tokens in corpus: {self._num_of_tokens}\n\n'
        text += 'CS instances:\n'
        for k in self._cs.keys():
            text += f'{k}: {self._cs[k]}\n'
        text += '\nNumber of "Shared" tokens:\n'
        for k in self._shared_count.keys():
            text += f'{k}: {self._shared_count[k]}\n'
        text += f'All Shared: {sum(self._shared_count.values())}'
        text += '\n\nNumber of tokens and percentages:\n'
        for k in self._langs_count.keys():
            text += f'{k}: {self._langs_count[k]}  {round(self._langs_count[k]/self._num_of_tokens*100,2)}% \n'

        with open(report_path, 'w',encoding="utf8") as f:
            f.writelines(text)


#twitter = Corpus('twitter_corpus.json', 'Twitter Corpus')
#twitter.write_report('twitter_details.txt')
reddit = Corpus('reddit_corpus.json', 'Reddit Corpus')
reddit.write_report('reddit_details.txt')
