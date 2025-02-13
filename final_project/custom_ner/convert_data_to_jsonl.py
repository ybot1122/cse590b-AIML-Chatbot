import numpy as np
from all_intents_cse import DATA

NUM_SAMPLES = 50

sample = np.random.randint(1, len(DATA), NUM_SAMPLES)

print(sample)

with open('./spacey20.jsonl', 'w+') as f:
  for i in sample:
    f.write("{\"text\": \"" + DATA[i][0] + "\", \"label\": [[]]}\n")
