"""Finish build-owned reporting after a local wave; never performs model inference."""
import argparse,fcntl,json,subprocess,sys,time
from pathlib import Path
from core import ROOT,digest
from local_redraft import DEST,atomic,registration

def finish(wave,dest=DEST,wait=False):
    m,_=registration(dest);folder=dest/f'wave-{wave:03d}';marker=folder/'reported.json';idle_since=None
    while not marker.exists():
        if not wait:raise ValueError('Wave report is not ready')
        with (dest/'run.lock').open('a') as lock:
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);busy=False;fcntl.flock(lock,fcntl.LOCK_UN)
            except BlockingIOError:busy=True
        if busy:idle_since=None
        elif idle_since is None:idle_since=time.monotonic()
        elif time.monotonic()-idle_since>300:
            state={'wave':wave,'stage':'paused','reason':'Worker stopped without a complete emitted report; inspect the wave log before resuming.','paid_usd':0}
            atomic(dest/'run-state.json',state);return state
        time.sleep(5)
    report=json.loads((folder/'report.json').read_text())
    if not report['complete'] or digest(report)!=json.loads(marker.read_text())['report_hash']:raise ValueError('Incomplete or changed wave report')
    result=subprocess.run([sys.executable,str(ROOT/'scripts/entry_status.py'),'--write-history'],cwd=ROOT,text=True,capture_output=True,check=True)
    (folder/'status-refresh.log').write_text(result.stdout+result.stderr)
    state={'wave':wave,'stage':'wave_report_ready' if report['continue_allowed'] else 'stopped_below_60_percent',
           'completed':report['completed'],'headwords':report['headwords'],'pass_fraction':report['pass_fraction'],
           'passed_two_readers_and_copy':report['passed_two_readers_and_copy'],
           'next_wave_allowed':report['continue_allowed'],'report':f'reports/{"hybrid" if m.get("line")=="hybrid-redrafts-v1" else "local"}-redraft-wave-{wave:03d}.md',
           'old_entries_changed':0,'paid_usd':report['paid_usd']}
    atomic(dest/'run-state.json',state);print(json.dumps(state,indent=2),flush=True);return state

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--hybrid',action='store_true');p.add_argument('--wave',type=int,default=1);p.add_argument('--dest',type=Path,default=DEST);p.add_argument('--wait',action='store_true');a=p.parse_args()
    if a.hybrid:
        from hybrid_redraft import DEST,registration
        a.dest=DEST if a.dest==ROOT/'.private/local-redraft' else a.dest
    finish(a.wave,a.dest,a.wait)
