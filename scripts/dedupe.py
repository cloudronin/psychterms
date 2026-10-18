"""Exact normalized-content groups. Similarity never authorizes a merge."""
import collections,json
from core import load_inputs,normalize
if __name__=='__main__':
 groups=collections.defaultdict(list)
 for e in load_inputs()[0]:groups[normalize(e['definition'])].append(e['id'])
 print(json.dumps({'exact_duplicate_groups':[v for v in groups.values() if len(v)>1],'near_duplicate_policy':'manual contextual review; no automatic merges'},indent=2))
