import json
import logging
import os
import unicodedata
from typing import Any, Callable, TYPE_CHECKING

import Levenshtein
from metaphone import doublemetaphone
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler
import pandas as pd
import numpy as np
import re
from pathlib import Path


import warnings
import logging
warnings.filterwarnings("ignore", message="Accessing `__path__`")
logging.getLogger("transformers").setLevel(logging.ERROR)
from sentence_transformers import SentenceTransformer, util
import warnings
warnings.filterwarnings("ignore")



class Matcher: 

    '''Esta clase sirve para comparar una palabra transcrita con una lista de posibles candidatos reales. Dada la palabra transcrita y 
    la lista de candidatos, la función best_match(...) calcula una medida de similitud para todos los candidatos y devuelve el mejor. 
    Por ejemplo, si la palabra transcrita es "Bar terraza" y los candidatos son ["Cafetería manolo", "Casino Juan", "Bar Terrassa"], entonces 
    el matcher devolverá "Bar Terrassa" como mejor candidato porque es el que más se parece.'''

    def __init__(self, embeddings_path = "embeddings_cache.json"):

        self.ensemble_weights = np.array([1, 1, 1, 1, 1, 1, 1]) #Estos pesos se pueden ajustar para darle más importancia o menos a cada métrica. 
        self.ensemble_weights = self.ensemble_weights / self.ensemble_weights.sum() #Normalizamos los pesos para que sumen 1.
        self.score_cols = [
            "token_score", "embeddings_score", "metaphone_score", "levenstein_score",
            "token_sort_score", "partial_ratio_score", "jaro_winkler_score"
        ]
        
        self.emb = EmbeddingsManager()
    

    def quote_match(self, real_quote:str, guessed_quote:str): 

        scores =  {
            "common words": self.token_sort_score(real_quote, guessed_quote),
            "semantic": self.embeddings_score(real_quote, guessed_quote),
            "phonetic": self.metaphone_score(real_quote, guessed_quote),
            "levenstein": self.levenstein_score(real_quote, guessed_quote),
        }

        scores["total_score"] = sum(scores.values()) / len(scores)

        df_scores = pd.DataFrame([{
            "guessed_quote": guessed_quote,
            **scores
        }])

        return df_scores, scores["total_score"]



    def _normalize(self, text: str) -> str:
        '''Pone el texto en minúsculas, sin acentos, alfanumérico simple y sin espacios al principio o final'''
        lowered = text.lower()
        without_accents = "".join(ch for ch in unicodedata.normalize("NFD", lowered) if unicodedata.category(ch) != "Mn")
        return re.sub(r"[^a-z0-9]+", " ", without_accents).strip()



    '''Las funciones siguientes son de similitud. Todas reciben dos textos, el transcrito y uno oficial, 
    y devuelven un float en [0, 1] que indica cuánto se parecen ambos textos según esa métrica.'''


    def embeddings_score( self, transcripted_text: str, official_text: str) -> float:
        '''Mide la similitud semántica mediante embeddings. Cuando recalculate_transc_embedding es True, recalcula el embedding del texto "transcripted_text" y lo guarda en self.transc_emb. Altramente, reutiliza el 
        embedding calculado anteriormente. Es útil para no tener que estar recalculándolo todo el rato.'''

        self.transc_emb = self.emb.compute_embedding(transcripted_text, use_cache=False)
        official_emb = self.emb.compute_embedding(official_text, use_cache=True)
        similitud = util.cos_sim(self.transc_emb, official_emb).item()

        return similitud


    def metaphone_score(self, transcripted_text: str, official_text: str, ) -> float:
        '''Compara cómo suenan ambos textos transformándolos a códigos fonéticos raritos'''

        transc_metaphones = set( cosa for cosa in doublemetaphone(transcripted_text) if cosa )
        official_metaphones = set( cosa for cosa in doublemetaphone(official_text) if cosa )

        max_puntuacion = 0
        for text1 in transc_metaphones: 
            for text2 in official_metaphones: 
                puntuacion = Levenshtein.ratio(text1, text2)
                max_puntuacion = max(puntuacion, max_puntuacion)

        return max_puntuacion


    def levenstein_score(self, transcripted_text: str, official_text: str, ) -> float:
        '''Calcula la mínima cantidad de operaciones para pasar de un texto a otro 
        (las operaciones posibles son sustituir, añadir o eliminar una letra)'''
        return Levenshtein.ratio(transcripted_text, official_text)


    def token_sort_score(self, transcripted_text: str, official_text: str, ) -> float:
        '''Cuenta la proporción de palabras del texto oficial que están en el texto transcrito'''
        palabras_inicial = set(transcripted_text.lower().split())
        palabras_final = set(official_text.lower().split())
        
        en_comun = palabras_final & palabras_inicial
        return len(en_comun) / len(palabras_final)
        

    def partial_ratio_score(self, transcripted_text: str, official_text: str, ) -> float:
        '''Intenta ver la mayor secuencia de letras en común entre ambos textos'''
        return fuzz.partial_ratio(transcripted_text, official_text)/100
    

    def jaro_winkler_score(self, transcripted_text: str, official_text: str, ) -> float:
        '''Parecido a Levenstein, pero puntúa mejor cuando empiezan igual'''
        return JaroWinkler.similarity(transcripted_text, official_text)





class EmbeddingsManager: 

    def __init__(self): 
        self.embeddings_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')


    def compute_embedding(self, word:str, use_cache: bool=True): 
        '''Calcula el embedding de una palabra. Cuando use_cache es True, busca si ya lo había calculado antes en la cache para evitar recalcularlo, y si no lo está, lo calcula y también lo guarda en la cache. 
        Si use_cache es False, lo calcula directamente sin interactuar con la cache.'''

        return self.embeddings_model.encode(word, convert_to_tensor=True).tolist()








