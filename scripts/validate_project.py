#!/usr/bin/env python3
from pathlib import Path
import json, math
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'public'/'data'
checks=[]
def check(name, ok, detail=''):
    checks.append((name,bool(ok),detail))
meta=json.loads((D/'meta.json').read_text())
bat=json.loads((D/'batting-players.json').read_text())
bowl=json.loads((D/'bowling-players.json').read_text())
br=json.loads((D/'final-batter-rankings.json').read_text())
wr=json.loads((D/'final-bowler-rankings.json').read_text())
be=json.loads((D/'top10-batter-evidence.json').read_text())
we=json.loads((D/'top10-bowler-evidence.json').read_text())
check('Scope match counts',meta['matches_total']==828 and meta['matches_ipl']==364 and meta['matches_t20i']==464)
check('Eligible delivery rows',meta['eligible_delivery_rows']==193372)
check('Pressure-union deliveries',meta['pressure_union_deliveries']==57330)
check('Batter scorecard row count',len(bat)==1006)
check('Bowler scorecard row count',len(bowl)==612)
check('Batter both-format shortlist support',len(br)>=10 and meta['batters_both_formats_eligible']==13)
check('Bowler both-format shortlist support',len(wr)>=10 and meta['bowlers_both_formats_eligible']==62)
check('Top ten evidence rows',len(be)==10 and len(we)==10)
check('Batter final ranks are 1-10',sorted(int(x['final_rank']) for x in be)==list(range(1,11)))
check('Bowler final ranks are 1-10',sorted(int(x['final_rank']) for x in we)==list(range(1,11)))
check('No duplicate batter-format keys',len({(x['player_id'],x['source_format']) for x in bat})==len(bat))
check('No duplicate bowler-format keys',len({(x['player_id'],x['source_format']) for x in bowl})==len(bowl))
for name,rows,fields in [('batting',bat,['score_output','score_adaptability','score_risk_control','score_consistency','score_balanced']),('bowling',bowl,['score_effectiveness','score_consistency','score_balanced'])]:
    invalid=[]
    for r in rows:
      for f in fields:
        v=r.get(f)
        if v is not None and (not math.isfinite(float(v)) or float(v)<0 or float(v)>100):invalid.append((r.get('player_name'),f,v))
    check(f'{name} score bounds 0-100',not invalid, f'{len(invalid)} invalid values')
check('PDF methodology report exists',(ROOT/'public/reports/SupeRR_Pressure_Methodology_Report.pdf').exists())
check('HTML dashboard exists',(ROOT/'public/index.html').exists())
check('HTML methodology exists',(ROOT/'public/methodology.html').exists())
for name,ok,detail in checks: print(('PASS' if ok else 'FAIL')+f' | {name}'+(f' | {detail}' if detail else ''))
failed=[x for x in checks if not x[1]]
print(f'\n{len(checks)-len(failed)}/{len(checks)} checks passed')
if failed: raise SystemExit(1)
