"""Verify pinned packets independently of entry review status."""
import json,re
from core import ROOT,ALLOWED_LICENSES,digest,load_inputs

def validate_packet(packet,sources):
 source=sources.get(packet.get('source'))
 if not source or source['decision']!='yes' or source['licence'] not in ALLOWED_LICENSES:raise ValueError('Unpermitted packet source')
 if 'draft_basis' not in source['roles']:raise ValueError('No drafting role')
 if packet.get('licence')!=source['licence']:raise ValueError('Licence mismatch')
 if not packet.get('text') or not packet.get('revision') or not packet.get('source_record'):raise ValueError('Missing pinned packet content')
 if not re.fullmatch(r'[a-f0-9]{64}',packet.get('source_snapshot_sha256','')):raise ValueError('Missing source snapshot hash')
 if packet.get('packet_hash')!=digest({k:v for k,v in packet.items() if k!='packet_hash'}):raise ValueError('Packet hash mismatch')
 if packet.get('original_packet_hash'):
  original={k:v for k,v in packet.items() if k not in ('packet_hash','original_packet_hash')}
  original['id']=packet['source_record']
  if digest(original)!=packet['original_packet_hash']:raise ValueError('Original judged packet binding changed')
 if source.get('content_snapshot_sha256') and packet['source_snapshot_sha256']!=source['content_snapshot_sha256']:raise ValueError('Source snapshot mismatch')
 return True

if __name__=='__main__':
 entries,sources,_=load_inputs()
 for entry in entries:
  packet=json.loads((ROOT/'data/packets'/f'{entry["id"]}.json').read_text())
  validate_packet(packet,sources)
  if entry['packet_hash']!=packet['packet_hash']:raise ValueError('Stale entry packet')
 print(json.dumps({'packets_checked':len(entries),'pinned':True,'legacy_inputs':0},indent=2))
