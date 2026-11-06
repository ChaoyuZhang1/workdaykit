#!/usr/bin/env python3
"""WorkdayKit — static business-day calculator site.

Data comes from the HolidayKit repo (../holiday-kit/data): 95 countries of public
holidays plus China 调休/补班. Output is a fully static site in dist/.

Usage:
  python build.py
  python build.py --site-url https://workdaykit.pages.dev
"""
from __future__ import annotations

import argparse
import calendar
import json
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

try:
    import qrcode  # type: ignore
except ImportError:  # pragma: no cover
    qrcode = None

ROOT = Path(__file__).resolve().parent
HK = ROOT.parent / "holiday-kit"
sys.path.insert(0, str(HK / "scripts"))
from build_site import COUNTRY_NAMES, flag_emoji, slugify  # noqa: E402

SITE_NAME = "WorkdayKit"
SITE_TAGLINE = "Count business days between dates, skip weekends and holidays."
YEARS = [2025, 2026, 2027, 2028]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

CSS = """
:root{--ink:#15161a;--ink-soft:#2a2c33;--muted:#6b6f78;--line:#e8e5dd;--bg:#fbfaf7;--surface:#fff;--soft:#f4f1ea;--accent:#0f6b5c;--amber:#c2761a;--radius:18px;--radius-sm:12px;
--font-body:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;--font-display:ui-serif,Georgia,"Times New Roman","Songti SC",serif}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font-body);line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1040px;margin:0 auto;padding:0 22px}
.site-head{position:sticky;top:0;z-index:20;background:rgba(251,250,247,.9);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
.head-inner{display:flex;align-items:center;justify-content:space-between;height:62px}
.brand{display:inline-flex;align-items:center;gap:9px;font-weight:700;color:var(--ink);font-size:1.05rem}
.brand-mark{display:inline-grid;place-items:center;width:28px;height:28px;border-radius:9px;background:var(--ink);color:#fff;font-size:.8rem}
nav{display:flex;gap:20px}nav a{color:var(--ink-soft);font-size:.9rem;font-weight:500}
.hero{padding:56px 0 20px}
.eyebrow{font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--amber);font-weight:700;margin:0 0 12px}
h1{font-family:var(--font-display);font-size:clamp(2rem,4.6vw,3.2rem);line-height:1.1;letter-spacing:-.02em;margin:0 0 16px;font-weight:600}
.lede{font-size:1.05rem;color:var(--muted);max-width:38em;margin:0 0 24px}
.btn{display:inline-flex;align-items:center;justify-content:center;background:var(--ink);color:#fff;border:1px solid var(--ink);border-radius:999px;padding:11px 22px;font-weight:600;font-size:.92rem;cursor:pointer}
.btn:hover{opacity:.92;text-decoration:none}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-sm);padding:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin:18px 0}
.grid a.card{display:block;color:var(--ink);transition:transform .15s ease,box-shadow .15s ease}
.grid a.card:hover{transform:translateY(-2px);box-shadow:0 14px 34px rgba(21,22,26,.08);text-decoration:none}
.grid h3{margin:6px 0 3px;font-size:.98rem}
.grid p{margin:0;color:var(--muted);font-size:.82rem}
.flag{font-size:1.3rem}
.sec{margin:42px 0}
.sec h2{font-family:var(--font-display);font-size:clamp(1.35rem,2.2vw,1.8rem);margin:0 0 8px}
.sec .sub{color:var(--muted);margin:0 0 18px;font-size:.95rem}
.calc{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:22px;box-shadow:0 18px 50px rgba(21,22,26,.08)}
.calc-tabs{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.calc-tabs button{border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:7px 16px;font-size:.86rem;cursor:pointer;color:var(--ink-soft)}
.calc-tabs button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.calc-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:12px}
.calc label{display:block;font-size:.8rem;color:var(--muted);margin-bottom:4px}
.calc input,.calc select{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:10px;font-size:.92rem;background:var(--surface);color:var(--ink)}
.calc-result{margin-top:16px}
.result-card{background:var(--soft);border-radius:12px;padding:16px 18px}
.result-actions{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
.result-actions .btn{padding:8px 16px;font-size:.84rem}
.result-num{font-family:var(--font-display);font-size:2.4rem;line-height:1;color:var(--accent)}
.result-num span{font-size:.9rem;color:var(--muted);font-family:var(--font-body);margin-left:8px}
.result-detail{color:var(--muted);font-size:.88rem;margin-top:8px}
.tbl-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--surface)}
table{width:100%;border-collapse:collapse}
th,td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;font-size:.9rem}
th{background:var(--soft);font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
tr:last-child td{border-bottom:0}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}
.chip{font-size:.8rem;border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:4px 12px}
.ad{border:1px dashed #d8d3c7;background:#f7f4ee;color:#9a958a;border-radius:12px;padding:18px;min-height:90px;display:grid;place-items:center;font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;margin:28px 0}
.years{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 18px}
.years a{border:1px solid var(--line);border-radius:999px;padding:6px 14px;font-size:.86rem;color:var(--ink)}
.years a:hover{border-color:var(--ink);text-decoration:none}
.years a.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.callout{border-left:3px solid var(--amber);background:#fdf6e9;padding:12px 16px;border-radius:10px;font-size:.9rem;margin:16px 0}
.faq dt{font-weight:650;margin-top:14px}.faq dd{margin:4px 0 0;color:var(--muted);font-size:.92rem}
.site-foot{border-top:1px solid var(--line);margin-top:56px;padding:26px 0 40px;font-size:.84rem;color:var(--muted)}
.muted{color:var(--muted)}
html{scroll-behavior:smooth}
.reveal{opacity:0;transform:translateY(14px);transition:opacity .62s cubic-bezier(.16,1,.3,1),transform .62s cubic-bezier(.16,1,.3,1)}
.reveal.in{opacity:1;transform:none}
.site-head{transition:box-shadow .3s cubic-bezier(.16,1,.3,1)}
.site-head.scrolled{box-shadow:0 10px 34px rgba(21,22,26,.08)}
.btn{transition:transform .18s cubic-bezier(.16,1,.3,1),box-shadow .25s}
.btn:hover{transform:translateY(-1px);box-shadow:0 12px 28px rgba(21,22,26,.18)}
.card{transition:transform .28s cubic-bezier(.16,1,.3,1),box-shadow .28s}
.card:hover{transform:translateY(-3px);box-shadow:0 20px 48px rgba(21,22,26,.10)}
.hero{position:relative;overflow:hidden}
.hero::before{content:"";position:absolute;inset:-50% -10% auto -10%;height:130%;background:radial-gradient(600px 300px at 18% 6%,rgba(15,107,92,.09),transparent 62%),radial-gradient(520px 260px at 88% 0%,rgba(194,118,26,.09),transparent 60%);pointer-events:none}
.hero>*{position:relative}
tbody tr{transition:background .15s}
tbody tr:hover{background:#faf7f0}
::selection{background:rgba(15,107,92,.18)}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}html{scroll-behavior:auto}}
@media(max-width:640px){nav{gap:12px}nav a{font-size:.82rem}.calc{padding:16px}.head-inner{height:auto;min-height:56px;flex-wrap:wrap;padding:8px 0}}
.cd-hero{position:relative;overflow:hidden;border-radius:26px;margin:28px 0 10px;padding:44px 34px;background:linear-gradient(135deg,#0d1b18 0%,#0b1520 55%,#0a0f16 100%);color:#eef4f2;box-shadow:0 30px 80px rgba(10,16,24,.28)}
.cd-hero::before{content:"";position:absolute;inset:-40% -20% auto -20%;height:130%;background:radial-gradient(600px 320px at 18% 6%,rgba(34,197,94,.20),transparent 62%),radial-gradient(520px 280px at 86% 0%,rgba(56,189,248,.18),transparent 60%);pointer-events:none}
.cd-hero>*{position:relative}
.cd-hero .eyebrow{color:#7dd3a8}
.cd-hero h1{color:#f7fbfa}
.cd-hero .lede{color:#b9c6c2;max-width:36em}
.cd-wrap{display:grid;grid-template-columns:220px 1fr;gap:26px;align-items:center;margin-top:18px}
@media(max-width:760px){.cd-wrap{grid-template-columns:1fr}}
.cd-ring{position:relative;width:200px;height:200px;margin:0 auto;border-radius:50%;
  background:conic-gradient(#22c55e 0deg,#22c55e calc(var(--p,85) * 3.6deg),rgba(255,255,255,.10) calc(var(--p,85) * 3.6deg));
  box-shadow:0 0 40px rgba(34,197,94,.18);transition:background .9s cubic-bezier(.16,1,.3,1)}
.cd-ring::after{content:"";position:absolute;inset:16px;border-radius:50%;background:#0a141c;box-shadow:inset 0 0 0 1px rgba(255,255,255,.06)}
.cd-ring-mid{position:absolute;inset:0;display:grid;place-items:center;text-align:center;z-index:2}
.lang-select{border:1px solid var(--line);background:var(--surface);color:var(--ink-soft);border-radius:9px;padding:4px 8px;font-size:.8rem;margin-left:14px}
@media(max-width:640px){nav{flex-wrap:wrap;gap:10px}.lang-select{margin-left:0}}
.cd-big{font-family:var(--font-display);font-size:3.1rem;line-height:1;color:#f7fbfa;position:relative;z-index:2}
.cd-big span{display:block;font-family:var(--font-body);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:#8fa39d;margin-top:6px}
.cd-tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px}
.cd-tile{background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.10);border-radius:16px;padding:16px 18px;backdrop-filter:blur(6px)}
.cd-tile .v{font-family:var(--font-display);font-size:1.9rem;line-height:1.05;color:#f7fbfa}
.cd-tile .k{font-size:.72rem;color:#94a8a2;margin-top:4px;letter-spacing:.04em}
.cd-tile .dot-live{display:inline-block;width:7px;height:7px;border-radius:50%;background:#22c55e;margin-right:6px;animation:cdpulse 1.8s infinite}
.cd-ico{display:inline-grid;place-items:center;width:30px;height:30px;border-radius:9px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);font-size:.88rem;line-height:1;margin-bottom:10px}
.cd-note{font-size:.76rem;color:#94a8a2;margin:14px 0 0;line-height:1.6;max-width:70ch}
.cd-note b{color:#d7e5df;font-weight:600}
@keyframes cdpulse{0%{box-shadow:0 0 0 0 rgba(34,197,94,.5)}70%{box-shadow:0 0 0 7px rgba(34,197,94,0)}100%{box-shadow:0 0 0 0 rgba(34,197,94,0)}}
.cd-country{display:flex;gap:10px;align-items:center;margin-top:20px;color:#b9c6c2;font-size:.86rem;flex-wrap:wrap}
.cd-country select{background:rgba(255,255,255,.08);color:#eef4f2;border:1px solid rgba(255,255,255,.16);border-radius:10px;padding:8px 12px;font-size:.86rem}
.cd-note{color:#8fa39d;font-size:.8rem;margin-top:14px}
.cd-pop{animation:cdpop .6s cubic-bezier(.16,1,.3,1)}
@keyframes cdpop{0%{transform:scale(.94);opacity:.6}100%{transform:scale(1);opacity:1}}
@media(prefers-reduced-motion:reduce){.cd-ring .ring-fg{transition:none}.cd-tile .dot-live{animation:none}}
"""

MOTION_JS = """
(function(){
  var head = document.querySelector('.site-head');
  function onScroll(){ if (head) head.classList.toggle('scrolled', window.scrollY > 8); }
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || !('IntersectionObserver' in window)) return;
  var io = new IntersectionObserver(function(es){
    es.forEach(function(en){ if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
  }, { rootMargin: '0px 0px -40px 0px', threshold: 0.08 });
  document.querySelectorAll('.sec, .card, .calc, .tbl-wrap, .grid > *').forEach(function(el){ el.classList.add('reveal'); io.observe(el); });
  var nums = document.querySelectorAll('.result-num, .stat .num');
  if (nums.length) {
    var io2 = new IntersectionObserver(function(es){
      es.forEach(function(en){
        if (!en.isIntersecting) return;
        var el = en.target; io2.unobserve(el);
        var n = parseInt(el.textContent.trim().replace(/,/g, ''), 10);
        if (isNaN(n) || n > 1000000) return;
        var t0 = performance.now();
        function step(t){ var p = Math.min(1, (t - t0) / 800); el.textContent = Math.round(n * (1 - Math.pow(1 - p, 3))).toLocaleString(); if (p < 1) requestAnimationFrame(step); }
        requestAnimationFrame(step);
      });
    }, { threshold: 0.4 });
    nums.forEach(function(el){ io2.observe(el); });
  }
})();
"""


COUNTDOWN_JS = """
(function(){
  var root=document.getElementById('hk-countdown'); if(!root) return;
  var COUNTRIES=window.WK.countries||[];
  var TZ={'Asia/Shanghai':'CN','Asia/Hong_Kong':'HK','Asia/Taipei':'TW','Asia/Tokyo':'JP','Asia/Seoul':'KR',
    'Asia/Singapore':'SG','Asia/Kuala_Lumpur':'MY','Asia/Bangkok':'TH','Asia/Jakarta':'ID','Asia/Manila':'PH',
    'Asia/Kolkata':'IN','Asia/Calcutta':'IN','Asia/Karachi':'PK','Asia/Dubai':'AE','Asia/Riyadh':'SA',
    'Europe/London':'GB','Europe/Dublin':'IE','Europe/Paris':'FR','Europe/Berlin':'DE','Europe/Madrid':'ES',
    'Europe/Rome':'IT','Europe/Amsterdam':'NL','Europe/Brussels':'BE','Europe/Vienna':'AT','Europe/Zurich':'CH',
    'Europe/Lisbon':'PT','Europe/Stockholm':'SE','Europe/Oslo':'NO','Europe/Copenhagen':'DK','Europe/Helsinki':'FI',
    'Europe/Warsaw':'PL','Europe/Prague':'CZ','Europe/Budapest':'HU','Europe/Athens':'GR','Europe/Moscow':'RU',
    'America/New_York':'US','America/Chicago':'US','America/Denver':'US','America/Los_Angeles':'US',
    'America/Toronto':'CA','America/Vancouver':'CA','America/Mexico_City':'MX','America/Sao_Paulo':'BR',
    'America/Argentina/Buenos_Aires':'AR','Australia/Sydney':'AU','Australia/Melbourne':'AU','Pacific/Auckland':'NZ',
    'Africa/Johannesburg':'ZA','Africa/Cairo':'EG','Africa/Lagos':'NG','Africa/Nairobi':'KE','Asia/Jerusalem':'IL',
    'Europe/Istanbul':'TR'};
  var LOC={'zh-cn':'CN','zh-tw':'TW','zh-hk':'HK','ja':'JP','ko':'KR','th':'TH','vi':'VN','id':'ID','ms':'MY',
    'en-gb':'GB','en-au':'AU','en-ca':'CA','en-nz':'NZ','en-in':'IN','de':'DE','fr':'FR','es':'ES','it':'IT',
    'pt':'PT','nl':'NL','pl':'PL','ru':'RU','tr':'TR','ar':'AE','he':'IL'};
  function pad(n){return (n<10?'0':'')+n;}
  function iso(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());}
  function biz(hol,makeup,from,to){var n=0,d=new Date(from);while(d<=to){var k=iso(d);var wk=d.getDay()===0||d.getDay()===6;if(wk?!!makeup[k]:!hol[k])n++;d.setDate(d.getDate()+1);}return n;}
  function setText(id,v){var el=document.getElementById(id);if(el)el.textContent=v;}
  var MONB=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  function updateBars(mo){
    var bars=document.querySelectorAll('#cd-bars .bz'); if(!bars.length) return;
    var vals=[];
    for(var i=0;i<12;i++){ vals.push(mo&&mo[MONB[i]]!=null?mo[MONB[i]]:0); }
    var lo=Math.min.apply(null,vals), hi=Math.max.apply(null,vals), rng=Math.max(hi-lo,1);
    for(var j=0;j<bars.length;j++){
      var h=Math.round(20+(vals[j]-lo)/rng*66);
      bars[j].style.height=h+'%';
      var b=bars[j].querySelector('b'); if(b) b.textContent=vals[j];
    }
  }
  function render(d,cc){
    var today=new Date();today.setHours(0,0,0,0);var y=today.getFullYear();
    var hol={},mk={};
    (d.holidays||[]).forEach(function(x){hol[x]=1;});
    (d.makeup||[]).forEach(function(x){mk[x]=1;});
    var monthEnd=new Date(y,today.getMonth()+1,0),yearEnd=new Date(y,11,31),yearStart=new Date(y,0,1);
    var monthLeft=biz(hol,mk,today,monthEnd);
    var yearLeft=biz(hol,mk,today,yearEnd);
    var total=biz(hol,mk,yearStart,yearEnd);
    var pct=total?Math.round((total-yearLeft)/total*100):0;
    setText('cd-year',yearLeft); setText('cd-month',monthLeft); setText('cd-total',total);
    setText('cd-pct',pct+'%');
    updateBars(d.monthly);
    var fg=document.querySelector('[data-cd-ring]');
    if(fg){ fg.style.setProperty('--p', pct); }
    var keys=Object.keys(hol).sort(), next=null;
    for(var i=0;i<keys.length;i++){ if(keys[i]>=iso(today)){ next=keys[i]; break; } }
    if(next){ setText('cd-next',Math.round((new Date(next+'T00:00:00')-today)/86400000)); }
    else {
      setText('cd-next','—');
      fetch('/api/v1/business/'+cc+'/'+(y+1)+'.json').then(function(r){return r.ok?r.json():null;}).then(function(nd){
        if(nd&&nd.holidays&&nd.holidays.length){
          var h=nd.holidays.slice().sort()[0];
          var ndays=Math.round((new Date(h+'T00:00:00')-today)/86400000);
          setText('cd-next',ndays);
          if(window.WK_SHARE){ window.WK_SHARE.next=ndays; if(window.WK_SHARE_REFRESH) window.WK_SHARE_REFRESH(); }
        }
      }).catch(function(){});
    }
    if(window.WK_SHARE){
      var nm=(COUNTRIES.filter(function(x){return x.code===cc;})[0]||{}).name||cc;
      window.WK_SHARE.country=nm;
      window.WK_SHARE.yearLeft=yearLeft;
      window.WK_SHARE.monthLeft=monthLeft;
      window.WK_SHARE.total=total;
      window.WK_SHARE.pct=pct;
      window.WK_SHARE.next=(next?Math.round((new Date(next+'T00:00:00')-today)/86400000):'—');
      if(window.WK_SHARE_REFRESH) window.WK_SHARE_REFRESH();
    }
  }
  function load(cc){
    var year=new Date().getFullYear();
    fetch('/api/v1/business/'+cc+'/'+year+'.json').then(function(r){return r.ok?r.json():null;}).then(function(d){
      if(!d){ if(cc!=='US') load('US'); return; }
      render(d,cc);
    }).catch(function(){ if(cc!=='US') load('US'); });
  }
  function guess(){
    try{var tz=Intl.DateTimeFormat().resolvedOptions().timeZone||'';if(TZ[tz])return TZ[tz];}catch(e){}
    var l=(navigator.language||'en').toLowerCase();
    if(LOC[l])return LOC[l];
    var b=l.split('-')[0]; if(LOC[b])return LOC[b];
    return 'US';
  }
  function supported(cc){ for(var i=0;i<COUNTRIES.length;i++) if(COUNTRIES[i].code===cc) return true; return false; }
  function init(){
    var defaultCc=(root.getAttribute('data-country')||'US').toUpperCase();
    var sel=document.querySelector('[data-cd-country]');
    var yearEl=document.getElementById('cd-year-label');
    if(yearEl) yearEl.textContent=new Date().getFullYear();
    fetch('/geo').then(function(r){return r.ok?r.json():null;}).then(function(g){
      var c=((g&&g.country)||'').toUpperCase();
      if(!c||!supported(c)) c=supported(defaultCc)?defaultCc:guess();
      if(sel) sel.value=c;
      load(c);
    }).catch(function(){ load(defaultCc); });
    function clock(){var el=document.getElementById('cd-clock'); if(!el)return;
      try{el.textContent=new Date().toLocaleTimeString(undefined,{hour12:false});}catch(e){}
    }
    clock(); setInterval(clock,1000);
    if(sel) sel.addEventListener('change',function(){ load(sel.value); });
  }
  init();
})();
"""


I18N_JS = """
(function(){
  var D={
    en:{'nav.calc':'Calculator','nav.cd':'Countdown','nav.countries':'Countries','nav.api':'API','nav.about':'About',
      'hero.eyebrow':'Business days · weekends · public holidays','hero.h1':'Business days calculator',
      'hero.lede':'Count working days between two dates, or add business days to a date — for 95 countries, skipping weekends and public holidays (including China\\'s 调休/补班 rules).',
      'calc.tab1':'Days between dates','calc.tab2':'Add / subtract business days','calc.calc':'Calculate',
      'calc.addcal':'Add to calendar','calc.country':'Country','calc.year':'Year','calc.start':'Start date','calc.end':'End date','calc.addn':'Business days (negative to subtract)','home.countries':'Business days by country','home.countries.sub':'How many business days are left this year, country by country.','home.countdown':'Business days left this year',
      'home.countdown.sub':'A live countdown of how many working days remain — auto-detected for your country.',
      'home.how':'How it works','home.faq':'FAQ',
      'cd.eyebrow':'Live business-day countdown','cd.lede':'Detected automatically from your location. Counts working days only — weekends and public holidays excluded.','cd.what':'What this counts','cd.left':'business days left','cd.month':'business days left this month',
      'cd.next':'days until next public holiday','cd.total':'business days this year','cd.clock':'your local time',
      'cd.pct':'of the year\\'s business days done','foot.note':'Count business days between dates, skip weekends and holidays.'},
    zh:{'nav.calc':'计算器','nav.cd':'倒计时','nav.countries':'国家','nav.api':'API','nav.about':'关于',
      'hero.eyebrow':'工作日 · 周末 · 公共假期','hero.h1':'工作日计算器',
      'hero.lede':'计算两个日期之间的工作日，或在日期上加减工作日——支持 95 个国家，自动排除周末与公共假期（含中国调休/补班）。',
      'calc.tab1':'两个日期之间','calc.tab2':'加减工作日','calc.calc':'计算',
      'calc.addcal':'加入日历','calc.country':'国家','calc.year':'年份','calc.start':'开始日期','calc.end':'结束日期','calc.addn':'工作日天数（负数表示减去）','home.countries':'按国家查看工作日','home.countries.sub':'按国家查看今年还剩多少工作日。','home.countdown':'今年还剩多少工作日',
      'home.countdown.sub':'实时倒计时，按你的位置自动识别国家。',
      'home.how':'怎么用','home.faq':'常见问题',
      'cd.eyebrow':'实时工作日倒计时','cd.lede':'根据你的位置自动识别，只计算工作日——排除周末与公共假期（中国补班计入工作日）。','cd.what':'这个数字怎么算的','cd.left':'个工作日剩余','cd.month':'本月剩余工作日',
      'cd.next':'距离下一个公共假期','cd.total':'今年工作日总数','cd.clock':'你的当地时间',
      'cd.pct':'今年工作日已完成','foot.note':'计算工作日，自动跳过周末和假期。'},
    ja:{'nav.calc':'計算機','nav.cd':'カウントダウン','nav.countries':'国','nav.api':'API','nav.about':'概要',
      'hero.eyebrow':'営業日 · 週末 · 祝日','hero.h1':'営業日計算機',
      'hero.lede':'2つの日付の間の営業日数を計算、または営業日を加減。95か国対応、週末と祝日を除外（中国の振替休日/振替出勤も考慮）。',
      'calc.tab1':'日付間','calc.tab2':'営業日を加減','calc.calc':'計算',
      'calc.addcal':'カレンダーに追加','calc.country':'国','calc.year':'年','calc.start':'開始日','calc.end':'終了日','calc.addn':'営業日数（マイナスで減算）','home.countries':'国別の営業日','home.countries.sub':'今年の残り営業日を国別に。','home.countdown':'今年の残り営業日',
      'home.countdown.sub':'現在地から自動判定した残り営業日のライブカウントダウン。',
      'home.how':'使い方','home.faq':'FAQ',
      'cd.eyebrow':'営業日ライブカウントダウン','cd.lede':'現在地から自動判定。営業日のみを数え、週末と祝日を除外します。','cd.what':'この数字の計算方法','cd.left':'営業日残り','cd.month':'今月の残り営業日',
      'cd.next':'次の祝日まで','cd.total':'今年の営業日','cd.clock':'現地時刻',
      'cd.pct':'今年の営業日消化率','foot.note':'週末と祝日を除いた営業日を計算。'},
    ko:{'nav.calc':'계산기','nav.cd':'카운트다운','nav.countries':'국가','nav.api':'API','nav.about':'소개',
      'hero.eyebrow':'영업일 · 주말 · 공휴일','hero.h1':'영업일 계산기',
      'hero.lede':'두 날짜 사이 영업일을 계산하거나 영업일을 더하고 빼세요. 95개국 지원, 주말·공휴일 제외(중국 조정휴무/보충근무 포함).',
      'calc.tab1':'날짜 사이','calc.tab2':'영업일 더하기/빼기','calc.calc':'계산',
      'calc.addcal':'캘린더에 추가','calc.country':'국가','calc.year':'연도','calc.start':'시작일','calc.end':'종료일','calc.addn':'영업일 수(음수는 빼기)','home.countries':'국가별 영업일','home.countries.sub':'올해 남은 영업일을 국가별로.','home.countdown':'올해 남은 영업일',
      'home.countdown.sub':'위치 기반으로 자동 인식한 남은 영업일 실시간 카운트다운.',
      'home.how':'사용법','home.faq':'자주 묻는 질문',
      'cd.eyebrow':'실시간 영업일 카운트다운','cd.lede':'위치를 자동 감지해 영업일만 계산합니다. 주말과 공휴일은 제외합니다.','cd.what':'계산 방식','cd.left':'영업일 남음','cd.month':'이번 달 남은 영업일',
      'cd.next':'다음 공휴일까지','cd.total':'올해 영업일','cd.clock':'현지 시간',
      'cd.pct':'올해 영업일 진행률','foot.note':'주말과 공휴일을 제외한 영업일 계산.'},
    es:{'nav.calc':'Calculadora','nav.cd':'Cuenta atrás','nav.countries':'Países','nav.api':'API','nav.about':'Acerca de',
      'hero.eyebrow':'Días laborables · fines de semana · festivos','hero.h1':'Calculadora de días laborables',
      'hero.lede':'Cuenta días laborables entre dos fechas o suma/resta días laborables — 95 países, sin fines de semana ni festivos (incluye 调休/补班 de China).',
      'calc.tab1':'Días entre fechas','calc.tab2':'Sumar/restar días laborables','calc.calc':'Calcular',
      'calc.addcal':'Añadir al calendario','calc.country':'País','calc.year':'Año','calc.start':'Fecha inicial','calc.end':'Fecha final','calc.addn':'Días laborables (negativo para restar)','home.countries':'Días laborables por país','home.countries.sub':'Cuántos días laborables quedan este año, país por país.','home.countdown':'Días laborables que quedan este año',
      'home.countdown.sub':'Cuenta atrás en vivo de días laborables restantes, detectada por tu ubicación.',
      'home.how':'Cómo funciona','home.faq':'Preguntas frecuentes',
      'cd.eyebrow':'Cuenta atrás de días laborables','cd.lede':'Detectado automáticamente por tu ubicación. Solo cuenta días laborables, sin fines de semana ni festivos.','cd.what':'Cómo se calcula','cd.left':'días laborables restantes','cd.month':'días laborables este mes',
      'cd.next':'días hasta el próximo festivo','cd.total':'días laborables este año','cd.clock':'tu hora local',
      'cd.pct':'del año laboral completado','foot.note':'Calcula días laborables sin fines de semana ni festivos.'},
    fr:{'nav.calc':'Calculateur','nav.cd':'Compte à rebours','nav.countries':'Pays','nav.api':'API','nav.about':'À propos',
      'hero.eyebrow':'Jours ouvrés · week-ends · jours fériés','hero.h1':'Calculateur de jours ouvrés',
      'hero.lede':'Comptez les jours ouvrés entre deux dates, ajoutez ou retirez des jours ouvrés — 95 pays, hors week-ends et jours fériés (y compris 调休/补班 en Chine).',
      'calc.tab1':'Entre deux dates','calc.tab2':'Ajouter/retirer des jours ouvrés','calc.calc':'Calculer',
      'calc.addcal':'Ajouter au calendrier','calc.country':'Pays','calc.year':'Année','calc.start':'Date de début','calc.end':'Date de fin','calc.addn':'Jours ouvrés (négatif pour retirer)','home.countries':'Jours ouvrés par pays','home.countries.sub':'Combien de jours ouvrés restent cette année, pays par pays.','home.countdown':'Jours ouvrés restants cette année',
      'home.countdown.sub':'Compte à rebours en direct des jours ouvrés restants, détecté selon votre position.',
      'home.how':'Comment ça marche','home.faq':'FAQ',
      'cd.eyebrow':'Compte à rebours des jours ouvrés','cd.lede':'Détecté selon votre position. Compte uniquement les jours ouvrés, hors week-ends et fériés.','cd.what':'Comment est calculé ce nombre','cd.left':'jours ouvrés restants','cd.month':'jours ouvrés ce mois',
      'cd.next':'jours avant le prochain férié','cd.total':'jours ouvrés cette année','cd.clock':'votre heure locale',
      'cd.pct':'de l\\'année ouvrée écoulée','foot.note':'Compte les jours ouvrés hors week-ends et fériés.'},
    de:{'nav.calc':'Rechner','nav.cd':'Countdown','nav.countries':'Länder','nav.api':'API','nav.about':'Über',
      'hero.eyebrow':'Werktage · Wochenenden · Feiertage','hero.h1':'Werktage-Rechner',
      'hero.lede':'Werktage zwischen zwei Daten zählen oder Werktage addieren/subtrahieren — 95 Länder, ohne Wochenenden und Feiertage (inkl. chinesischer 调休/补班).',
      'calc.tab1':'Zwischen Daten','calc.tab2':'Werktage addieren/subtrahieren','calc.calc':'Berechnen',
      'calc.addcal':'Zum Kalender','calc.country':'Land','calc.year':'Jahr','calc.start':'Startdatum','calc.end':'Enddatum','calc.addn':'Werktage (negativ zum Abziehen)','home.countries':'Werktage nach Land','home.countries.sub':'Wie viele Werktage dieses Jahr übrig sind, Land für Land.','home.countdown':'Restliche Werktage dieses Jahr',
      'home.countdown.sub':'Live-Countdown der verbleibenden Werktage, automatisch nach Standort.',
      'home.how':'So funktioniert es','home.faq':'FAQ',
      'cd.eyebrow':'Live-Werktage-Countdown','cd.lede':'Automatisch nach Standort erkannt. Zählt nur Werktage, ohne Wochenenden und Feiertage.','cd.what':'So wird gerechnet','cd.left':'Werktage übrig','cd.month':'Werktage diesen Monat übrig',
      'cd.next':'Tage bis zum nächsten Feiertag','cd.total':'Werktage dieses Jahr','cd.clock':'Ihre Ortszeit',
      'cd.pct':'des Arbeitsjahres erledigt','foot.note':'Werktage ohne Wochenenden und Feiertage zählen.'}
  };
  var CC_LANG={CN:'zh',TW:'zh',HK:'zh',SG:'zh',JP:'ja',KR:'ko',ES:'es',MX:'es',AR:'es',CO:'es',CL:'es',PE:'es',FR:'fr',BE:'fr',CA:'fr',DE:'de',AT:'de',CH:'de'};
  var lang='en';
  try{ var saved=localStorage.getItem('wk_lang'); if(saved&&D[saved]) lang=saved; }catch(e){}
  function detect(){
    var n=(navigator.language||'en').toLowerCase(), b=n.split('-')[0];
    if(D[b]) return b;
    return 'en';
  }
  function t(k){ var d=D[lang]||D.en; return d[k]||D.en[k]||k; }
  function apply(){
    document.documentElement.lang=lang;
    document.querySelectorAll('[data-i18n]').forEach(function(el){ el.textContent=t(el.getAttribute('data-i18n')); });
    document.querySelectorAll('[data-hk-lang]').forEach(function(s){ s.value=lang; });
    document.dispatchEvent(new CustomEvent('hk-lang-changed'));
  }
  function set(l){ if(!D[l]) return; lang=l; try{localStorage.setItem('wk_lang',l);}catch(e){} apply(); }
  window.HKI18N={t:t,set:set,lang:function(){return lang;},apply:apply};
  document.addEventListener('DOMContentLoaded',function(){
    apply();
    document.querySelectorAll('[data-hk-lang]').forEach(function(s){ s.addEventListener('change',function(){set(this.value);}); });
    if(!localStorage.getItem('wk_lang')){
      var auto=detect();
      fetch('/geo').then(function(r){return r.ok?r.json():null;}).then(function(d){
        var c=((d&&d.country)||'').toUpperCase();
        var l=CC_LANG[c]||auto;
        if(D[l]) set(l);
      }).catch(function(){ if(auto!=='en') set(auto); });
    }
  });
})();
"""


SHARE_CSS = """
.share-modal{position:fixed;inset:0;z-index:80;background:rgba(12,16,22,.62);backdrop-filter:blur(6px);display:none;align-items:center;justify-content:center;padding:20px}
.share-modal.on{display:flex}
.share-panel{background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:18px;max-width:min(780px,96vw);max-height:94vh;overflow:auto;box-shadow:0 30px 80px rgba(15,17,21,.35)}
.share-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;font-size:.95rem}
.share-close{border:1px solid var(--line);background:var(--surface);width:32px;height:32px;border-radius:10px;cursor:pointer;font-size:1rem;line-height:1}
.share-canvas{display:block;width:100%;max-height:52vh;height:auto;border-radius:12px;background:#111;margin:0 auto}
.share-controls{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0}
.share-controls label{font-size:.72rem;color:var(--muted);display:flex;flex-direction:column;gap:4px;text-transform:uppercase;letter-spacing:.06em}
.share-controls select{padding:7px 10px;border:1px solid var(--line);border-radius:9px;background:var(--surface);font-size:.85rem;text-transform:none}
.share-btns{display:flex;gap:8px;flex-wrap:wrap}
.share-btns .btn{padding:9px 16px;font-size:.85rem}
.share-platforms{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.share-plat{border:1px solid var(--line);background:var(--surface);color:var(--ink-soft);border-radius:999px;padding:7px 14px;font-size:.8rem;cursor:pointer;transition:all .18s}
.share-plat:hover{border-color:var(--ink);transform:translateY(-1px)}
.share-hint{font-size:.72rem;color:var(--muted);margin:10px 0 0;line-height:1.5}
/* prominent share CTA + floating button */
.btn-share-hot{position:relative;display:inline-flex;align-items:center;gap:9px;border:0;cursor:pointer;font-weight:700;font-size:.95rem;padding:14px 24px;border-radius:999px;color:#04231a;background:linear-gradient(100deg,#34d399,#22d3ee,#a78bfa,#34d399);background-size:280% 100%;animation:wkhotgrad 7s linear infinite;box-shadow:0 12px 32px rgba(34,211,238,.32),0 0 0 1px rgba(255,255,255,.28) inset;transition:transform .18s,box-shadow .18s}
.btn-share-hot:hover{transform:translateY(-2px) scale(1.02);box-shadow:0 18px 42px rgba(34,211,238,.42)}
@keyframes wkhotgrad{to{background-position:280% 50%}}
.share-fab{position:fixed;right:20px;bottom:100px;z-index:70;display:inline-flex;align-items:center;gap:9px;padding:12px 18px;border-radius:999px;border:1px solid rgba(255,255,255,.35);cursor:pointer;color:#04231a;font-weight:800;font-size:.86rem;background:linear-gradient(120deg,#34d399,#22d3ee);box-shadow:0 12px 30px rgba(34,211,238,.38);animation:wkfabpulse 2.8s ease-in-out infinite;transition:transform .18s}
.share-fab:hover{transform:translateY(-3px) scale(1.04)}
.share-fab .sf-ic{width:22px;height:22px;display:grid;place-items:center;border-radius:7px;background:rgba(255,255,255,.4);font-size:.95rem;line-height:1}
@keyframes wkfabpulse{0%,100%{box-shadow:0 12px 30px rgba(34,211,238,.38),0 0 0 0 rgba(52,211,153,.5)}50%{box-shadow:0 12px 30px rgba(34,211,238,.38),0 0 0 15px rgba(52,211,153,0)}}
@media (max-width:720px){.share-fab{right:12px;bottom:78px;padding:10px 14px;font-size:.8rem}.btn-share-hot{padding:12px 18px;font-size:.88rem}}
/* monthly business-day bars */
.vz-wrap{margin:20px 0 4px}
.vz-bars{display:flex;align-items:flex-end;gap:6px;height:130px;padding:10px 6px 6px;border-radius:14px;background:linear-gradient(180deg,rgba(52,211,153,.08),rgba(52,211,153,0));border:1px solid var(--line)}
.vz-bars .bz{flex:1;position:relative;height:2px;min-height:2px;border-radius:5px 5px 2px 2px;background:linear-gradient(180deg,#34d399,#0ea5e9);transform-origin:bottom;animation:vzGrow .95s cubic-bezier(.2,.75,.25,1) both}
.vz-bars .bz b{position:absolute;top:-17px;left:0;right:0;text-align:center;font-size:.62rem;color:var(--muted);font-weight:600}
@keyframes vzGrow{from{transform:scaleY(.02)}to{transform:scaleY(1)}}
.vz-x{display:flex;gap:6px;margin-top:6px}
.vz-x span{flex:1;text-align:center;font-size:.6rem;color:var(--muted);text-transform:uppercase;letter-spacing:.03em}
@media (prefers-reduced-motion:reduce){.vz-bars .bz{animation:none}}
/* card sparkline */
.spark{display:flex;align-items:flex-end;gap:2px;height:26px;margin:8px 0 2px}
.spark i{flex:1;min-height:2px;border-radius:2px 2px 1px 1px;background:linear-gradient(180deg,#34d399,#0ea5e9);transform-origin:bottom;animation:sparkGrow .8s cubic-bezier(.2,.75,.25,1) both}
@keyframes sparkGrow{from{transform:scaleY(.05)}to{transform:scaleY(1)}}
.card-note{font-size:.72rem;color:var(--muted);margin:2px 0 6px}
@media (prefers-reduced-motion:reduce){.spark i{animation:none}}
"""


SHARE_JS = r"""
(function(){
  var D=window.WK_SHARE; if(!D) return;
  var TPL={
    aurora:{bg:['#0c211c','#0a1420'],ink:'#eef7f2',sub:'#9fb8ae',accent:'#34d399',cell:'rgba(255,255,255,.06)',line:'rgba(255,255,255,.14)'},
    paper:{bg:['#f8f3e8','#efe5d2'],ink:'#1d1a16',sub:'#6f6557',accent:'#b5731a',cell:'rgba(255,255,255,.55)',line:'rgba(29,26,22,.14)'},
    neon:{bg:['#050809','#0a1411'],ink:'#eafff3',sub:'#7fd6a5',accent:'#7cffb2',cell:'rgba(124,255,178,.08)',line:'rgba(124,255,178,.28)'},
    bloom:{bg:['#ffe9f0','#e8efff'],ink:'#2b2540',sub:'#6b6280',accent:'#7c5cff',cell:'rgba(255,255,255,.62)',line:'rgba(43,37,64,.14)'}
  };
  var SIZES={story:[1080,1350],square:[1080,1080],wide:[1600,900]};
  var st={tpl:'aurora',size:'story',qr:null};
  var canvas=null,modal=null,qrImg=null;
  function px(n){return Math.round(n);}
  function rr(ctx,x,y,w,h,r){var q=Math.min(r,w/2,h/2);ctx.beginPath();ctx.moveTo(x+q,y);ctx.arcTo(x+w,y,x+w,y+h,q);ctx.arcTo(x+w,y+h,x,y+h,q);ctx.arcTo(x,y+h,x,y,q);ctx.arcTo(x,y,x+w,y,q);ctx.closePath();}
  function draw(){
    if(!canvas)return;
    var S=SIZES[st.size],W=S[0],H=S[1];canvas.width=W;canvas.height=H;
    var ctx=canvas.getContext('2d'),t=TPL[st.tpl];
    var g=ctx.createLinearGradient(0,0,W,H);g.addColorStop(0,t.bg[0]);g.addColorStop(1,t.bg[1]);ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
    var P=px(W*0.06);
    ctx.fillStyle=t.ink;ctx.font='700 '+px(W*0.034)+'px Georgia,serif';ctx.fillText('WorkdayKit',P,px(H*0.085));
    ctx.fillStyle=t.sub;ctx.font='400 '+px(W*0.016)+'px system-ui';ctx.fillText('Business days · countdown',P,px(H*0.115));
    ctx.textAlign='right';ctx.fillStyle=t.accent;ctx.font='700 '+px(W*0.05)+'px Georgia,serif';ctx.fillText(String(D.year),W-P,px(H*0.095));ctx.textAlign='left';
    ctx.fillStyle=t.ink;ctx.font='600 '+px(W*0.056)+'px Georgia,"Songti SC","Microsoft YaHei",serif';
    ctx.fillText(D.country+' business days',P,px(H*0.19));
    ctx.fillStyle=t.sub;ctx.font='400 '+px(W*0.022)+'px system-ui';ctx.fillText('Working days left this year',P,px(H*0.222));
    // ring
    var cx=W*0.25,cy=H*0.46,r=px(Math.min(W,H)*0.16);
    ctx.lineWidth=px(W*0.028);ctx.strokeStyle=t.cell;ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.stroke();
    var pct=Math.max(0,Math.min(100,D.pct||0));
    ctx.strokeStyle=t.accent;ctx.beginPath();ctx.arc(cx,cy,r,-Math.PI/2,-Math.PI/2+Math.PI*2*pct/100);ctx.stroke();
    ctx.fillStyle=t.ink;ctx.textAlign='center';ctx.font='700 '+px(W*0.12)+'px Georgia,serif';
    ctx.fillText(String(D.yearLeft),cx,cy+px(W*0.025));
    ctx.fillStyle=t.sub;ctx.font='500 '+px(W*0.014)+'px system-ui';ctx.fillText('business days left',cx,cy+px(W*0.075));
    ctx.textAlign='left';
    // stats
    var sx=W*0.5, sy=H*0.36, gap=H*0.135;
    function stat(label,val,dy){
      ctx.fillStyle=t.sub;ctx.font='600 '+px(W*0.013)+'px system-ui';ctx.fillText(label,sx,sy+dy);
      ctx.fillStyle=t.ink;ctx.font='700 '+px(W*0.05)+'px Georgia,serif';ctx.fillText(val,sx,sy+dy+px(H*0.05));
    }
    stat('business days left this month',String(D.monthLeft),0);
    stat('days until next public holiday',String(D.next),gap);
    stat('business days this year',String(D.total),gap*2);
    // footer
    var fy=px(H*0.84);
    ctx.strokeStyle=t.line;ctx.beginPath();ctx.moveTo(P,fy);ctx.lineTo(W-P,fy);ctx.stroke();
    ctx.fillStyle=t.ink;ctx.font='600 '+px(W*0.017)+'px system-ui';ctx.fillText('WorkdayKit',P,fy+px(H*0.035));
    ctx.fillStyle=t.sub;ctx.font='400 '+px(W*0.0105)+'px system-ui';ctx.fillText(D.url.replace('https://',''),P,fy+px(H*0.058));
    ctx.fillText('Scan to open the live countdown',P,fy+px(H*0.078));
    if(st.qr){var qs=px(Math.min(W*0.105,H*0.105)),qx=W-P-qs,qy=fy+px(H*0.012);
      ctx.fillStyle='#ffffff';rr(ctx,qx-px(W*0.006),qy-px(W*0.006),qs+px(W*0.012),qs+px(W*0.012),px(W*0.008));ctx.fill();
      ctx.drawImage(st.qr,qx,qy,qs,qs);}
  }
  function ensure(){
    if(modal)return modal;
    var wrap=document.createElement('div');wrap.className='share-modal';
    wrap.innerHTML='<div class="share-panel"><div class="share-head"><strong>Share card</strong>'+
      '<button type="button" class="share-close" aria-label="Close">x</button></div>'+
      '<canvas class="share-canvas"></canvas>'+
      '<div class="share-controls"><label>Style<select data-share-tpl>'+Object.keys(TPL).map(function(k){return '<option value="'+k+'">'+k+'</option>';}).join('')+'</select></label>'+
      '<label>Size<select data-share-size><option value="story">Story 4:5</option><option value="square">Square</option><option value="wide">Wide</option></select></label></div>'+
      '<div class="share-btns"><button type="button" class="btn" data-share-dl>Download PNG</button>'+
      '<button type="button" class="btn ghost" data-share-native>Share</button>'+
      '<button type="button" class="btn ghost" data-share-copy>Copy image</button></div>'+
      '<div class="share-platforms" data-share-platforms></div>'+
      '<p class="share-hint">Shortcuts open the platform composer with text + link. For image-only apps (WeChat Moments, Xiaohongshu, Douyin, Instagram) tap "Download PNG" first, then post the image there.</p></div>';
    document.body.appendChild(wrap);modal=wrap;canvas=wrap.querySelector('.share-canvas');
    wrap.querySelector('.share-close').addEventListener('click',function(){wrap.classList.remove('on');});
    wrap.addEventListener('click',function(e){if(e.target===wrap)wrap.classList.remove('on');});
    wrap.querySelector('[data-share-tpl]').addEventListener('change',function(){st.tpl=this.value;draw();});
    wrap.querySelector('[data-share-size]').addEventListener('change',function(){st.size=this.value;draw();});
    wrap.querySelector('[data-share-dl]').addEventListener('click',function(){dl();});
    wrap.querySelector('[data-share-native]').addEventListener('click',function(){nativeShare();});
    wrap.querySelector('[data-share-copy]').addEventListener('click',function(){copy();});
    return wrap;
  }
  function toBlob(cb){canvas.toBlob(function(b){cb(b);},'image/png');}
  var CP={CN:['wechat','weibo','xhs','douyin'],TW:['line','facebook','whatsapp'],HK:['whatsapp','wechat','facebook'],
    JP:['line','x','facebook'],KR:['kakao','facebook','x'],US:['x','facebook','reddit','linkedin'],
    GB:['x','facebook','whatsapp','linkedin'],CA:['x','facebook','whatsapp'],AU:['facebook','x','whatsapp'],
    IN:['whatsapp','x','telegram','linkedin'],SG:['whatsapp','telegram','facebook'],MY:['whatsapp','facebook','telegram'],
    TH:['line','facebook','x'],VN:['facebook','zalo'],ID:['whatsapp','facebook','instagram'],PH:['facebook','whatsapp'],
    DE:['whatsapp','facebook','x'],FR:['whatsapp','facebook','x'],ES:['whatsapp','facebook','x'],IT:['whatsapp','facebook','x'],
    NL:['whatsapp','facebook','x'],PL:['facebook','x','whatsapp'],RU:['vk','telegram','whatsapp'],
    BR:['whatsapp','instagram','facebook'],MX:['whatsapp','facebook','x'],AR:['whatsapp','facebook','x'],
    ZA:['whatsapp','facebook','x'],AE:['whatsapp','telegram','x'],SA:['whatsapp','x','telegram'],
    TR:['whatsapp','x','telegram'],IL:['whatsapp','facebook','telegram'],EG:['whatsapp','facebook','x'],
    NG:['whatsapp','facebook','x'],KE:['whatsapp','facebook','x'],NZ:['facebook','x','whatsapp'],
    SE:['facebook','whatsapp','x'],NO:['facebook','whatsapp'],DK:['facebook','whatsapp'],FI:['whatsapp','facebook','x'],
    CH:['whatsapp','facebook','x'],AT:['whatsapp','facebook','x'],PT:['whatsapp','facebook','x'],GR:['facebook','whatsapp','x']};
  var PN={x:'X',facebook:'Facebook',whatsapp:'WhatsApp',telegram:'Telegram',line:'LINE',weibo:'微博',
    wechat:'微信',xhs:'小红书',douyin:'抖音',kakao:'KakaoTalk',vk:'VK',reddit:'Reddit',linkedin:'LinkedIn',
    instagram:'Instagram',zalo:'Zalo'};
  function platformHref(id,cap,url){
    var u=encodeURIComponent(url), t=encodeURIComponent(cap);
    if(id==='x')return 'https://twitter.com/intent/tweet?text='+t+'&url='+u;
    if(id==='facebook')return 'https://www.facebook.com/sharer/sharer.php?u='+u;
    if(id==='linkedin')return 'https://www.linkedin.com/sharing/share-offsite/?url='+u;
    if(id==='reddit')return 'https://www.reddit.com/submit?url='+u+'&title='+t;
    if(id==='whatsapp')return 'https://wa.me/?text='+encodeURIComponent(cap+' '+url);
    if(id==='telegram')return 'https://t.me/share/url?url='+u+'&text='+t;
    if(id==='line')return 'https://social-plugins.line.me/lineit/share?url='+u;
    if(id==='weibo')return 'https://service.weibo.com/share/share.php?url='+u+'&title='+t;
    if(id==='kakao')return 'https://story.kakao.com/share?url='+u;
    if(id==='vk')return 'https://vk.com/share.php?url='+u;
    if(id==='zalo')return 'https://zalo.me/share?u='+u;
    return '';
  }
  function caption(){ return 'WorkdayKit · '+D.country+' — '+D.yearLeft+' business days left in '+D.year+' · '+D.url; }
  function renderPlatforms(){
    if(!modal)return;
    var box=modal.querySelector('[data-share-platforms]'); if(!box)return;
    var cc=(window.WK_COUNTRY||'').toUpperCase();
    var ids=CP[cc]||['x','facebook','whatsapp','telegram','linkedin'];
    box.innerHTML='';
    ids.forEach(function(id){
      var b=document.createElement('button'); b.type='button'; b.className='share-plat'; b.textContent=PN[id]||id;
      b.addEventListener('click',function(){
        var h=platformHref(id,caption(),D.url);
        if(h){ window.open(h,'_blank','noopener'); }
        else { try{navigator.clipboard.writeText(caption());}catch(e){} dl(); alert(PN[id]+' 不支持网页直接带图发布：图片已下载、文案已复制，请打开 App 发布。'); }
      });
      box.appendChild(b);
    });
  }
  function detectCountry(){
    if(window.WK_COUNTRY)return;
    fetch('/geo').then(function(r){return r.ok?r.json():null;}).then(function(d){
      window.WK_COUNTRY=((d&&d.country)||'').toUpperCase(); renderPlatforms();
    }).catch(function(){ renderPlatforms(); });
  }
  function dl(){toBlob(function(b){var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='workdaykit-'+D.year+'.png';document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},800);});}
  function nativeShare(){toBlob(function(b){var f=new File([b],'workdaykit.png',{type:'image/png'});if(navigator.canShare&&navigator.canShare({files:[f]})){navigator.share({files:[f],title:'WorkdayKit',text:D.country+' — '+D.yearLeft+' business days left'}).catch(function(){});}else{dl();}});}
  function copy(){toBlob(function(b){if(navigator.clipboard&&window.ClipboardItem){navigator.clipboard.write([new ClipboardItem({'image/png':b})]).then(function(){alert('Copied image / 图片已复制');},function(){dl();});}else{dl();}});}
  function open(){ensure().classList.add('on');draw();detectCountry();renderPlatforms();}
  qrImg=new Image();qrImg.onload=function(){st.qr=qrImg;if(modal)draw();};qrImg.src=D.qr;
  document.querySelectorAll('[data-share-open]').forEach(function(b){b.addEventListener('click',function(e){e.preventDefault();open();});});
  // floating, always-visible share CTA
  (function(){
    if(document.querySelector('.share-fab')) return;
    var lang=(document.documentElement.lang||'en').slice(0,2);
    var TXT={zh:'分享卡片',ja:'共有カード',ko:'공유 카드',es:'Compartir',fr:'Partager',de:'Teilen'};
    var fab=document.createElement('button');
    fab.type='button'; fab.className='share-fab'; fab.setAttribute('aria-label','Share card');
    fab.innerHTML='<span class="sf-ic" aria-hidden="true">✨</span><span class="sf-txt">'+(TXT[lang]||'Share card')+'</span>';
    fab.addEventListener('click', function(){ open(); });
    document.body.appendChild(fab);
  })();
  window.WK_SHARE_REFRESH=function(){if(modal&&modal.classList.contains('on'))draw();};
  if(new URLSearchParams(location.search).has('share')){window.addEventListener('load',open);}
})();
"""


def page(title: str, desc: str, canonical: str, body: str, base: str = "", extra: str = "") -> str:
    nav = (
        '<header class="site-head"><div class="wrap head-inner">'
        f'<a class="brand" href="{base}index.html"><span class="brand-mark">◷</span>{SITE_NAME}</a>'
        f'<nav><a href="{base}index.html" data-i18n="nav.calc">Calculator</a>'
        f'<a href="{base}countdown/index.html" data-i18n="nav.cd">Countdown</a>'
        f'<a href="{base}index.html#countries" data-i18n="nav.countries">Countries</a>'
        f'<a href="{base}api/index.html" data-i18n="nav.api">API</a>'
        f'<a href="{base}about/index.html" data-i18n="nav.about">About</a></nav>'
        '<select class="lang-select" data-hk-lang aria-label="Language">'
        '<option value="en">EN</option><option value="zh">中文</option><option value="ja">日本語</option>'
        '<option value="ko">한국어</option><option value="es">ES</option><option value="fr">FR</option>'
        '<option value="de">DE</option></select>'
        "</div></header>"
    )
    foot = (
        '<footer class="site-foot"><div class="wrap">'
        f'<p><strong>{SITE_NAME}</strong> — <span data-i18n="foot.note">Count business days between dates, skip weekends and holidays.</span></p>'
        '<p>Data: open holiday datasets (Nager.Date, OpenHolidays, python-holidays, chinese-days). '
        "For planning only — confirm critical dates with official sources.</p>"
        f'<p><a href="{base}privacy/index.html">Privacy</a> · '
        f'<a href="{base}about/index.html">About</a> · '
        f'<a href="{base}index.html">Calculator</a> · '
        f'<a href="{base}support/index.html">♥ Support · 打赏</a> · '
        '<a href="https://holidaykit.pages.dev">Holiday calendars &amp; long weekends</a></p>'
        "</div></footer>"
    )
    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{title}</title>"
        f'<meta name="description" content="{desc}">'
        f'<link rel="canonical" href="{canonical}">'
        '<meta name="robots" content="index,follow">'
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">'
        f"<style>{CSS}{SHARE_CSS}</style></head><body>{nav}"
        f'<main class="wrap">{body}</main>{foot}'
        f"<script>{MOTION_JS}</script><script>{I18N_JS}</script>{extra}</body></html>"
    )


FAVICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" rx="14" fill="#15161a"/>'
    '<path d="M20 26h24M20 36h14M20 46h9" stroke="#fbfaf7" stroke-width="3.4" stroke-linecap="round"/>'
    '<circle cx="45" cy="44" r="6" fill="#0f6b5c"/></svg>'
)


def page_support(site_url: str) -> str:
    def media(img: str, alt: str) -> str:
        path = ROOT / "assets" / "support" / f"{img}.png"
        if path.exists():
            return f'<img class="sup-qr" src="../assets/support/{img}.png" alt="{alt}" loading="lazy">'
        return f'<div class="sup-ph" aria-hidden="true">QR<br><code>assets/support/{img}.png</code></div>'

    cards = "".join([
        '<div class="sup-card">' + media("wechat", "WeChat tip QR code") +
        '<h3>微信赞赏</h3><p>扫码随意打赏，金额随意。</p></div>',
        '<div class="sup-card">' + media("alipay", "Alipay tip QR code") +
        '<h3>支付宝</h3><p>扫码打赏，支持项目持续更新。</p></div>',
        '<div class="sup-card"><div class="sup-ico">☕</div><h3>Buy me a coffee</h3>'
        '<p>International cards / PayPal.</p>'
        '<a class="btn" href="https://buymeacoffee.com/" target="_blank" rel="noopener">Open</a></div>',
        '<div class="sup-card"><div class="sup-ico">★</div><h3>GitHub Sponsors</h3>'
        '<p>Monthly or one-time sponsorship.</p>'
        '<a class="btn" href="https://github.com/sponsors/ChaoyuZhang1" target="_blank" '
        'rel="noopener">Sponsor</a></div>',
    ])
    body = (
        '<style>'
        '.sup-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:22px 0}'
        '@media(max-width:820px){.sup-grid{grid-template-columns:repeat(2,1fr)}}'
        '@media(max-width:460px){.sup-grid{grid-template-columns:1fr}}'
        '.sup-card{background:#fff;border:1px solid #e7e3da;border-radius:16px;padding:18px;text-align:center}'
        '.sup-qr{width:100%;max-width:180px;border-radius:12px;display:block;margin:0 auto 12px}'
        '.sup-ph{height:150px;border:2px dashed #d9d3c7;border-radius:12px;display:flex;flex-direction:column;'
        'align-items:center;justify-content:center;gap:6px;color:#8a8274;font-size:.78rem;margin-bottom:12px}'
        '.sup-ph code{font-size:.7rem;word-break:break-all}'
        '.sup-ico{font-size:2.2rem;line-height:1;margin:26px 0 14px}'
        '.sup-card h3{margin:0 0 6px;font-size:1.02rem}.sup-card p{color:#6b6558;font-size:.86rem;margin:0 0 12px}'
        '</style>'
        '<section class="hero"><p class="eyebrow">SUPPORT · 打赏支持</p>'
        '<h1>Keep WorkdayKit free</h1>'
        '<p class="lede">If WorkdayKit saved you time, you can buy me a coffee. Tips are optional — the '
        'calculator, countdown and API stay free for everyone.</p></section>'
        '<section class="sec"><h2>打赏方式</h2><div class="sup-grid">' + cards + '</div>'
        '<p class="muted">打赏完全自愿，不换取任何功能、数据或优先级。</p></section>'
        '<section class="sec"><h2>打赏用在哪里</h2><ul>'
        '<li>维护 95 个国家的假期与调休数据</li>'
        '<li>域名、CDN 与构建基础设施费用</li>'
        '<li>继续完善工作日 API 与倒计时页面</li></ul></section>'
        '<section class="sec"><h2>Commercial API use</h2>'
        '<p>The JSON API is free under a generous fair-use policy. For commercial use or a higher-volume '
        'guarantee, a sponsor licence is available — tip above and get in touch.</p></section>'
    )
    return page("Support WorkdayKit · 打赏支持",
                "Support WorkdayKit with a tip — WeChat, Alipay, Buy Me a Coffee or GitHub Sponsors.",
                f"{site_url}/support/", body, base="../")


def calc_widget(default_cc: str, countries: list[dict], preview: str = "") -> str:
    options = "".join(
        f'<option value="{c["code"]}"{" selected" if c["code"] == default_cc else ""}>{c["name"]}</option>'
        for c in countries
    )
    _t = date.today()
    _e = _t + timedelta(days=30)
    sel_year = _t.year if _t.year in YEARS else max(YEARS)
    years = "".join(f'<option value="{y}"{" selected" if y == sel_year else ""}>{y}</option>' for y in YEARS)
    return (
        '<div class="calc" data-calc-root>'
        '<div class="calc-tabs">'
        '<button type="button" data-mode="between" class="on" data-i18n="calc.tab1">Days between dates</button>'
        '<button type="button" data-mode="add" data-i18n="calc.tab2">Add / subtract business days</button>'
        "</div>"
        '<div class="calc-row">'
        f'<label><span data-i18n="calc.country">Country</span><select data-country>{options}</select></label>'
        f'<label><span data-i18n="calc.year">Year</span><select data-year>{years}</select></label>'
        "</div>"
        '<div class="calc-row" data-panel="between">'
        f'<label><span data-i18n="calc.start">Start date</span><input type="date" data-start value="{_t.isoformat()}"></label>'
        f'<label><span data-i18n="calc.end">End date</span><input type="date" data-end value="{_e.isoformat()}"></label>'
        "</div>"
        '<div class="calc-row" data-panel="add" hidden>'
        f'<label><span data-i18n="calc.start">Start date</span><input type="date" data-add-start value="{_t.isoformat()}"></label>'
        '<label><span data-i18n="calc.addn">Business days (negative to subtract)</span><input type="number" value="10" min="-365" max="365" data-add-n></label>'
        "</div>"
        '<button type="button" class="btn" data-calc data-i18n="calc.calc">Calculate</button>'
        f'<div class="calc-result" data-result>{preview}</div>'
        "</div>"
    )


CALC_JS = """
(function(){
  var root = document.querySelector('[data-calc-root]');
  if (!root || !window.WK) return;
  var countries = window.WK.countries || [];
  var mode = 'between';
  var cache = {};
  function $(sel){ return root.querySelector(sel); }
  function pad(n){ return (n<10?'0':'')+n; }
  function iso(d){ return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate()); }
  function parse(v){ return v ? new Date(v+'T00:00:00') : null; }
  function fmt(d){ return d ? d.toLocaleDateString(undefined,{year:'numeric',month:'short',day:'numeric'}) : '—'; }
  function dataFor(cc, year, cb){
    var key = cc + '-' + year;
    if (cache[key]) return cb(cache[key]);
    fetch('/api/v1/business/' + cc + '/' + year + '.json')
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(d){ cache[key] = d || {holidays:[],makeup:[]}; cb(cache[key]); })
      .catch(function(){ cb({holidays:[],makeup:[]}); });
  }
  function holidaySet(d){
    var set = {};
    (d.holidays||[]).forEach(function(x){ set[x]=1; });
    (d.makeup||[]).forEach(function(x){ set[x]=1; });
    return set;
  }
  function countBetween(start, end, data){
    var hol = holidaySet(data);
    var total = 0, weekend = 0, holidays = 0, d = new Date(start);
    while (d <= end) {
      var key = iso(d);
      var isWeekend = d.getDay()===0 || d.getDay()===6;
      if (hol[key]) { total++; if (!isWeekend) holidays++; }
      else if (isWeekend) weekend++;
      d.setDate(d.getDate()+1);
    }
    var allDays = Math.round((end-start)/86400000)+1;
    var biz = allDays - weekend - holidays;
    return { business: biz, total: allDays, weekend: weekend, holidays: holidays };
  }
  function addBusiness(start, n, data){
    var hol = holidaySet(data);
    var dir = n >= 0 ? 1 : -1;
    var left = Math.abs(n);
    var d = new Date(start);
    var skipped = [];
    while (left > 0) {
      d.setDate(d.getDate() + dir);
      var key = iso(d);
      var isWeekend = d.getDay()===0 || d.getDay()===6;
      if (isWeekend && !hol[key]) continue;
      if (hol[key] && !isWeekend) { skipped.push(key); continue; }
      left--;
    }
    return { date: d, skipped: skipped };
  }
  function render(html){ $('[data-result]').innerHTML = html; }
  function icsFor(dateStr, title){
    var d = new Date(dateStr + 'T00:00:00');
    var next = new Date(d.getTime() + 86400000);
    function p2(n){ return (n < 10 ? '0' : '') + n; }
    function ymd(x){ return x.getFullYear() + p2(x.getMonth() + 1) + p2(x.getDate()); }
    return ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//WorkdayKit//EN', 'CALSCALE:GREGORIAN',
      'BEGIN:VEVENT', 'UID:' + ymd(d) + '-' + Math.random().toString(36).slice(2) + '@workdaykit',
      'DTSTAMP:' + ymd(d) + 'T000000Z', 'DTSTART;VALUE=DATE:' + ymd(d), 'DTEND;VALUE=DATE:' + ymd(next),
      'SUMMARY:' + (title || 'Business day'), 'TRANSP:TRANSPARENT', 'END:VEVENT', 'END:VCALENDAR'
    ].join('\r\n');
  }
  function downloadIcs(dateStr, title){
    var blob = new Blob([icsFor(dateStr, title)], { type: 'text/calendar;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'workdaykit-' + dateStr + '.ics';
    document.body.appendChild(a); a.click();
    setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); }, 600);
  }
  function setMode(m){
    mode = m;
    root.querySelectorAll('[data-mode]').forEach(function(b){ b.classList.toggle('on', b.getAttribute('data-mode')===m); });
    root.querySelector('[data-panel="between"]').hidden = m !== 'between';
    root.querySelector('[data-panel="add"]').hidden = m !== 'add';
  }
  root.querySelectorAll('[data-mode]').forEach(function(b){
    b.addEventListener('click', function(){ setMode(b.getAttribute('data-mode')); });
  });
  $('[data-calc]').addEventListener('click', function(){
    var cc = $('[data-country]').value;
    var year = parseInt($('[data-year]').value, 10);
    dataFor(cc, year, function(data){
      if (mode === 'between') {
        var s = parse($('[data-start]').value), e = parse($('[data-end]').value);
        if (!s || !e) { render('<div class="callout">Pick both dates first.</div>'); return; }
        if (s > e) { var t = s; s = e; e = t; }
        var r = countBetween(s, e, data);
        render('<div class="result-card"><div class="result-num">' + r.business + '<span>business days</span></div>' +
          '<div class="result-detail">' + fmt(s) + ' → ' + fmt(e) + ' · ' + r.total + ' calendar days · ' +
          r.weekend + ' weekend days · ' + r.holidays + ' public holidays</div>' +
          '<div class="result-actions"><button type="button" class="btn ghost" data-ics="' + iso(e) +
          '" data-ics-title="Deadline (' + r.business + ' business days)">Add deadline to calendar</button></div></div>');
      } else {
        var st = parse($('[data-add-start]').value);
        var n = parseInt($('[data-add-n]').value, 10);
        if (!st || isNaN(n)) { render('<div class="callout">Pick a start date and a number of days.</div>'); return; }
        var res = addBusiness(st, n, data);
        render('<div class="result-card"><div class="result-num">' + fmt(res.date) + '</div>' +
          '<div class="result-detail">' + (n >= 0 ? '+' : '') + n + ' business days from ' + fmt(st) +
          (res.skipped.length ? ' · skipped ' + res.skipped.length + ' holiday(s)' : '') + '</div>' +
          '<div class="result-actions"><button type="button" class="btn ghost" data-ics="' +
          iso(res.date) + '" data-ics-title="' + n + ' business days from ' + fmt(st).replace(/"/g, '') +
          '">Add result to calendar</button></div></div>');
      }
    });
  });
  root.addEventListener('click', function(e){
    var btn = e.target && e.target.closest ? e.target.closest('[data-ics]') : null;
    if (!btn) return;
    downloadIcs(btn.getAttribute('data-ics'), btn.getAttribute('data-ics-title') || 'Business day');
  });
  // sensible defaults: today → +30 days, current year, first result visible immediately
  (function(){
    var t = new Date(); t.setHours(0, 0, 0, 0);
    var e = new Date(t); e.setDate(e.getDate() + 30);
    var sEl = root.querySelector('[data-start]'), eEl = root.querySelector('[data-end]'),
        aEl = root.querySelector('[data-add-start]'), yEl = root.querySelector('[data-year]');
    if (sEl && !sEl.value) sEl.value = iso(t);
    if (eEl && !eEl.value) eEl.value = iso(e);
    if (aEl && !aEl.value) aEl.value = iso(t);
    if (yEl) { var y = String(t.getFullYear());
      for (var i = 0; i < yEl.options.length; i++) { if (yEl.options[i].value === y) { yEl.selectedIndex = i; break; } } }
  })();
  setMode('between');
  // geo-detect the country so visitors outside the US see their own numbers
  fetch('/geo').then(function(r){ return r.ok ? r.json() : null; }).then(function(g){
    if (!g || !g.country) return;
    var sel = root.querySelector('[data-country]');
    if (!sel) return;
    for (var i = 0; i < sel.options.length; i++) {
      if (sel.options[i].value === g.country) {
        if (sel.selectedIndex !== i) { sel.selectedIndex = i; }
        var b0 = root.querySelector('[data-calc]');
        if (b0) b0.click();
        return;
      }
    }
  }).catch(function(){});
  var recalc = function(){ var b = root.querySelector('[data-calc]'); if (b) b.click(); };
  var cSel = root.querySelector('[data-country]'), ySel = root.querySelector('[data-year]');
  if (cSel) cSel.addEventListener('change', recalc);
  if (ySel) ySel.addEventListener('change', recalc);
})();
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-url", default="https://workdaykit.pages.dev")
    args = parser.parse_args()
    site_url = args.site_url.rstrip("/")

    rows = json.loads((HK / "data" / "holidays.json").read_text(encoding="utf-8"))["holidays"]
    cn = json.loads((HK / "data" / "cn_calendar.json").read_text(encoding="utf-8")).get("years", {})

    public: dict[tuple, set] = {}
    for row in rows:
        if not (set(row.get("types") or []) & {"Public", "Bank"}):
            continue
        try:
            d = date.fromisoformat(row["date"])
        except (KeyError, ValueError):
            continue
        public.setdefault((row["country"], d.year), set()).add(d)
    makeup: dict[tuple, set] = {}
    for y, data in cn.items():
        for item in data.get("work") or []:
            try:
                d = date.fromisoformat(item["date"])
            except (KeyError, ValueError):
                continue
            makeup.setdefault(("CN", d.year), set()).add(d)

    def business_total(cc: str, year: int) -> tuple[int, list[int]]:
        hol = public.get((cc, year), set())
        mk = makeup.get((cc, year), set())
        monthly = [0] * 13
        d = date(year, 1, 1)
        end = date(year, 12, 31)
        while d <= end:
            weekend = d.weekday() >= 5
            is_biz = (not weekend and d not in hol) or (d in mk)
            if is_biz:
                monthly[d.month] += 1
            d += timedelta(days=1)
        return sum(monthly), monthly

    def static_preview(cc: str, days: int = 30) -> str:
        """Server-rendered first result so numbers are visible before any click."""
        t = date.today()
        e = t + timedelta(days=days)
        n = 0
        d = t
        while d <= e:
            weekend = d.weekday() >= 5
            hol = public.get((cc, d.year), set())
            mk = makeup.get((cc, d.year), set())
            if (mk and d in mk) or (not weekend and d not in hol):
                n += 1
            d += timedelta(days=1)
        return (
            f'<div class="result-card"><div class="result-num">{n}<span>business days</span></div>'
            f'<div class="result-detail">{t.isoformat()} → {e.isoformat()} · {days} calendar days</div></div>'
        )

    countries = []
    for cc in sorted({r["country"] for r in rows}):
        name = COUNTRY_NAMES.get(cc, cc)
        countries.append({"code": cc, "name": name, "slug": slugify(name)})

    out = ROOT / "dist"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    qr_dir = out / "assets" / "qr"
    qr_dir.mkdir(parents=True, exist_ok=True)
    if qrcode is not None:
        try:
            qrcode.make(f"{site_url}/countdown/", box_size=4, border=1).save(qr_dir / "countdown.png")
        except Exception:  # noqa: BLE001
            pass
    urls: list[str] = []

    wk_js = (
        "<script>window.WK=" + json.dumps({"countries": countries, "years": YEARS}) + ";</script>"
        f"<script>{CALC_JS}</script>"
    )

    # homepage
    current_year = date.today().year if date.today().year in YEARS else max(YEARS)
    cards = []
    for c in countries:
        total, monthly = business_total(c["code"], current_year)
        if total <= 0:
            continue
        _mm = monthly[1:] if len(monthly) > 12 else monthly
        _mx = max(_mm) or 1
        spark = "".join(f'<i style="height:{max(6, v / _mx * 100):.0f}%"></i>' for v in _mm)
        cards.append(
            f'<a class="card" href="{c["slug"]}/index.html"><div class="flag">{flag_emoji(c["code"])}</div>'
            f'<h3>{c["name"]}</h3><p>{total} business days in {current_year}</p>'
            f'<span class="spark" aria-hidden="true">{spark}</span>'
            f'<p class="card-note">{min(_mm)}–{max(_mm)} working days per month</p></a>'
        )
    faq = [
        ("What counts as a business day?",
         "Monday to Friday that is not a public holiday in the selected country. China's 调休/补班 workdays are counted as business days."),
        ("Does the calculator include regional holidays?",
         "It uses national public holidays; regional differences may apply in some countries."),
        ("Can I subtract business days?",
         "Yes — switch to 'Add / subtract business days' and enter a negative number."),
    ]
    faq_html = "".join(f"<dt>{q}</dt><dd>{a}</dd>" for q, a in faq)
    body = (
        '<section class="hero">'
        '<p class="eyebrow" data-i18n="hero.eyebrow">Business days · weekends · public holidays</p>'
        '<h1 data-i18n="hero.h1">Business days calculator</h1>'
        '<p class="lede" data-i18n="hero.lede">Count working days between two dates, or add business days to a date — for 95 countries, skipping weekends and public holidays (including China\'s 调休/补班 rules).</p>'
        '</section>'
        + calc_widget("US", countries, static_preview("US"))
        + '<section class="sec"><h2 data-i18n="home.countries">Business days by country</h2>'
        '<p class="sub" data-i18n="home.countries.sub">How many business days are left this year, country by country.</p>'
        '<div class="grid">' + "".join(cards) + "</div></section>"
        '<span hidden></span>'
        '<section class="sec"><h2 data-i18n="home.how">How it works</h2>'
        "<p>Pick a country and year, then either count the business days between two dates or add/subtract a number "
        "of business days. The calculator loads that country's public holidays and excludes them. Weekends are "
        "skipped automatically; China's make-up workdays (补班) are counted as working days.</p>"
        '<div class="callout">Tip: use it for delivery estimates, SLA deadlines, payroll periods, visa timelines and project planning.</div>'
        "</section>"
        '<section class="sec"><h2 data-i18n="home.countdown">Business days left this year</h2>'
        '<p class="sub" data-i18n="home.countdown.sub">A live countdown of how many working days remain — auto-detected for your country.</p>'
        '<p><a class="btn" href="countdown/index.html">Open the live countdown</a></p></section>'
        '<section class="sec"><h2 data-i18n="home.faq">FAQ</h2><dl class="faq">' + faq_html + "</dl></section>"
    )
    (out / "index.html").write_text(
        page("Business Days Calculator — Count Working Days (95 countries)", 
             "Free business days calculator: count working days between dates or add business days, excluding weekends and public holidays.",
             site_url + "/", body, extra=wk_js),
        encoding="utf-8",
    )
    urls.append("")

    # country + year pages + API
    for c in countries:
        cc, name, slug = c["code"], c["name"], c["slug"]
        cdir = out / slug
        cdir.mkdir(parents=True, exist_ok=True)
        cw = calc_widget(cc, countries, static_preview(cc))
        year_rows = []
        for year in YEARS:
            total, monthly = business_total(cc, year)
            if total <= 0:
                continue
            year_rows.append(
                f'<tr><td><a href="{year}/index.html">{year}</a></td><td>{total}</td>'
                f"<td>{sum(1 for m in monthly[1:] if m)}</td></tr>"
            )
        (cdir / "index.html").write_text(
            page(f"{name} Business Days {current_year}", f"Business days in {name}: count working days by year, with public holidays.",
                 f"{site_url}/{slug}/",
                 f'<section class="hero"><p class="eyebrow">{cc} · business days</p>'
                 f'<h1><span class="flag">{flag_emoji(cc)}</span> {name} business days</h1>'
                 f'<p class="lede">Working days in {name} by year, excluding weekends and public holidays.</p></section>'
                 + cw
                 + '<section class="sec"><h2>Business days by year</h2>'
                 '<div class="tbl-wrap"><table><thead><tr><th>Year</th><th>Business days</th><th>Months with holidays</th>'
                 "</tr></thead><tbody>" + "".join(year_rows) + "</tbody></table></div></section>"
                 + '<p><a href="../index.html">← All countries</a></p>',
                 base="../../"),
            encoding="utf-8",
        )
        urls.append(f"{slug}/")
        for year in YEARS:
            total, monthly = business_total(cc, year)
            if total <= 0:
                continue
            ydir = cdir / str(year)
            ydir.mkdir(parents=True, exist_ok=True)
            hol_rows = []
            for d in sorted(public.get((cc, year), set())):
                hol_rows.append(
                    f"<tr><td>{d.strftime('%d %b %Y')}</td><td>{d.strftime('%A')}</td></tr>"
                )
            (ydir / "index.html").write_text(
                page(f"{name} Business Days {year}",
                     f"How many business days in {name} in {year}: {total} working days after excluding weekends and public holidays.",
                     f"{site_url}/{slug}/{year}/",
                     f'<section class="hero"><p class="eyebrow">{cc} · {year}</p>'
                     f'<h1><span class="flag">{flag_emoji(cc)}</span> {name} business days in {year}</h1>'
                     f'<p class="lede"><strong>{total} business days</strong> in {year} (weekends and public holidays excluded).</p>'
                     f'<div class="chips"><span class="chip">{total} business days</span>'
                     f'<span class="chip">{len(public.get((cc, year), set()))} public holidays</span></div></section>'
                     + cw
                     + '<section class="sec"><h2>Business days by month</h2>'
                     '<div class="tbl-wrap"><table><thead><tr><th>Month</th><th>Business days</th></tr></thead><tbody>'
                     + "".join(f"<tr><td>{MONTHS[i-1]}</td><td>{monthly[i]}</td></tr>" for i in range(1, 13))
                     + "</tbody></table></div></section>"
                     '<section class="sec"><h2>Public holidays in ' + str(year) + "</h2>"
                     '<div class="tbl-wrap"><table><thead><tr><th>Date</th><th>Day</th></tr></thead><tbody>'
                     + "".join(hol_rows) + "</tbody></table></div></section>"
                     + f'<p><a href="../index.html">← {name} overview</a> · <a href="../../index.html">Calculator</a></p>',
                     base="../../../"),
                encoding="utf-8",
            )
            urls.append(f"{slug}/{year}/")
            api_dir = out / "api" / "v1" / "business" / cc
            api_dir.mkdir(parents=True, exist_ok=True)
            (api_dir / f"{year}.json").write_text(
                json.dumps({
                    "country": cc,
                    "name": name,
                    "year": year,
                    "businessDays": total,
                    "monthly": {MONTHS[i-1]: monthly[i] for i in range(1, 13)},
                    "holidays": [d.isoformat() for d in sorted(public.get((cc, year), set()))],
                    "makeup": [d.isoformat() for d in sorted(makeup.get((cc, year), set()))],
                }, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    # countdown page (auto-located remaining business days)
    def biz_between(cc: str, start: date, end: date) -> int:
        n = 0
        d = start
        while d <= end:
            wk = d.weekday() >= 5
            h = public.get((cc, d.year), set())
            m = makeup.get((cc, d.year), set())
            if (m and d in m) or (not wk and d not in h):
                n += 1
            d += timedelta(days=1)
        return n

    today_d = date.today()
    data_years = sorted({y for (_c, y) in public.keys()})
    static_year = today_d.year if today_d.year in data_years else (data_years[-1] if data_years else today_d.year)
    static_cc = "US" if "US" in {c["code"] for c in countries} else countries[0]["code"]
    if static_year != today_d.year:
        static_start = date(static_year, 1, 1)
        static_end = date(static_year, 12, 31)
    else:
        static_start = today_d
        static_end = date(static_year, 12, 31)
    static_total = biz_between(static_cc, date(static_year, 1, 1), date(static_year, 12, 31))
    static_left = biz_between(static_cc, static_start, static_end)
    static_month_left = biz_between(static_cc, today_d, date(today_d.year, today_d.month + 1, 1) - timedelta(days=1)) if today_d.month < 12 else biz_between(static_cc, today_d, date(today_d.year, 12, 31))
    static_done = static_total - static_left
    static_pct = round(static_done / static_total * 100) if static_total else 0
    next_hol = None
    for d in sorted(public.get((static_cc, static_year), set())):
        if d >= today_d:
            next_hol = d
            break
    next_days = (next_hol - today_d).days if next_hol else None

    static_monthly = []
    for _m in range(1, 13):
        _ms = date(static_year, _m, 1)
        _me = (date(static_year + 1, 1, 1) if _m == 12 else date(static_year, _m + 1, 1)) - timedelta(days=1)
        static_monthly.append(biz_between(static_cc, _ms, _me))
    _lo, _hi = min(static_monthly), max(static_monthly)
    _rng = max(_hi - _lo, 1)
    cd_bars = "".join(
        f'<div class="bz" data-m="{_i}" style="height:{round(20 + (v - _lo) / _rng * 66)}%">'
        f"<b>{v}</b></div>"
        for _i, v in enumerate(static_monthly)
    )
    cd_bar_labels = '<div class="vz-x">' + "".join(f"<span>{m}</span>" for m in MONTHS) + "</div>"

    country_options = "".join(
        f'<option value="{c["code"]}"{" selected" if c["code"] == static_cc else ""}>{c["name"]}</option>'
        for c in countries
    )
    cd_body = (
        '<section class="cd-hero" id="hk-countdown" data-country="' + static_cc + '">'
        '<p class="eyebrow" data-i18n="cd.eyebrow">Live business-day countdown</p>'
        f'<h1><span data-i18n="home.countdown">Business days left this year</span> <span id="cd-year-label">{static_year}</span></h1>'
        '<div class="cd-wrap">'
        '<div class="cd-ring" data-cd-ring style="--p:' + str(static_pct) + '">'
        '<div class="cd-ring-mid"><div class="cd-big" id="cd-year">' + str(static_left) + '</div>'
        '<span data-i18n="cd.left">business days left</span></div></div>'
        '<div class="cd-tiles">'
        '<div class="cd-tile"><span class="cd-ico" aria-hidden="true">📅</span>'
        '<div class="v" id="cd-month">' + str(static_month_left) + '</div>'
        '<div class="k" data-i18n="cd.month">business days left this month</div></div>'
        '<div class="cd-tile"><span class="cd-ico" aria-hidden="true">🎯</span>'
        '<div class="v" id="cd-next">' + (str(next_days) if next_days is not None else "—") + '</div>'
        '<div class="k" data-i18n="cd.next">days until next public holiday</div></div>'
        '<div class="cd-tile"><span class="cd-ico" aria-hidden="true">🗓️</span>'
        '<div class="v" id="cd-total">' + str(static_total) + '</div>'
        '<div class="k" data-i18n="cd.total">business days this year</div></div>'
        '<div class="cd-tile"><span class="cd-ico" aria-hidden="true">⏱️</span>'
        '<div class="v"><span class="dot-live"></span><span id="cd-clock">--:--:--</span></div>'
        '<div class="k" data-i18n="cd.clock">your local time</div></div>'
        "</div></div>"
        '<div class="cd-country"><label>Country <select data-cd-country>' + country_options + "</select></label>"
        '<span><strong id="cd-pct">' + str(static_pct) + '%</strong> <span data-i18n="cd.pct">of the year\'s business days done</span></span></div>'
        '<div class="vz-wrap"><h3>📊 Business days by month</h3>'
        '<div class="vz-bars" id="cd-bars">' + cd_bars + "</div>" + cd_bar_labels + "</div>"
        '<p class="cd-note" data-i18n="cd.lede">Auto-detected from your location — change the country above to '
        "recalculate. Counts working days only: weekends and public holidays are excluded (China's 补班 counted "
        "as working days).</p>"
        '<p style="margin-top:18px"><button type="button" class="btn-share-hot" data-share-open>'
        '<span aria-hidden="true">✨</span> 生成分享卡片 · Share card</button></p>'
        "</section>"
        '<section class="sec"><h2 data-i18n="cd.what">What this counts</h2>'
        "<p>Remaining business days = weekdays left in the year minus public holidays, plus China's make-up "
        "workdays (补班). The ring shows how much of the year's working time has already passed.</p>"
        '<div class="callout">Use it for sprint planning, payroll cut-offs, SLA deadlines and year-end delivery '
        "estimates.</div></section>"
        '<section class="sec"><h2>FAQ</h2><dl class="faq">'
        "<dt>Why does the number change when I switch country?</dt><dd>Each country has a different set of public "
        "holidays, so its remaining business days differ.</dd>"
        "<dt>How is my location detected?</dt><dd>Cloudflare's edge geolocation tells us your country; if the "
        "country is unsupported we fall back to your timezone or browser language.</dd>"
        "<dt>Does it update automatically?</dt><dd>Yes — the countdown recalculates on load and the clock ticks "
        "every second.</dd></dl></section>"
    )
    (out / "countdown").mkdir(exist_ok=True)
    wkdata = "<script>window.WK=" + json.dumps({"countries": countries, "years": YEARS}) + ";</script>"
    static_name = next((c["name"] for c in countries if c["code"] == static_cc), static_cc)
    wshare = {
        "country": static_name,
        "year": static_year,
        "yearLeft": static_left,
        "monthLeft": static_month_left,
        "next": next_days if next_days is not None else "—",
        "total": static_total,
        "pct": static_pct,
        "url": f"{site_url}/countdown/",
        "qr": "/assets/qr/countdown.png",
    }
    (out / "countdown" / "index.html").write_text(
        page("Business Days Left in " + str(static_year) + " — Live Countdown",
             "Live countdown of remaining business days in the year, auto-detected for your country. Weekends and public holidays excluded.",
             f"{site_url}/countdown/", cd_body, base="../",
             extra=wkdata
             + "<script>" + COUNTDOWN_JS + "</script>"
             + "<script>window.WK_SHARE=" + json.dumps(wshare, ensure_ascii=False) + ";</script>"
             + "<script>" + SHARE_JS + "</script>"),
        encoding="utf-8",
    )
    urls.append("countdown/")

    # API docs / about / privacy
    api_body = (
        '<section class="hero"><p class="eyebrow">API</p><h1>Free business-day API</h1>'
        '<p class="lede">Static JSON for every supported country and year.</p></section>'
        '<section class="sec"><h2>Endpoints</h2>'
        f'<div class="card"><code>GET {site_url}/api/v1/business/{{CC}}/{{YYYY}}.json</code></div>'
        '<p class="muted" style="margin-top:10px">Example: <a href="/api/v1/business/US/2026.json">'
        "/api/v1/business/US/2026.json</a></p></section>"
        '<section class="sec"><h2>Fields</h2><ul>'
        "<li><code>businessDays</code> — total business days in the year</li>"
        "<li><code>monthly</code> — business days per month</li>"
        "<li><code>holidays</code> — public holiday dates to exclude</li>"
        "<li><code>makeup</code> — China 补班 workdays counted as business days</li>"
        "<li>Rate limit: 240 requests/minute per IP; over the limit returns HTTP 429 with "
        "<code>Retry-After</code>. Responses are cacheable for a day.</li>"
        "</ul></section>"
        '<section class="sec"><h2>Support</h2><p>Free under a generous fair-use policy. '
        'Commercial or high-volume use? See <a href="../support/index.html">Support</a>.</p></section>'
    )
    (out / "api").mkdir(exist_ok=True)
    (out / "api" / "index.html").write_text(
        page("Business Day API — JSON by country and year", "Free static JSON API for business days and public holidays.", f"{site_url}/api/", api_body, base="../"),
        encoding="utf-8",
    )
    urls.append("api/")
    (out / "about").mkdir(exist_ok=True)
    (out / "about" / "index.html").write_text(
        page("About WorkdayKit", "About WorkdayKit, data sources and methodology.", f"{site_url}/about/",
             '<section class="hero"><h1>About WorkdayKit</h1><p class="lede">A free business-day calculator built on open holiday data.</p></section>'
             '<section class="sec"><p>Data sources: Nager.Date, OpenHolidays, python-holidays and chinese-days. '
             "China 调休/补班 is included. The calculator is for planning; always verify critical dates with official sources.</p></section>",
             base="../"),
        encoding="utf-8",
    )
    urls.append("about/")
    (out / "privacy").mkdir(exist_ok=True)
    (out / "privacy" / "index.html").write_text(
        page("Privacy", "Privacy policy for WorkdayKit.", f"{site_url}/privacy/",
             '<section class="hero"><h1>Privacy</h1><p class="lede">No accounts, no personal data collection.</p></section>'
             '<section class="sec"><p>We use standard server logs for security and aggregate analytics. '
             "Third-party advertising/affiliate partners may set cookies; control them in your browser settings.</p></section>",
             base="../"),
        encoding="utf-8",
    )
    urls.append("privacy/")
    (out / "support").mkdir(exist_ok=True)
    (out / "support" / "index.html").write_text(page_support(site_url), encoding="utf-8")
    urls.append("support/")

    (out / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    (out / "_headers").write_text(
        "/api/*\n  Access-Control-Allow-Origin: *\n  Cache-Control: public, max-age=86400\n"
        "/assets/support/*\n  Cache-Control: public, max-age=604800\n",
        encoding="utf-8",
    )
    support_dir = ROOT / "assets" / "support"
    if support_dir.exists():
        (out / "assets" / "support").mkdir(parents=True, exist_ok=True)
        for p in support_dir.glob("*.png"):
            (out / "assets" / "support" / p.name).write_bytes(p.read_bytes())
    (out / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {site_url}/sitemap.xml\n", encoding="utf-8"
    )
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    today = date.today().isoformat()
    for path in urls:
        sitemap.append(f"<url><loc>{site_url}/{path}</loc><lastmod>{today}</lastmod></url>")
    sitemap.append("</urlset>")
    (out / "sitemap.xml").write_text("\n".join(sitemap), encoding="utf-8")

    print(f"Built {len(urls)} pages -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
