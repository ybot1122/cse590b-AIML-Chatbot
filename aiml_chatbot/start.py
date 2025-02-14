import aiml
import os

path = os.path.dirname(os.path.realpath(__file__))

k = aiml.Kernel()

k.learn(path + "/files/udc.aiml")

while True:
    user_prompt = input("> ")
    response = k.respond(user_prompt)
    print(response)
