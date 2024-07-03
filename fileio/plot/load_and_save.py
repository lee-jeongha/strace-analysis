import os
import json

def save_csv(df, filename, index=0):
    try:
        if index==0:
            df.to_csv(filename, index=True, header=True, mode='w') # encoding='utf-8-sig'
        else: #append mode
            df.to_csv(filename, index=True, header=False, mode='a') # encoding='utf-8-sig'

    except FileNotFoundError:    # FileNotFoundError: [Errno2] No such file or directory: '~'
        path = filename[:filename.rfind('/')]

        if not os.path.exists(path):
            os.makedirs(path)

        if index==0:
            df.to_csv(filename, index=True, header=True, mode='w') # encoding='utf-8-sig'
        else: #append mode
            df.to_csv(filename, index=True, header=False, mode='a') # encoding='utf-8-sig'

def save_json(savings, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # indent=2 is not needed but makes the file human-readable
            json.dump(savings, f, indent=2)

    except FileNotFoundError:    # FileNotFoundError: [Errno2] No such file or directory: '~'
        path = filename[:filename.rfind('/')]

        if not os.path.exists(path):
            os.makedirs(path)

        with open(filename, 'w', encoding='utf-8') as f:
            # indent=2 is not needed but makes the file human-readable
            json.dump(savings, f, indent=2)

def load_json(saving_list, filename):
    with open(filename, 'r') as f:
        load = json.load(f)

    savings = []

    for i in saving_list:
        savings.append(load[i])

    return tuple(savings)