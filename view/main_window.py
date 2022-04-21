import json
import os
import time
import tkinter
import tkinter as tk
from tkinter import END
from tkinter.filedialog import askopenfilename, asksaveasfilename, asksaveasfile

import nltk
import spacy
from PIL import Image
from nltk.corpus import wordnet as wn
from nltk.draw import TreeWidget
from nltk.draw.util import CanvasFrame

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('universal_tagset')
nltk.download('omw-1.4')
nltk.download('wordnet')


class MainWindow:
    def __init__(self):
        self._window = tk.Tk()
        self._is_window_opened = False
        self._tree_frame = tkinter.Frame(self._window)
        self._dictionary_documentation_txt_edit = tk.Text(self._window)
        self._text_field = tkinter.Text(self._window)
        self._generate_button = tkinter.Button(self._window, text="Run analysis", command=self.draw_semantic_tree)
        self._left_frame_buttons = tk.Frame(self._window)
        self._dictionary_documentation_label = tk.Label(self._window, text="History")
        self._button_open = tk.Button(self._left_frame_buttons, text="Open file", command=self.open_file)
        self._save_button = tk.Button(self._left_frame_buttons, text="   Save tree   ",
                                      command=self.save_json)

        self._button_help = tk.Button(self._left_frame_buttons, text="   Help   ",
                                      command=self.about)
        self._nlp = spacy.load("en_core_web_sm")
        self._canvas = CanvasFrame(self._tree_frame, width=770, height=500)
        self._canvas.pack()

    def start(self):
        self._configure_window()
        self._window.mainloop()
        return

    def _configure_window(self):
        self._window.title("Syntax text analysis")

        self._left_frame_buttons.grid(row=0, column=0, rowspan=2, sticky="ns")
        self._button_open.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self._save_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self._button_help.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self._text_field.grid(row=0, column=1, sticky="ns", padx=5, pady=5)
        self._text_field.configure(height=2, border=3)
        self._generate_button.grid(row=0, column=2, sticky="ns", padx=5, pady=5)

        self._tree_frame.grid(row=1, column=1, rowspan=3, columnspan=6, sticky="nsew")

        self._dictionary_documentation_label.grid(row=2, column=0, ipady=5)
        self._dictionary_documentation_txt_edit.grid(row=3, column=0, sticky="e", ipady=5)
        self._dictionary_documentation_txt_edit.configure(width=25, borderwidth=10)

    def open_file(self):
        filepath = askopenfilename(
            filetypes=[("Текстовый документ", "*.txt")]
        )
        if not filepath:
            return
        file = open(filepath)
        file_content = file.read()
        self._text_field.insert("1.0", file_content)
        return

    @staticmethod
    def about():
        tk.messagebox.showinfo("Help",
                               "To start, open text file or enter your sentence.\nEnglish language.\nSemantic parsed tree will generated.")
        return

    def save_json(self):
        f = asksaveasfile(defaultextension=".json")

        doc = nltk.word_tokenize(self._text_field.get(1.0, END))
        data_set: dict

        items = []

        for word in doc:
            print(word)
            data = {"syn": self.get_synonims(word), "ant": self.get_synonims(word), "hypon": self.get_hyponyms(word),
                    "hyper": self.get_hypernyms(word)}

            items.append({"name" : word, "data" : data})

        json_dump = json.dumps(items)

        f.write(json_dump)

        return

    def draw_semantic_tree(self):
        self._canvas.canvas().delete("all")
        start = time.time()
        text = self._text_field.get(1.0, END)
        text = text.replace('\n', '')
        if text != '':
            sentences = nltk.sent_tokenize(text)
            self._canvas.canvas().update()
            result = '(S '
            for sent in sentences:
                sent = sent.replace('.', '')
                sent = sent.replace(',', '')
                sent = sent.replace('?', '')
                doc = nltk.word_tokenize(sent)
                result_sent = '(SENT '
                for word in doc:
                    result_sent += self.get_word_semantic(word)
                result_sent += ')'
                result += result_sent
            result += ')'
            result = nltk.tree.Tree.fromstring(result)
            widget = TreeWidget(self._canvas.canvas(), result)
            widget['node_font'] = 'arial 10 bold'
            widget['leaf_font'] = 'arial 10'
            widget['node_color'] = '#005990'
            widget['leaf_color'] = '#3F8F57'
            widget['line_color'] = '#175252'
            self._canvas.add_widget(widget, 50, 10)

            self._dictionary_documentation_txt_edit.insert(tkinter.END, self._text_field.get("1.0", END) + "\n")
        finish = time.time()
        delta = finish - start
        print('draw tree: ', delta)
        return

    @staticmethod
    def get_word_semantic(word: str) -> str:
        start = time.time()
        if len(wn.synsets(word)) == 0:
            return '(WS (W ' + word + '))'
        result = '(WS (W ' + word + ') (DEF ' + wn.synsets(word)[0].definition().replace(' ', '_') + ')'
        synonyms, antonyms, hyponyms, hypernyms = [], [], [], []
        word = wn.synsets(word)
        syn_app = synonyms.append
        ant_app = antonyms.append
        he_app = hyponyms.append
        hy_app = hypernyms.append
        for synset in word:
            for lemma in synset.lemmas():
                syn_app(lemma.name())
                if lemma.antonyms():
                    ant_app(lemma.antonyms()[0].name())
        for hyponym in word[0].hyponyms():
            he_app(hyponym.name())
        for hypernym in word[0].hypernyms():
            hy_app(hypernym.name())
        if len(synonyms):
            result += ' (SYN '
            for synonym in synonyms:
                result += synonym + ' '
        if len(antonyms):
            result += ') (ANT '
            for antonym in antonyms:
                result += antonym + ' '
        if len(hyponyms):
            result += ') (HY '
            for hyponym in hyponyms:
                result += hyponym + ' '
        if len(hypernyms):
            result += ') (HE '
            for hypernym in hypernyms:
                result += hypernym + ' '
        result += '))'
        print('get word semantic', time.time() - start)
        return result

    def get_synonims(self, word: str):
        synonyms = []
        syn_app = synonyms.append
        word = wn.synsets(word)
        for synset in word:
            for lemma in synset.lemmas():
                synonyms.append(lemma.name())

        return synonyms

    def get_hyponyms(self, word):
        hyponims = []
        he_app = hyponims.append
        word = wn.synsets(word)

        for hyponym in word[0].hyponyms():
            he_app(hyponym.name())

        return hyponims

    def get_hypernyms(self, word):
        hypernyms = []
        he_app = hypernyms.append
        word = wn.synsets(word)

        for hyponym in word[0].hypernyms():
            he_app(hyponym.name())

        return hypernyms
