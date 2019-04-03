import json
import os
def load_json(filename, savepath='/'):
    """ check if it exists, if so, load it """
    if filename in os.listdir(savepath):
        return json.load(open(savepath+filename, 'r'))
    else:
        print("{} not in directory".format(filename))
        return {}
def save_json(dictionary, filename, savepath='/'):
    with open(savepath+filename,'w') as f:
        json.dump(dictionary, f, sort_keys=True, indent=4)
    return True
