import json

FILE_PATH = "./states.json"
def getStates():
    with open(FILE_PATH) as f:
        return json.load(f)
def setStates(states):
    with open(FILE_PATH, 'w') as f:
        json.dump(states, f)

def getFlagEnd():
    states = getStates()
    return states['flag_end']

def setFlagEnd(value):
    states = getStates()
    states['flag_end'] = value
    setStates(states)

