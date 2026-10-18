import argparse,json
from core import load_inputs,validate_corpus
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');a=p.parse_args()
 print(json.dumps(validate_corpus(*load_inputs(),release=not a.preview),indent=2))
