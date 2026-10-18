import argparse,json
from risk_registry import prepare
from core import load_inputs,validate_corpus
from entry_status import prepare as prepare_status
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');a=p.parse_args()
 entries,sources,fields=load_inputs();entries,_=prepare(entries);entries,_=prepare_status(entries)
 print(json.dumps(validate_corpus(entries,sources,fields,release=not a.preview,built=True),indent=2))
