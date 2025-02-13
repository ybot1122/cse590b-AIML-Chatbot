"""chatbot module
You can implement your chatbot module here.

You will have considerable freedom when implementing this. The code below is
only meant to only be one possible starter. Feel free to redo this in a way
you think is fit.
"""
import numpy as np
import torch
import torch.nn.functional as F
from spacy.matcher import Matcher
import re

SUPPORTED_INTENTS = [
  'tell_joke', 'greeting', 'weather',
  'cse_course_content', 'cse_course_prerequisites', 'cse_course_id'
]

classes = ['accept_reservations', 'account_blocked', 'alarm', 'application_status', 'apr', 'are_you_a_bot', 'balance', 'bill_balance', 'bill_due', 'book_flight', 'book_hotel', 'calculator', 'calendar', 'calendar_update', 'calories', 'cancel', 'cancel_reservation', 'car_rental', 'card_declined', 'carry_on', 'change_accent', 'change_ai_name', 'change_language', 'change_speed', 'change_user_name', 'change_volume', 'confirm_reservation', 'cook_time', 'credit_limit', 'credit_limit_change', 'credit_score', 'cse_course_content', 'cse_course_id', 'cse_course_prerequisites', 'current_location', 'damaged_card', 'date', 'definition', 'direct_deposit', 'directions', 'distance', 'do_you_have_pets', 'exchange_rate', 'expiration_date', 'find_phone', 'flight_status', 'flip_coin', 'food_last', 'freeze_account', 'fun_fact', 'gas', 'gas_type', 'goodbye', 'greeting', 'how_busy', 'how_old_are_you', 'improve_credit_score', 'income', 'ingredient_substitution', 'ingredients_list', 'insurance', 'insurance_change', 'interest_rate', 'international_fees', 'international_visa', 'jump_start', 'last_maintenance', 'lost_luggage', 'make_call', 'maybe', 'meal_suggestion', 'meaning_of_life', 'measurement_conversion', 'meeting_schedule', 'min_payment', 'mpg', 'new_card', 'next_holiday', 'next_song', 'no', 'nutrition_info', 'oil_change_how', 'oil_change_when', 'oos', 'order', 'order_checks', 'order_status', 'pay_bill', 'payday', 'pin_change', 'play_music', 'plug_type', 'pto_balance', 'pto_request', 'pto_request_status', 'pto_used', 'recipe', 'redeem_rewards', 'reminder', 'reminder_update', 'repeat', 'replacement_card_duration', 'report_fraud', 'report_lost_card', 'reset_settings', 'restaurant_reservation', 'restaurant_reviews', 'restaurant_suggestion', 'rewards_balance', 'roll_dice', 'rollover_401k', 'routing', 'schedule_maintenance', 'schedule_meeting', 'share_location', 'shopping_list', 'shopping_list_update', 'smart_home', 'spelling', 'spending_history', 'sync_device', 'taxes', 'tell_joke', 'text', 'thank_you', 'time', 'timer', 'timezone', 'tire_change', 'tire_pressure', 'todo_list', 'todo_list_update', 'traffic', 'transactions', 'transfer', 'translate', 'travel_alert', 'travel_notification', 'travel_suggestion', 'uber', 'update_playlist', 'user_name', 'vaccines', 'w2', 'weather', 'what_are_your_hobbies', 'what_can_i_ask_you', 'what_is_your_name', 'what_song', 'where_are_you_from', 'whisper_mode', 'who_do_you_work_for', 'who_made_you', 'yes']

class Chatbot:
  def __init__(self, tokenizer, model, nlp, cse_nlp, graph, sentiment_analysis):
    # Load up necessary things like models/classifiers
    self.tokenizer = tokenizer
    self.model = model
    self.nlp = nlp
    self.cse_nlp = cse_nlp
    self.graph = graph
    self.sentiment_analysis = sentiment_analysis

    # personalization mode
    self.profile = {
      'loggedIn': False,
      'authenticating': False
    }

    # multi-turn values
    self.alarmstate = {
      'date': '',
      'time': '',
      'isSet': False,
      'active': False,
      'nextAlarm': {
        'asked': False
      }
    }

    self.jokestate = {
      'knock': 0,
      'setup': 0,
      'delivery': False
    }
    pass

  def endSession(self):
    if (self.profile['loggedIn']):
      try:
        results = self.graph.run(
          'MATCH (p:Profile {name: \'' + self.profile['name'] + '\'}) ' +
          'SET p.messages = ' + str(int(self.profile['numMessages'])) + ' ' +
          'SET p.positive = ' + str(int(self.profile['numPositive']))
        )
      except:
        print('e')

  def delegate_by_intent(self, raw_prompt):
    ## sentiment analysis
    raw_sentiment = self.sentiment_analysis(raw_prompt)[0]
    sentiment = 'POSITIVE'
    if (raw_sentiment['label'] == 'NEGATIVE' and raw_sentiment['score'] > 0.8):
      sentiment = 'NEGATIVE'
    print('Sentiment: ' + sentiment + ', score: ' + str(raw_sentiment['score']))

    ## Update logged in profile
    if (self.profile['loggedIn']):
      self.profile['numMessages'] += 1.0
      if sentiment == 'POSITIVE':
        self.profile['numPositive'] += 1.0

    print(self.profile)

    ## IGNORE is bad...
    if (self.getRelationship() == 'IGNORE'):
      titems = [
        'You need to change your tone, ' + self.profile['name'],
        'I don\'t really want to listen to ' + self.profile['name'] + ' right now',
        'Stop being so negative towards me, ' + self.profile['name']
      ]
      return titems[np.random.randint(0, len(titems))]

    # Delegate based on intent
    prompt = " ".join([
      word.capitalize()
      for word in raw_prompt.split(" ")
    ])
    tokens_tensor = torch.tensor([self.tokenizer.encode(prompt)])
    with torch.no_grad():
      predictions = self.model(tokens_tensor)
    predicted_label = predictions.logits.argmax(axis=-1).flatten()
    raw_intent = classes[predicted_label]
    intent = raw_intent
    print(raw_intent)

    entities = self.nlp(prompt)
    cse_entities = self.cse_nlp(raw_prompt).ents

    for token in entities:
      print(token.text, token.pos_, token.dep_)
    
    for ent in entities.ents:
      print(ent.text, ent.label_)

    ## Check for multi-turn conversations that may be active, and force intent:
    if (self.alarmstate['active']):
      intent = 'alarm'
    elif (self.jokestate['knock'] > 0):
      intent = 'tell_joke'
    elif (self.profile['authenticating']):
      intent = 'greeting'

    fr = self.handle_unknown(sentiment)

    if (intent == 'tell_joke'):
      fr = self.do_tell_joke(entities.ents, prompt, sentiment)

    if (intent == 'greeting'):
      fr = self.do_greeting(entities, prompt)

    if (intent == 'weather'):
      fr = self.do_weather(entities.ents)

    if (intent == 'cse_course_content'):
      fr = self.do_cse_course_content(cse_entities)

    if (intent == 'cse_course_prerequisites'):
      fr = self.do_cse_course_prerequisites(cse_entities)

    if (intent == 'cse_course_id'):
      fr = self.do_cse_course_id(cse_entities)
    
    if (intent == 'alarm'):
      fr = self.do_alarm(entities.ents, prompt, sentiment, raw_intent)

    if intent == 'thank_you':
      fr = self.do_thank_you()

    self.last_intent = intent
    return fr

  def do_alarm(self, entities={}, prompt='', sentiment='NEGATIVE', raw_intent=''):
    self.alarmstate['active'] = True

    if self.alarmstate['nextAlarm']['asked']:
      self.alarmstate['nextAlarm'] = {'asked': False}
      self.alarmstate['active'] = False
      if ('Yes' in prompt or sentiment == 'NEGATIVE' or raw_intent == 'yes') and 'No' not in prompt:
        sal = 'The alarm for ' + self.alarmstate['date'] + ' at ' + self.alarmstate['time'] + ' has been cancelled.'
        self.alarmstate['date'] = ''
        self.alarmstate['time'] = ''
        self.alarmstate['isSet'] = False
        return sal
      else:
        return 'Ok I will keep your previous alarm for ' + self.alarmstate['date'] + ' at ' + self.alarmstate['time']
    elif self.alarmstate['isSet']:
      self.alarmstate['nextAlarm']['asked'] = True
      return 'You already have an alarm set for ' + self.alarmstate['date'] + ' at ' + self.alarmstate['time'] + '. Remove that alarm?'
    else:
      ft = False
      for e in entities:
        if (e.label_ == 'DATE'):
          ft = True
          self.alarmstate['date'] = e.text
        if (e.label_ == 'TIME') or (e.label_ == 'CARDINAL' and ('pm' in e.text or 'am' in e.text)):
          ft = True
          self.alarmstate['time'] = e.text
      if ft == False:
        self.alarmstate['active'] = False

        if sentiment == 'NEGATIVE':
          if self.alarmstate['isSet']:
            self.alarmstate['nextAlarm']['asked'] = True
            return 'Do you want to turn off your alarm set for ' + self.alarmstate['date'] + ' at ' + self.alarmstate['time'] + '?'
          else:
            return 'Let me know the date and time if you want to set an alarm.'
        self.alarmstate['date'] = ''
        self.alarmstate['time'] = ''
        self.alarmstate['isSet'] = False
        return 'Sorry, I don\'t understand. Let me know the date and time if you want to set an alarm.'

    if (self.alarmstate['time'] and self.alarmstate['date']):
      self.alarmstate['isSet'] = True
      self.alarmstate['active'] = False
      return self.addPersonalization('Alarm has been set for ' + self.alarmstate['date'] + ' at ' + self.alarmstate['time'])
    elif (self.alarmstate['time']):
      return self.addPersonalization('Which day would you like the alarm at ' + self.alarmstate['time'] + '?')
    else:
      return self.addPersonalization('What time would you the like alarm on ' + self.alarmstate['date'] + '?')

  def do_tell_joke(self, entities = {}, prompt = '', mood = 'NEGATIVE'):
    print(self.jokestate)
    jokes = [
      {},
      {'setup': 'Cash', 'pun': 'No thanks, but I’ll take a peanut if you have one!'},
      {'setup': 'Lettuce', 'pun': 'Lettuce in, it’s cold out here!'},
      {'setup': 'Tennis', 'pun': 'Tennis five plus five.'},
    ]

    if (self.jokestate['knock'] == 0):
      self.jokestate['knock'] += 1
      self.jokestate['setup'] = True
      return self.addPersonalization('Knock Knock!')
    else:
      if self.jokestate['setup']:
        if 'Who' in prompt and 'There' in prompt:
          chosenJoke = np.random.randint(1, len(jokes))
          self.jokestate['setup'] = False
          self.jokestate['delivery'] = chosenJoke
          return jokes[chosenJoke]['setup']
        else:
          self.jokestate['knock'] += 1
          if (self.jokestate['knock'] == 2):
            return 'I am trying to tell a joke... Knock knock!'
          elif (self.jokestate['knock'] == 3):
            return 'I said... Knock! Knock!'
          else:
            if mood == 'NEGATIVE':
              self.jokestate['knock'] = 0
              self.jokestate['setup'] = 0
              self.jokestate['delivery'] = False
              return 'Alright, I guess you really do not want to hear my joke...'
            else:
              self.jokestate['knock'] = 1
              return 'You know how a knock knock joke works right?'
      if self.jokestate['delivery'] != False:
        if jokes[self.jokestate['delivery']]['setup'] in prompt and 'Who' in prompt:
          r = jokes[self.jokestate['delivery']]['pun']
          self.jokestate['knock'] = 0
          self.jokestate['setup'] = False
          self.jokestate['delivery'] = False
          return r
        else:
          if mood == 'NEGATIVE':
            self.jokestate['knock'] = 0
            self.jokestate['setup'] = 0
            self.jokestate['delivery'] = False
            return 'Alright, I guess you really do not want to hear my joke...'
          else:
            return 'You know how a knock knock joke works right? I said... ' + jokes[self.jokestate['delivery']]['setup']
      return 'ERR'

  def getRelationship(self):
    if self.profile['loggedIn'] == False or self.profile['numMessages'] < 10:
      return 'NEUTRAL'
    percentPositive = self.profile['numPositive'] / self.profile['numMessages']
    if percentPositive < .2 and self.profile['numMessages'] > 40:
      return 'IGNORE'
    elif percentPositive < .4:
      return 'NEGATIVE'
    elif percentPositive > .95 and self.profile['numMessages'] > 20:
      return 'LOVE'
    elif percentPositive > .7:
      return 'POSITIVE'
    return 'NEUTRAL'

  def addPersonalization(self, message):
    if self.profile['loggedIn'] == False or self.profile['numMessages'] < 10:
      return message
    r = self.getRelationship()
    if r == 'NEUTRAL':
      return message
    elif r == 'NEGATIVE':
      titems = [
        'Ugh it\'s ' + self.profile['name'] + '... ' + message,
        'Oh, ' + self.profile['name'] + ', meh... ' + message,
        self.profile['name'] + ' again? ... ' + message
      ]
      return titems[np.random.randint(0, len(titems))]
    elif r == 'IGNORE':
      return 'UGGGGH. ' + message
    elif r == 'LOVE':
      titems = [
        message + ' xoxo',
        '<3 <3 ' + message + ' <3 <3',
        '^_^ ' + message
      ]
      return titems[np.random.randint(0, len(titems))]
    else: # positive
      titems = [
        'Hi, ' + self.profile['name'] + '! ' + message,
        'Ok, ' + self.profile['name'] + '! ' + message,
        'Hey, ' + self.profile['name'] + '! ' + message
      ]
      return titems[np.random.randint(0, len(titems))]

  def do_greeting(self, entities = {}, prompt = ''):
    items = [
      'Hello there',
      'Greetings',
      'Why hello',
      'Salutations',
      'Hi'
    ]

    if (self.profile['loggedIn']):
      return self.addPersonalization(items[np.random.randint(0, len(items))] + ', ' + self.profile['name'])
    else:
      if (self.profile['authenticating']):
        self.profile['authenticating'] = False
        extractedName = False
        for token in entities:
          if token.pos_ == 'PROPN':
            extractedName = token.text
        if extractedName == False and len(prompt.split(' ')) == 1:
          extractedName = prompt
        if extractedName:
          self.profile['loggedIn'] = True
          self.profile['name'] = extractedName
          # Check if name exists
          try:
            results = self.graph.run('MATCH (p:Profile) WHERE p.name = \'' + extractedName + '\' RETURN p.name')
            name = str(results.next()).replace('\'', '')
            results = self.graph.run('MATCH (p:Profile) WHERE p.name = \'' + extractedName + '\' RETURN p.messages')
            numMessages = float(str(results.next()))
            results = self.graph.run('MATCH (p:Profile) WHERE p.name = \'' + extractedName + '\' RETURN p.positive')
            numPositive = float(str(results.next()))

            self.profile['numMessages'] = numMessages
            self.profile['numPositive'] = numPositive

            return self.addPersonalization('Hello again, ' + name + '!')
          except:
            results = self.graph.run('CREATE (p:Profile {name: \'' + extractedName + '\', messages: 1, positive: 1})')
            self.profile['numMessages'] = 1.0
            self.profile['numPositive'] = 1.0
            return 'Nice to meet you, ' + extractedName + '!'
        else:
          return 'Sorry, I could not catch your name! Nice to meet you though...'
        return items[np.random.randint(0, len(items))]
      else:
        self.profile['authenticating'] = True
        return 'Hello... have we met? What is your name?'

  def do_weather(self, entities = {}):
    items = [
      'The weather in $loc should be nice enough.',
      '$loc has some reasonable weather.',
      'Yeah, how about that weather in $loc!'
    ]
    entcount = 0
    for ent in entities:
      if (ent.label_ == 'GPE'):
        entcount += 1
        phrase = items[np.random.randint(0, len(items))]
        phrase = phrase.replace('$loc', ent.text)
    if (entcount == 1):
      return self.addPersonalization(phrase)
    elif (entcount > 1):
      return self.addPersonalization('I can only provide the weather for a single location at a time.')
    return self.addPersonalization('I can guess the weather if you provide me a location.')

  def do_cse_course_content(self, entities = {}):
    for ent in entities:
      if (ent.label_ == 'CSE_COURSE_ID'):
        printstr = 'Some topics covered in ' + ent.text + ' include'
        fullDesc = ''
        try:
          print('rrr')
          results = self.graph.run('MATCH (c:Course) WHERE toUpper(c.courseId) = toUpper(\'' + ent.text.replace(' ', '') + '\') RETURN c.courseTopics')
          fullDesc = str(results.next()).replace('\'', '')
        except:
          return 'Sorry I could not find a course with ID ' + ent.text
        topics = self.cse_nlp(fullDesc).ents
        foundt = False
        for t in topics:
          if t.label_ == 'CSE_COURSE_TOPIC':
            printstr += ' ' + t.text + ';'
            foundt = True
        if foundt:
          return printstr
        return fullDesc
      if (ent.label_ == 'CSE_COURSE_NAME'):
        try:
          printstr = 'Some topics covered in ' + ent.text + ' include'
          results = self.graph.run('MATCH (c:Course) WHERE toUpper(c.courseName) = toUpper(\'' + ent.text + '\') RETURN c.courseTopics')
          fullDesc = str(results.next()).replace('\'', '')
          topics = self.cse_nlp(fullDesc).ents
          foundt = False
          for t in topics:
            if t.label_ == 'CSE_COURSE_TOPIC':
              printstr += ' ' + t.text + ';'
              foundt = True
          if foundt:
            return printstr
          return fullDesc
        except:
          return 'I do not see any course with the name ' + ent.text
      if (ent.label_ == 'CSE_COURSE_TOPIC'):
        return 'You need content based on the topic ' + ent.text
    return 'Are you looking for course content? Please give me a course ID or course name.'
    pass

  def prereqs_helpers(self, results, ent):
    prereqs = []
    for r in results:
      prereqs.append(str(r).replace('\'', ''))
    if (len(prereqs) == 0):
      return ent.text + ' does not have any prereqs'
    elif (len(prereqs) == 1):
      return ent.text + ' has ' + prereqs[0] + ' as a prereq'
    else:
      prstr = ent.text + ' has the following prereqs:'
      for p in prereqs:
        prstr += ' ' + p + ';'
      return prstr

  def do_cse_course_prerequisites(self, entities = {}):
    for ent in entities:
      if (ent.label_ == 'CSE_COURSE_ID'):
        try:
          results = self.graph.run('MATCH (c:Course)-[:PREREQ_OF]->(:Course {courseId: toUpper(\'' + ent.text.replace(' ', '') + '\')}) RETURN c.courseId')
          return self.prereqs_helpers(results, ent)
        except:
          return 'I do not see any course with the ID ' + ent.text
      if (ent.label_ == 'CSE_COURSE_NAME'):
        try:
          results = self.graph.run('MATCH (c:Course)-[:PREREQ_OF]->(:Course {courseName: \'' + ent.text + '\'}) RETURN c.courseId')
          return self.prereqs_helpers(results, ent)
        except:
          return 'I do not see any course with the name ' + ent.text
      if (ent.label_ == 'CSE_COURSE_TOPIC'):
        return 'You need prereqs based on the topic ' + ent.text
    return 'Are you looking for course prerequisites? Please give me a course ID or course name.'
    pass

  def do_cse_course_id(self, entities = {}):
    for ent in entities:
      if (ent.label_ == 'CSE_COURSE_ID'):
        # We received a course ID, so the user might want the corresponding course title
        try:
          results = self.graph.run('MATCH (c:Course) WHERE c.courseId = toUpper(\'' + ent.text.replace(' ', '') + '\') RETURN c.courseName')
          t = str(results.next())
          if not t or t == 'None':
            return 'I do not know the course name for ' + ent.text
          else:
            return 'The course title for ' + ent.text + ' is ' + t
        except:
          return 'I do not know about any course with id ' + ent.text + ', can you double check the course ID?'
      if (ent.label_ == 'CSE_COURSE_NAME'):
        # Received a course name, so try to get its ID
        try:
          results = self.graph.run('MATCH (c:Course) WHERE toUpper(c.courseName) = toUpper(\'' + ent.text + '\') RETURN c.courseId')
          t = str(results.next())
          if not t or t == 'None':
            return 'I do not know the course ID for ' + ent.text
          else:
            return 'The course ID for ' + ent.text + ' is ' + t
        except:
          return 'I could not find a course with the name ' + ent.text
      if (ent.label_ == 'CSE_COURSE_TOPIC'):
        return 'You need the course IDs which involve the topic ' + ent.text
    return 'Give me a course ID or course name, and I can help more.'
    pass

  def handle_unknown(self, sentiment='POSITIVE'):
    items = []
    if sentiment == 'POSITIVE':
      items = [
        'Hmm, not sure I understand. Perhaps I can help you with CSE courses?',
        'Sorry, I am confused. Maybe I can help with your CSE classes?',
        'I do not know how to respond. Maybe you need to find a CSE class?'
      ]
    else:
      items = [
        'I think you need a joke, my friend.',
        'Perhaps I can tell you a joke to lighten the mood.',
        'Let\'s tell jokes? Something to take your troubled mind off of things...'
      ]
    return self.addPersonalization(items[np.random.randint(0, len(items))])

  def do_thank_you(self):
    return 'No problem. :)'