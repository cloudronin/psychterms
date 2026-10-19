"""Run one registered hybrid wave, report it, then refresh its build-owned queue."""
import argparse,json,subprocess,sys
from pathlib import Path
from core import ROOT
from hybrid_redraft import DEST,atomic,registration

def main(wave):
    registration(DEST)
    atomic(DEST/'run-state.json',{'stage':'running','wave':wave,'paid_role':'draft','next_wave_automatic':False})
    commands=[['hybrid_redraft.py','run','--wave',str(wave)],['hybrid_redraft.py','report','--wave',str(wave)],['finalize_local_redraft_wave.py','--hybrid','--wave',str(wave)]]
    for command in commands:
        result=subprocess.run([sys.executable,str(ROOT/'scripts'/command[0]),*command[1:]],cwd=ROOT)
        if result.returncode:
            atomic(DEST/'run-state.json',{'stage':'paused','wave':wave,'failed_step':command[0],'exit_code':result.returncode,'next_wave_automatic':False})
            return result.returncode
    return 0
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--wave',type=int,default=1);a=p.parse_args();sys.exit(main(a.wave))
