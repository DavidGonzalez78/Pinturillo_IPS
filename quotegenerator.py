import json
from pathlib import Path
from typing import Any, Callable, TYPE_CHECKING
from urllib.parse import urlsplit
from openai import AzureOpenAI
import streamlit as st


class QuoteGenerator:

    def __init__(self):

            #self.config = json.loads(self.config_path.read_text(encoding="utf-8"))

            foundry_cfg = st.secrets["azure_foundry"]
            if not isinstance(foundry_cfg, dict):
                foundry_cfg = {}

            self.foundry_endpoint = self._normalize_foundry_endpoint(str(st.secrets["azure_foundry"]["endpoint"]).strip())
            self.foundry_api_key = str(st.secrets["azure_foundry"]["api_key"]).strip()
            self.foundry_model = str(st.secrets["azure_foundry"]["model"]).strip()
            if "api_version" in foundry_cfg:
                self.foundry_api_version = foundry_cfg["api_version"]
            else:
                self.foundry_api_version = "2024-10-21"

            self.client = AzureOpenAI(api_key=self.foundry_api_key, api_version=self.foundry_api_version, azure_endpoint=self.foundry_endpoint)

            with open("previous_quotes.txt", "r", encoding="utf-8") as f:
                self.previous_quotes = [line.strip() for line in f.readlines() if line.strip()]


            print(f"EntityExtractor inicializado con Foundry, endpoint: {self.foundry_endpoint}, model: {self.foundry_model}")



    def generate_quote(self): 
        # Crear cliente de Foundry
        

        #Las prompts que va a recibir el modelo
        system_prompt = (
            "Te encargas de generar escenas cortas (de entre 4 a 10 palabras) para un juego donde un jugador tendrá que dibujar la escena y el otro adivinarla. " \
            "Tienen que ser escenas visuales, dibujables, pero un poco complejas. Algunas ideas de cosas que pueden incluir: " \
            " - Emociones, frutas y verduras animadas, animales divertidos, elementos de una oficina, cosas relacionadas con programación y data science. " \
            " - Sería especialmente divertido si nos mencionaras a nosotros, que nos llamamos Alba, David, Arnau, Jan, Manuel, Josep, Francesc, Mayra, Sam, Naranja diabolica, y a nuestra empresa de máquinas recreativas llamada IPS "
            " - Cosas o sitios que puedes encontrar en Barcelona o España. Cosas de nuestra oficina, como cafe, churros, tazas, tuppers, cascos, etc." \
            " - No tiene que ser siempre así, se te pueden ocurrir más cosas random, las que quieras, desde piratas, astronautas o bandidos, playeros, o mucho más, mientras más diversidad mejor. " \
            " - No digas todo el rato un mismo concepto, escoge aleatoriamente (por ejemplo no hagas todas las frases con la naranja diabólica). " \
            f"No seas muy repetitivo, evita ideas parecidas a las de escenas anteriores, algunas de las últimas escenas que generaste fueron estas: {self.previous_quotes[-20:]}"
        )
        user_prompt = """Genera una escena para dibujar. Solamente una. """

        # Conectarse con el modelo, enviarle las prompts y obtener la respuesta
        response = self.client.chat.completions.create(
            model=self.foundry_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.9,
        )

        # `response.choices[0].message.content` es un string con el resultado del LLM. Ahora lo transforman a un diccionario en el formato parseado correcto y lo devuelven
        content = (response.choices[0].message.content or "").strip()

        # Guardar en el archivo "previous_quotes.txt"
        with open("previous_quotes.txt", "a", encoding="utf-8") as f:
            f.write("\n" + content )
        self.previous_quotes.append(content)

        return content
    


    @staticmethod
    def _normalize_foundry_endpoint(endpoint: str) -> str:
        '''Sirve para arreglar la ruta URL del endpoint. Poco más'''

        raw = endpoint.strip()
        if not raw:
            return ""

        parsed = urlsplit(raw)
        if parsed.scheme and parsed.netloc:
            base = f"{parsed.scheme}://{parsed.netloc}"
        else:
            base = raw

        lowered = raw.lower()
        openai_idx = lowered.find("/openai/")
        if openai_idx >= 0:
            return raw[:openai_idx].rstrip("/")
        return base.rstrip("/")
    



