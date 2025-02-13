#!/usr/bin/env python3
"""api.py

Provides an API into the chatbot implementation
"""
import chatbot
import time
from transformers import DistilBertForSequenceClassification, DistilBertConfig, DistilBertTokenizerFast, pipeline
import spacy
from py2neo import Graph

sessions = {}

tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')
model = DistilBertForSequenceClassification.from_pretrained(
  'modeltobyfinal', config=DistilBertConfig(num_labels=24477)
)
nlp = spacy.load('en_core_web_sm')
ruler = nlp.add_pipe("entity_ruler")
ruler.add_patterns([
  {"label": "TIME", "pattern": [{"LOWER": {"REGEX": "((1[0-2]|0?[1-9]):([0-5][0-9]) ?([AaPp][Mm]))"}}]},
  {"label": "TIME", "pattern": [
      {"LOWER": {"REGEX": "(1[0-2]|0?[1-9])"}},
      {"IS_SPACE": True},
      {"LOWER": {"REGEX": "([AaPp][Mm])"}}
    ]
  }
])

cse_nlp = spacy.load('./custom_ner/output/model-best')
graph = Graph('bolt://localhost:7687', auth=('toby', 'toby'))
sentiment_analysis = pipeline('sentiment-analysis')

def start_session():
  """start_session
  FUTURE: Returns a token that indicates a chat session.

  You do not not need to implement this unless your chatbot supports keeping
  working memory of different chats. This
  """
  # You do not need to implement this for assignment 4
  t = str(time.time())
  sessions[t] = chatbot.Chatbot(tokenizer, model, nlp, cse_nlp, graph, sentiment_analysis)
  print('Created session: ' + t)
  return t


def end_session(token):
  """end_session
  FUTURE: Discards a token terminating a chat session.

  You do not not need to implement this unless your chatbot supports keeping
  working memory of different chats.
  """
  # You do not need to implement this for assignment 4
  try:
    sessions[token].endSession()
  except:
    print('?')
  pass

def respond(token, prompt):
  """respond
  Given a token and an utterance string, your chatbot should return with a 
  string response.
  
  If sessions are not supported, this method should ignore the token provided.
  If the prompt is an empty string, it indicates that the bot should initiate
  a conversation.

  :param token: A session token to associate the prompt to
  :param prompt: A string indicating text from a user
  :return: A string response from the chatbot
  """
  return sessions[token].delegate_by_intent(prompt)

if __name__ == '__main__':
  print('This file should not be run directly. ' + \
    'To try out your chatbot, please use debugserver.py.')
  exit(1)
