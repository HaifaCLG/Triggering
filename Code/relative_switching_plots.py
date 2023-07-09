import json
from scipy.stats import fisher_exact
import plotly.graph_objects as go

# Languages:
SHARED_ENG = '7'
SHARED_AR = '6'
SHARED_OTHER = '4'
AR = '0'
EN = '1'
SHARED = {SHARED_ENG, SHARED_AR, SHARED_OTHER}

shared_names = {'6': 'Shared Arabic', '7': 'Shared English', '4': 'Shared Other'}
DIRECTIONS = {'[1, 2]': 'Both directions', '[1]': 'English->Arabic', '[2]': 'Arabic->English'}
AREAS = {-1: 'Shared before CS', 0: 'Shared around CS', 1: 'Shared after CS'}


class SharedAndCS:

    def __init__(self, corpus_path, name):
        self._corpus = self.load_corpus(corpus_path)
        self._langs, self._cs = self.load_langs_and_cs()
        self._name = name

    @staticmethod
    def load_corpus(path) -> dict[int, list[dict]]:
        with open(path, 'r', encoding="utf8") as f:
            corpus = json.load(f)
        return corpus

    def load_langs_and_cs(self) -> (list[str], list[int]):
        langs, cs = list(), list()
        for conv in self._corpus.values():
            for utterance in conv:
                langs.append(utterance['langs'])
                cs.append(utterance['cs'])
        return langs, cs

    @staticmethod
    def check_cs(langs):
        cs = list()
        prev = ''
        for lang in langs:
            if prev == EN and lang == AR:
                cs.append(1)
            elif prev == AR and lang == EN:
                cs.append(2)
            else:
                cs.append(0)
            if lang in [EN, AR]:
                prev = lang
        return cs

    @staticmethod
    def check_instance_cs(cs_arr, ind: int, gap: int,
                          area: int, direction) -> bool:
        # Noice that when we changed the anchor to cs - we should reverse the area
        if area == 1:
            indices = [ind - k - 1 for k in range(min(ind, gap))]
        elif area == 0:
            indices = [ind - k - 1 for k in range(min(ind, gap))] + \
                      [ind + k + 1 for k in range(min(len(cs_arr) - ind - 1, gap))]
        else:
            indices = [ind + k + 1 for k in range(min(len(cs_arr) - ind - 1, gap))]
        for k in indices:
            if cs_arr[k] in direction:
                return True
        return False


    @staticmethod
    def modify_labels(lang_arr):
        First_lang = SHARED_AR
        Second_lang = SHARED_ENG
        new_lang = list()
        new_lang.append(lang_arr[0])
        for i in range(1, len(lang_arr)):
            if (lang_arr[i] not in SHARED) or (lang_arr[i] in SHARED and lang_arr[i - 1] != lang_arr[i]):
                new_lang.append(lang_arr[i])
        tmp_lang = list()
        tmp_lang.append(new_lang[0])
        for i in range(1, len(new_lang)):
            if (new_lang[i] == SHARED_OTHER):
                if not (new_lang[i - 1] in [First_lang, Second_lang]):
                    tmp_lang.append(new_lang[i])
            else:
                tmp_lang.append(new_lang[i])

        new_lang = list.copy(tmp_lang)
        tmp_lang = list()
        for i in range(0, (len(new_lang) - 1)):
            if new_lang[i] == SHARED_OTHER:
                if not (new_lang[i + 1] in [First_lang, Second_lang]):
                    tmp_lang.append(new_lang[i])
            else:
                tmp_lang.append(new_lang[i])
        tmp_lang.append(new_lang[-1])
        return tmp_lang

    def count_instances_by_shared(self, gap: int, area: int, what_shared: set, direction: list[int]):
        shared_cs, not_shared_cs, shared_not_cs, not_shared_not_cs = 0, 0, 0, 0
        for i in range(len(self._langs)):
            new_langs = self.modify_labels(self._langs[i])
            new_cs = self.check_cs(new_langs)
            updated_cs = self.update_cs_in_utterance(new_cs)
            # try for updated cs (take care of insertion)
            new_cs = updated_cs
            # get rid of the first and the last tag
            for j in range(1, len(new_langs) - 1):
                if new_langs[j] in what_shared:
                    if self.check_instance_cs(new_cs, j, gap, area, direction):
                        shared_cs += 1
                    else:
                        shared_not_cs += 1
                else:
                    if self.check_instance_cs(new_cs, j, gap, area, direction):
                        not_shared_cs += 1
                    else:
                        not_shared_not_cs += 1
        return shared_cs, not_shared_cs, shared_not_cs, not_shared_not_cs


    def test_stats_instances(self, gap: int, area: int, what_shared: set, direction: list[int]):
        stats = self.count_instances_by_shared(gap, area, what_shared, direction)
        table = [[stats[0], stats[2]], [stats[1], stats[3]]]
        fisher_object = fisher_exact(table)
        p_val = fisher_object.pvalue
        odds = fisher_object.statistic
        rr = (stats[0] / (stats[0] + stats[2])) / (stats[1] / (stats[1] + stats[3]))
        return p_val, odds, rr

    @staticmethod
    def update_cs_in_utterance(cs: list[int]) -> list[int]:
        new_cs = list(cs)
        for i in range(len(cs)):
            if cs[i] and (i > 0 and new_cs[i - 1]):
                new_cs[i] = 0
        return new_cs

    def get_data_to_plot(self, shared_set: set):
        data = {'[1, 2]-1': {'rr': list(), 'p_val': list(), 'color': '#8AC926', 'dash': False,
                             'name': 'All Switches Following <i>Shared</i>'},
                '[1, 2]0': {'rr': list(), 'p_val': list(), 'color': '#8AC926', 'dash': True,
                            'name': 'All Switches Near <i>Shared</i>'},
                '[1]-1': {'rr': list(), 'p_val': list(), 'color': '#FFCA3A', 'dash': False,
                          'name': 'EN->AR Switches Following <i>Shared</i>'},
                '[1]0': {'rr': list(), 'p_val': list(), 'color': '#FFCA3A', 'dash': True,
                         'name': 'EN->AR Switches Near <i>Shared</i>'},
                '[2]-1': {'rr': list(), 'p_val': list(), 'color': '#FF595E', 'dash': False,
                          'name': 'AR->EN Switches Following <i>Shared</i>'},
                '[2]0': {'rr': list(), 'p_val': list(), 'color': '#FF595E', 'dash': True,
                         'name': 'AR->EN Switches Near <i>Shared</i>'}}
        for direction in [[1, 2], [1], [2]]:
            for area in [-1, 0]:
                for gap in range(1, 7):
                    p, o, rr = self.test_stats_instances(gap, area, shared_set, direction)
                    data[str(direction) + str(area)]['rr'].append(rr)
                    data[str(direction) + str(area)]['p_val'].append(p)
        return data

    @staticmethod
    def shared_name(shared_set: set):
        shared_names = {SHARED_ENG: 'Shared-English',
                        SHARED_AR: 'Shared-Arabic',
                        SHARED_OTHER: 'Shared-Other'}
        if len(shared_set) == 1:
            return shared_names[list(shared_set)[0]]
        return 'All Shared Items'

    def plot_all_rr(self):
        gaps = [1, 2, 3, 4, 5, 6]
        for shared in [{SHARED_ENG, SHARED_AR, SHARED_OTHER}, {SHARED_ENG}, {SHARED_AR}, {SHARED_OTHER}]:
            sh = self.shared_name(shared)
            data = self.get_data_to_plot(shared)
            fig = go.Figure()
            for elem in data.keys():
                if data[elem]['dash']:
                    fig.add_trace(go.Scatter(x=gaps, y=data[elem]['rr'], name=data[elem]['name'],
                                             line=dict(color=data[elem]['color'], width=4, dash='dash'), mode='lines'))
                else:
                    fig.add_trace(go.Scatter(x=gaps, y=data[elem]['rr'], name=data[elem]['name'],
                                             line=dict(color=data[elem]['color'], width=4), mode='lines'))
                fig.add_trace(go.Scatter(x=[gaps[i - 1] if data[elem]['p_val'][i - 1] > 0.05 else None for i in gaps],
                                         y=[data[elem]['rr'][i - 1] if data[elem]['p_val'][i - 1] > 0.05 else None for i
                                            in gaps],
                                         marker=dict(color='black', size=11, symbol='diamond'),
                                         mode='markers', showlegend=False))
                fig.add_trace(go.Scatter(x=[gaps[i - 1] if data[elem]['p_val'][i - 1] <= 0.05 else None for i in gaps],
                                         y=[data[elem]['rr'][i - 1] if data[elem]['p_val'][i - 1] <= 0.05 else None for
                                            i in gaps],
                                         marker=dict(color=data[elem]['color'], size=7, symbol='circle'),
                                         mode='markers', showlegend=False))
            fig.add_hline(y=1)
            fig.update_layout(
                title_text=f'<b>Relative Switching Propensity as a Function of Distance</b><br><b>Corpus:</b> {self._name}; <b><i>Shared</i> Items:</b> {sh}',
                xaxis_title='Distance (#tokens)',
                yaxis_title='Relative switching propensity',
                font=dict(family='Tahoma', size=18))
            fig.show()
            print('fig ' + 'rr_plotly_' + self._name + '_' + sh + ' appears in chrome')


#twitter_corpus = SharedAndCS('twitter_corpus.json', 'Twitter')
#twitter_corpus.plot_all_rr()

reddit_corpus = SharedAndCS('reddit_corpus.json', 'Reddit')
reddit_corpus.plot_all_rr()
