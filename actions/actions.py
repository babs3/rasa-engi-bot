# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()  # Load environment variables from .env

# Set up Google Gemini API Key
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

class ActionCheckWeather(Action):

    def name(self) -> Text:
        return "action_check_weather"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        #dispatcher.utter_message(text="Today is a good day of sun!")

        try:
            g_model = genai.GenerativeModel("gemini-1.5-pro-latest")
            response = g_model.generate_content("How is the weather today?")

            if hasattr(response, "text") and response.text:
                print("\n🎯 Gemini Response Generated Successfully!")
                print(response.text)
                dispatcher.utter_message(text=response.text)
            else:
                print("\n⚠️ Gemini Response is empty.")
                dispatcher.utter_message(text="Sorry, I couldn't generate a response.")
        except Exception as e:
            dispatcher.utter_message(text="Sorry, I couldn't process that request.")
            print(f"\n❌ Error calling Gemini API: {e}")

        return []

