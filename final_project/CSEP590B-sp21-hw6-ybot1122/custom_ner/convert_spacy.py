# https://towardsdatascience.com/using-spacy-3-0-to-build-a-custom-ner-model-c9256bea098#_=_

from tqdm import tqdm
import spacy
from spacy.tokens import DocBin
import json

nlp = spacy.blank("en")
nlp.add_pipe("ner")

db_train = DocBin() # create a DocBin object
db_dev = DocBin()

TRAIN_DATA = []

myfile = open('./admin.jsonl', 'r')
myline = myfile.readline()
while myline:
  d = json.loads(myline)
  TRAIN_DATA.append((d['data'], {'entities': d['label']}))
  myline = myfile.readline()
myfile.close()

done = 0
for text, annot in tqdm(TRAIN_DATA): # data in previous format
  doc = nlp.make_doc(text) # create doc object from text
  ents = []
  for start, end, label in annot["entities"]: # add character indexes
    span = doc.char_span(start, end, label=label, alignment_mode="contract")
    if span is None:
      print("Skipping entity")
    else:
      print(span)
      ents.append(span)
  doc.ents = ents # label the text with the ents

  # use 80% for training, 20% for validation
  if (done < len(TRAIN_DATA) * .8):
    db_train.add(doc)
  else:
    db_dev.add(doc)
  done += 1

db_train.to_disk("./train.spacy") # save the docbin object
db_dev.to_disk("./dev.spacy") # save the docbin object
