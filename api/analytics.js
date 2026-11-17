const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(process.cwd(), 'public', 'data');
const cache = {};
function load(name) {
  if (!cache[name]) cache[name] = JSON.parse(fs.readFileSync(path.join(DATA_DIR, name), 'utf8'));
  return cache[name];
}
function safeNumber(v, fallback = null) {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}
function norm(s) {
  return String(s || '').normalize('NFKD').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}
function send(res, status, payload) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'public, max-age=60, s-maxage=300, stale-while-revalidate=3600');
  res.end(JSON.stringify(payload));
}
function asBool(v) { return v === true || v === 1 || v === 'true'; }
function getEvidence(type) {
  return load(type === 'batting' ? 'top10-batter-evidence.json' : 'top10-bowler-evidence.json');
}
function getFinal(type) {
  return load(type === 'batting' ? 'final-batter-rankings.json' : 'final-bowler-rankings.json');
}
function getPlayers(type) {
  return load(type === 'batting' ? 'batting-players.json' : 'bowling-players.json');
}
function mergeFinalEvidence(type) {
  const finalRows = getFinal(type);
  const evidence = getEvidence(type);
  const evidenceMap = new Map(evidence.map(x => [norm(type === 'batting' ? x.striker_canonical_name : x.bowler_canonical_name), x]));
  return finalRows.map(row => ({ ...row, evidence: evidenceMap.get(norm(type === 'batting' ? row.striker_canonical_name : row.bowler_canonical_name)) || null }));
}
function formatRankings(type, format, limit) {
  const rows = getPlayers(type).filter(r => r.format_label === format && asBool(r.eligible));
  const scoreKey = type === 'batting' ? 'score_balanced' : 'score_balanced';
  rows.sort((a,b) => safeNumber(b[scoreKey], -Infinity) - safeNumber(a[scoreKey], -Infinity));
  return rows.slice(0, limit).map((r,i) => ({ ...r, format_rank:i+1, rank_basis:'Format-specific balanced reference score' }));
}
function customRankings(type, params) {
  const format = params.get('format') || 'combined';
  const blend = params.get('blend') || 'ipl70';
  const iplWeightRequested = safeNumber(params.get('iplWeight'), null);
  const baseRows = getPlayers(type).filter(r => asBool(r.eligible));
  const dim = type === 'batting'
    ? ['output','adaptability','risk_control','consistency']
    : ['effectiveness','consistency'];
  let w = {};
  dim.forEach(k => w[k] = safeNumber(params.get(k), 1 / dim.length));
  const totalW = Object.values(w).reduce((s,x) => s + x,0);
  if (!totalW || Object.values(w).some(x => x < 0)) throw new Error('Weights must be non-negative and have a positive total.');
  Object.keys(w).forEach(k => w[k] /= totalW);
  const perFormat = new Map();
  for (const row of baseRows) {
    const score = dim.reduce((s,k) => s + safeNumber(row['score_'+k],0)*w[k],0);
    if (!Number.isFinite(score)) continue;
    const key = norm(row.player_name);
    if (!perFormat.has(key)) perFormat.set(key, { name:row.player_name, id:row.player_id, type:row.pace_spin_role || null, formats:{} });
    perFormat.get(key).formats[row.format_label] = { score, exposure:safeNumber(type==='batting'?row.pressure_balls:row.death_legal_balls,0), row };
  }
  let results=[];
  for (const p of perFormat.values()) {
    if (format === 'IPL' || format === 'T20I') {
      const f=p.formats[format];
      if (!f) continue;
      results.push({ player_name:p.name, player_id:p.id, pace_spin_role:p.type, format_score:f.score,
        score:f.score, format, exposure:f.exposure, profile:f.row });
    } else {
      const a=p.formats.IPL, b=p.formats.T20I;
      if (!a || !b) continue;
      let iw=iplWeightRequested;
      if (iw == null) {
        if (blend === 'equal') iw=.5;
        else if (blend === 'evidence') {
          const raw=Math.sqrt(Math.max(a.exposure,0))/(Math.sqrt(Math.max(a.exposure,0))+Math.sqrt(Math.max(b.exposure,0)) || 1);
          iw=Math.min(.7,Math.max(.3,raw));
        } else iw=.7;
      }
      iw=Math.min(.7,Math.max(.3,iw));
      const score=a.score*iw+b.score*(1-iw);
      results.push({ player_name:p.name, player_id:p.id, pace_spin_role:p.type,
        score, ipl_score:a.score, t20i_score:b.score, ipl_weight:iw, blend,
        ipl_exposure:a.exposure,t20i_exposure:b.exposure, profile:{IPL:a.row,T20I:b.row} });
    }
  }
  results.sort((a,b)=>b.score-a.score);
  return results.map((x,i)=>({...x,rank:i+1}));
}

function handle(req,res) {
  try {
    const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    const action=url.searchParams.get('action') || 'overview';
    const type=url.searchParams.get('type') || 'batting';
    if (!['batting','bowling'].includes(type)) return send(res,400,{error:'Type must be batting or bowling.'});
    if (action === 'overview' || action === 'meta') return send(res,200,load('meta.json'));
    if (action === 'rankings') {
      const format=url.searchParams.get('format') || 'combined';
      const limit=Math.max(1,Math.min(100,parseInt(url.searchParams.get('limit')||'20',10)||20));
      if (format==='combined') return send(res,200,{type,format,rank_basis:'Official mean rank across all tested weight and format-blend scenarios',rows:mergeFinalEvidence(type).slice(0,limit)});
      if (!['IPL','T20I'].includes(format)) return send(res,400,{error:'Format must be combined, IPL or T20I.'});
      return send(res,200,{type,format,rank_basis:'Format-specific balanced reference score',rows:formatRankings(type,format,limit)});
    }
    if (action === 'custom-rankings') {
      const rows=customRankings(type,url.searchParams);
      return send(res,200,{type,format:url.searchParams.get('format')||'combined',rank_basis:'Interactive custom-weight scenario; not the official final rank',rows});
    }
    if (action === 'scenarios') return send(res,200,load(type==='batting'?'batting-sensitivity.json':'bowling-sensitivity.json'));
    if (action === 'players') {
      const q=norm(url.searchParams.get('q')||'');
      const format=url.searchParams.get('format')||'all';
      const eligibleOnly=url.searchParams.get('eligible')==='true';
      let rows=getPlayers(type);
      if (q) rows=rows.filter(r=>norm(r.player_name).includes(q));
      if (format!=='all') rows=rows.filter(r=>r.format_label===format);
      if (eligibleOnly) rows=rows.filter(r=>asBool(r.eligible));
      return send(res,200,{type,count:rows.length,rows:rows.slice(0,100)});
    }
    if (action === 'player') {
      const q=norm(url.searchParams.get('name')||'');
      if (!q) return send(res,400,{error:'Pass a player name.'});
      const rows=getPlayers(type).filter(r=>norm(r.player_name)===q || norm(r.player_name).includes(q));
      if (!rows.length) return send(res,404,{error:'No matching player found.'});
      const final=mergeFinalEvidence(type).find(r=>norm(type==='batting'?r.striker_canonical_name:r.bowler_canonical_name)===q) || null;
      return send(res,200,{type,player_name:rows[0].player_name,formats:rows,final_record:final});
    }
    return send(res,404,{error:'Unknown action.'});
  } catch (err) {
    return send(res,500,{error:'Analytics request failed.',detail:err.message});
  }
}
module.exports = handle;
