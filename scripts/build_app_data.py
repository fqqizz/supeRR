#!/usr/bin/env python3
"""Prepare browser/API-ready datasets from the validated SupeRR analysis outputs."""
from pathlib import Path
import json
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'research-data' / 'processed'
OUT = ROOT / 'public' / 'data'
OUT.mkdir(parents=True, exist_ok=True)

def clean(v):
    if pd.isna(v): return None
    if isinstance(v, (np.integer,)): return int(v)
    if isinstance(v, (np.floating,)): return float(v)
    if isinstance(v, (np.bool_,)): return bool(v)
    if isinstance(v, bool): return v
    if isinstance(v, (int,float,str)): return v
    return str(v)

def records(df):
    return [{str(k): clean(v) for k,v in row.items()} for row in df.to_dict(orient='records')]

def save(name, obj):
    p=OUT/name
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(',',':')))
    print(f'{p.relative_to(ROOT)}: {p.stat().st_size/1024:.1f} KB')

# Batter scorecard and reliability metrics.
bat = pd.read_csv(SRC/'scoring/output/batting_scorecard_player_format.csv')
brel = pd.read_csv(SRC/'scoring/input/batting_reliability_player_format.csv')
brel_cols = ['striker_id','match_format','pressure_strike_rate_raw','normal_strike_rate_raw',
             'pressure_vs_normal_sr_delta_raw','pressure_boundary_probability_raw_per100',
             'pressure_dismissals','pressure_boundary_balls','pressure_sr_cluster_boot_ci95_low',
             'pressure_sr_cluster_boot_ci95_high','pressure_sr_ci_status']
brel = brel[[c for c in brel_cols if c in brel.columns]]
bat = bat.merge(brel, on=['striker_id','match_format'], how='left', validate='one_to_one')
bat = bat.rename(columns={'pressure_strike_rate_raw':'pressure_sr_raw','normal_strike_rate_raw':'normal_sr_raw'})
bat['format_label'] = bat.match_format.map({'T20':'IPL','T20I':'T20I'}).fillna(bat.match_format)
# Player names in scorecards are the stable display keys for the UI; numeric IDs are retained for audit.
bat = bat.rename(columns={
    'striker_id':'player_id','striker_canonical_name':'player_name','match_format':'source_format',
    'rank_eligible':'eligible','evidence_tier':'evidence_tier','pressure_balls_faced':'pressure_balls',
    'pressure_matches_with_balls':'pressure_matches','role_scoring_coverage_pct':'role_coverage_pct',
    'pressure_sr_eb_mean':'pressure_sr_eb','pressure_sr_eb_ci95_low':'pressure_sr_eb_ci_low',
    'pressure_sr_eb_ci95_high':'pressure_sr_eb_ci_high',
    'pressure_dismissal_probability_eb_mean_per100':'dismissal_probability_eb_per100',
    'pressure_dismissal_probability_eb_ci95_low_per100':'dismissal_probability_eb_ci_low_per100',
    'pressure_dismissal_probability_eb_ci95_high_per100':'dismissal_probability_eb_ci_high_per100',
    'score_output_weighted':'score_output','score_adaptability_weighted':'score_adaptability',
    'score_risk_control_weighted':'score_risk_control','score_consistency_weighted':'score_consistency',
    'score_balanced_equal_dimensions_weighted':'score_balanced',
    'score_output_led_weighted':'score_output_led','score_adaptability_led_weighted':'score_adaptability_led',
    'score_risk_control_led_weighted':'score_risk_control_led','score_consistency_led_weighted':'score_consistency_led',
})
# Keep a compact, documented player-format schema.
bat_fields = ['player_id','player_name','source_format','format_label','eligible','evidence_tier',
    'pressure_balls','pressure_matches','role_pressure_balls','role_pressure_matches_sum','role_strata',
    'role_coverage_pct','scored_role_pressure_balls','scored_role_strata','scored_role_names',
    'pressure_sr_raw','normal_sr_raw','pressure_vs_normal_sr_delta_raw','pressure_boundary_probability_raw_per100',
    'pressure_dismissals','pressure_boundary_balls','pressure_sr_eb','pressure_sr_eb_ci_low','pressure_sr_eb_ci_high',
    'pressure_dismissal_probability_eb_mean_per100','pressure_dismissal_probability_eb_ci95_low_per100',
    'pressure_dismissal_probability_eb_ci95_high_per100','score_output','score_adaptability','score_risk_control',
    'score_consistency','score_balanced','score_output_led','score_adaptability_led','score_risk_control_led',
    'score_consistency_led','rank_balanced_equal_dimensions','rank_output_led','rank_adaptability_led',
    'rank_risk_control_led','rank_consistency_led','core_sample_eligible','score_coverage_eligible']
bat = bat[[c for c in bat_fields if c in bat.columns]].copy()
bat=bat.rename(columns={'pressure_dismissal_probability_eb_mean_per100':'dismissal_probability_eb_per100',
                        'pressure_dismissal_probability_eb_ci95_low_per100':'dismissal_probability_eb_ci_low_per100',
                        'pressure_dismissal_probability_eb_ci95_high_per100':'dismissal_probability_eb_ci_high_per100'})

# Bowling scorecard and reliability metrics.
bow = pd.read_csv(SRC/'scoring/output/bowling_scorecard_player_format.csv')
brel = pd.read_csv(SRC/'scoring/input/bowling_reliability_player_format.csv')
brel_cols = ['bowler_id','match_format','death_phase_wicket_probability_raw_per100',
             'death_phase_known_boundary_event_rate_raw_per100_exposure']
brel=brel[[c for c in brel_cols if c in brel.columns]]
bow=bow.merge(brel,on=['bowler_id','match_format'],how='left',validate='one_to_one')
bow['format_label']=bow.match_format.map({'T20':'IPL','T20I':'T20I'}).fillna(bow.match_format)
bow=bow.rename(columns={'bowler_id':'player_id','bowler_canonical_name':'player_name','match_format':'source_format',
    'rank_eligible':'eligible','death_phase_legal_balls_bowled':'death_legal_balls',
    'death_phase_matches_with_legal_balls':'death_matches','death_phase_bowler_credited_wickets':'death_wickets',
    'death_phase_wicket_probability_eb_mean_per100':'death_wicket_rate_eb_per100',
    'death_phase_wicket_probability_eb_ci95_low_per100':'death_wicket_rate_eb_ci_low_per100',
    'death_phase_wicket_probability_eb_ci95_high_per100':'death_wicket_rate_eb_ci_high_per100',
    'score_balanced_reference':'score_balanced'})
bow_fields=['player_id','player_name','source_format','format_label','pace_spin_role','eligible','evidence_tier',
    'death_legal_balls','death_matches','death_wickets','legal_balls','wickets','known_boundary_events',
    'adjusted_wickets_per100_context_adjusted','adjusted_known_boundaries_per100_context_adjusted',
    'death_wicket_rate_eb_per100','death_wicket_rate_eb_ci_low_per100','death_wicket_rate_eb_ci_high_per100',
    'death_phase_known_boundary_event_rate_eb_mean_per100_exposure','non_death_baseline_legal_balls_bowled',
    'non_death_baseline_bowler_credited_wickets','death_vs_deep_lineup_legal_balls_bowled',
    'death_vs_deep_lineup_bowler_credited_wickets','consistency_matches','death_match_wicket_rate_median',
    'death_match_wicket_rate_iqr','score_effectiveness','score_consistency','score_balanced',
    'score_wicket_threat_led','score_consistency_led','rank_balanced_reference','rank_wicket_threat_led',
    'rank_consistency_led','environment_support_share_pct','core_sample_eligible','consistency_eligible']
bow=bow[[c for c in bow_fields if c in bow.columns]].copy()

# Official final ranked lists and full evidence tables.
bat_rank=pd.read_csv(SRC/'final_batter_rankings.csv')
bowl_rank=pd.read_csv(SRC/'final_bowler_rankings.csv')
bat_ev=pd.read_csv(SRC/'top10_batter_evidence.csv')
bowl_ev=pd.read_csv(SRC/'top10_bowler_evidence.csv')
bat_sens=pd.read_csv(SRC/'batting_ranking_sensitivity_all_scenarios.csv')
bowl_sens=pd.read_csv(SRC/'bowling_ranking_sensitivity_all_scenarios.csv')

# Rename format labels in final ranking and sensitivity outputs for presentation.
for df in (bat_rank,bowl_rank):
    for c in list(df.columns):
        if c.startswith('T20_'):
            df.rename(columns={c:'IPL_'+c[4:]},inplace=True)
for df in (bat_sens,bowl_sens):
    if 'blend' in df.columns:
        pass

# Metadata: values are carried from the source validation outputs and the final scope audit.
meta={
 'project':'SupeRR Analytics | Pressure Lab',
 'prepared_for':'SupeRR Selector Season 2, Round 1',
 'prepared_by':'Faaiz Qureshi',
 'data_scope':'IPL 2022-2026 and T20I only',
 'matches_total':828,'matches_ipl':364,'matches_t20i':464,
 'eligible_delivery_rows':193372,'unique_strikers':824,'unique_bowlers':596,
 'pressure_union_deliveries':57330,'death_phase_deliveries':43369,'collapse_deliveries':40013,
 'batter_player_format_rows':1006,'bowler_player_format_rows':612,
 'batters_rank_eligible_per_format_total':117,'batters_both_formats_eligible':13,
 'bowlers_rank_eligible_per_format_total':272,'bowlers_both_formats_eligible':62,
 'batting_scenarios':15,'bowling_scenarios':9,
 'pressure_definition':'Death phase OR five or more wickets lost before the delivery.',
 'death_definition':'At least 75% of scheduled legal balls completed; standard 20-over innings: overs 16-20.',
 'normal_definition':'Neither death phase nor collapse pressure is active.',
 'limitations':['Exact required run rate and score margin are not reconstructed reliably from the supplied extras data.',
  'Known bowling boundary events are a partial control proxy, not official economy or total runs conceded.',
  'Batter-runless legal balls are not labelled true dot balls.',
  'Percentile scores are relative peer positions, not probabilities or forecasts.',
  'Historical performance rankings do not establish current player or auction availability.']
}
# Validation values copied from the final source-scope validation outputs.
val=json.loads((SRC/'scoring/output/stage4_1_validation_summary.json').read_text())
meta['validation']=val

save('batting-players.json',records(bat))
save('bowling-players.json',records(bow))
save('final-batter-rankings.json',records(bat_rank))
save('final-bowler-rankings.json',records(bowl_rank))
save('top10-batter-evidence.json',records(bat_ev))
save('top10-bowler-evidence.json',records(bowl_ev))
save('batting-sensitivity.json',records(bat_sens))
save('bowling-sensitivity.json',records(bowl_sens))
save('meta.json',meta)
print('Export complete')
