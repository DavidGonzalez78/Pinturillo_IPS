from quotegenerator import QuoteGenerator
from matcher import Matcher
import pandas as pd
import os
import json
import pickle
from datetime import datetime
from pathlib import Path


class Partida: 

    def __init__(self, quote_generator): 

        self.player1 = None
        self.player2 = None
        self.blocked = False
        self.quote_generator = quote_generator
        self.matcher = Matcher()

        self.phase = "Choose quote" # "Choose quote", "Make drawing", "Make guess", "Finished"

        self.quote = None
        self.guessed_quotes = pd.DataFrame(
            columns=[
                "guessed_quote",
                "total_score",
                "common words",
                "semantic",
                "phonetic",
                "levenstein",
            ]
        )
        self.drawing = None

        self.generate_random_quote()
    


    def generate_random_quote(self): 
        '''Genera una quote aleatoria llamando al modelo de chatgtp'''

        self.quote = self.quote_generator.generate_quote()
        self.phase = "Make drawing"



    def play_drawing(self, player1, drawing): 
        '''Estando en next_phase "Make drawing", recibe una imágen y el jugador que la ha hecho (player1). Se la guarda y se prepara para la fase de adivinar'''

        if self.phase == "Make drawing": 
            self.player1 = player1
            self.drawing = drawing
            self.phase = "Make guess"
    


    def get_drawing(self): 
        '''Devuelve el dibujo que hizo el jugador en "Make drawing", así como el propio jugador'''

        if self.phase == "Make guess": 
            return self.drawing, self.player1



    def guess_drawing(self, player2, guessed_quote): 
        '''Estando en la frase "Make guess", recibe de player2 una propuesta de quote. La compara con la quote real'''

        if (self.phase == "Make guess") and (self.player1 != player2): 

            scores, total_score = self.matcher.quote_match(self.quote, guessed_quote)
            won = (total_score > 0.9)
            if won: 
                self.player2 = player2
                self.phase = "Finished"
            
            self.guessed_quotes = pd.concat(
                [scores, self.guessed_quotes],
                ignore_index=True
            )
            return won, scores
        
    

    def get_info(self): 
        print(  f"En esta partida dibuja {self.player1} y adivina {self.player2}. blocked = {self.blocked}"  )
    
    def block(self): 
        self.blocked = True
    
    def unblock(self): 
        self.blocked = False
    

    def save(self, save_dir: str = "partidas_guardadas", index:int=0) -> str:
        """
        Guarda la partida en una carpeta con timestamp.
        Devuelve la ruta donde se ha guardado.
        """
        # Crear carpeta con timestamp único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        partida_dir = Path(save_dir) / f"partida_{self.player1}_vs_{self.player2}_{timestamp}_{index}"
        partida_dir.mkdir(parents=True, exist_ok=True)

        # --- 1. Metadata en JSON (jugadores, fase, quote, etc.) ---
        metadata = {
            "saved_at": timestamp,
            "player1": self.player1,
            "player2": self.player2,
            "blocked": self.blocked,
            "phase": self.phase,
            "quote": self.quote,
        }
        with open(partida_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # --- 2. Historial de intentos en CSV ---
        if not self.guessed_quotes.empty:
            self.guessed_quotes.to_csv(partida_dir / "intentos.csv", index=False)

        # --- 3. Dibujo ---
        if self.drawing is not None:
            # Si es PIL Image
            if hasattr(self.drawing, 'save'):
                self.drawing.save(partida_dir / "drawing.png")
            
            # Si es CanvasResult (streamlit-drawable-canvas)
            elif hasattr(self.drawing, 'image_data') and self.drawing.image_data is not None:
                from PIL import Image
                img = Image.fromarray(self.drawing.image_data.astype('uint8'), 'RGBA')
                img.save(partida_dir / "drawing.png")
            
            # Si es numpy array directamente
            elif hasattr(self.drawing, 'shape'):
                from PIL import Image
                img = Image.fromarray(self.drawing.astype('uint8'), 'RGBA')
                img.save(partida_dir / "drawing.png")
            
            # Si es bytes
            elif isinstance(self.drawing, bytes):
                with open(partida_dir / "drawing.bin", "wb") as f:
                    f.write(self.drawing)

        return str(partida_dir)
