from sys import exception
from turtle import st
from googletrans import Translator
import json

import html
from google.cloud import translate_v2 as translate

translate_client = translate.Client()

def transliterate_to_hebrew(name: str) -> str:
    try:
        result = translate_client.translate(name, target_language='he')
        clean_text = html.unescape(result["translatedText"])
        return clean_text
    except Exception as e:
        print(f"Translation error: {e}")
        return None

def transliterate_to_enlish(name: str) -> str:
    try:
        result = translate_client.translate(name, target_language='en')
        clean_text = html.unescape(result["translatedText"])
        return clean_text
    except Exception as e:
        print(f"Translation error: {e}")
        return None


def is_hebrew(text:str):
    return any('\u0590' <= char <= '\u05FF' for char in text)

translator = Translator()

"""
def transliterate_to_hebrew(name: str) -> str:
    try:

        result = translator.translate(name, src='en', dest='he')
        return result.text
    except Exception as e:
        print("basa")
        return None
"""

def main():

    """
    try:

        with open("english_names.json","r",encoding="utf-8") as f:
            players = json.load(f)

        for eng_name,val in players.items():
            if is_hebrew(val):
                continue
            players[eng_name] = transliterate_to_hebrew(eng_name)
        
    except Exception as e:
        print(f"script crashed: {e}")
    finally:
        with open("english_names.json","w",encoding="utf-8") as f:
            json.dump(players,f,ensure_ascii=False,indent=2)
    """
    with open("players_db_wo_pos.txt","r",encoding="utf-8") as f:
        names = {name.strip():"" for name in f}
    for name in names.keys():
        names[name] = transliterate_to_enlish(name)
    with open("heb_eng.json","w",encoding="utf-8") as f:
        json.dump(names,f,ensure_ascii=False,indent=2)




if __name__=="__main__":
    main()