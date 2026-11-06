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
.cd-ring{position:relative;width:200px;height:200px;margin:0 auto}
.cd-ring svg{transform:rotate(-90deg);width:100%;height:100%}
.cd-ring .ring-bg{fill:none;stroke:rgba(255,255,255,.10);stroke-width:10}
.cd-ring .ring-fg{fill:none;stroke:#22c55e;stroke-width:10;stroke-linecap:round;stroke-dasharray:339.3;stroke-dashoffset:339.3;transition:stroke-dashoffset 1.4s cubic-bezier(.16,1,.3,1)}
.cd-ring-mid{position:absolute;inset:0;display:grid;place-items:center;text-align:center}
.cd-big{font-family:var(--font-display);font-size:3.1rem;line-height:1;color:#f7fbfa}
.cd-big span{display:block;font-family:var(--font-body);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:#8fa39d;margin-top:6px}
.cd-tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px}
.cd-tile{background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.10);border-radius:16px;padding:16px 18px;backdrop-filter:blur(6px)}
.cd-tile .v{font-family:var(--font-display);font-size:1.9rem;line-height:1.05;color:#f7fbfa}
.cd-tile .k{font-size:.72rem;color:#94a8a2;margin-top:4px;letter-spacing:.04em}
.cd-tile .dot-live{display:inline-block;width:7px;height:7px;border-radius:50%;background:#22c55e;margin-right:6px;animation:cdpulse 1.8s infinite}
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
    var fg=document.querySelector('.cd-ring .ring-fg');
    if(fg){ fg.style.strokeDashoffset=(339.3*(1-pct/100)).toFixed(1); }
    var keys=Object.keys(hol).sort(), next=null;
    for(var i=0;i<keys.length;i++){ if(keys[i]>=iso(today)){ next=keys[i]; break; } }
    if(next){ setText('cd-next',Math.round((new Date(next+'T00:00:00')-today)/86400000)); }
    else { setText('cd-next','—'); }
    var nameEl=document.getElementById('cd-name'); if(nameEl) nameEl.style.display='none';
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


def page(title: str, desc: str, canonical: str, body: str, base: str = "", extra: str = "") -> str:
    nav = (
        '<header class="site-head"><div class="wrap head-inner">'
        f'<a class="brand" href="{base}index.html"><span class="brand-mark">◷</span>{SITE_NAME}</a>'
        f'<nav><a href="{base}index.html">Calculator</a>'
        f'<a href="{base}countdown/index.html">Countdown</a>'
        f'<a href="{base}index.html#countries">Countries</a>'
        f'<a href="{base}api/index.html">API</a>'
        f'<a href="{base}about/index.html">About</a></nav>'
        "</div></header>"
    )
    foot = (
        '<footer class="site-foot"><div class="wrap">'
        f'<p><strong>{SITE_NAME}</strong> — {SITE_TAGLINE}</p>'
        '<p>Data: open holiday datasets (Nager.Date, OpenHolidays, python-holidays, chinese-days). '
        "For planning only — confirm critical dates with official sources.</p>"
        f'<p><a href="{base}privacy/index.html">Privacy</a> · '
        f'<a href="{base}about/index.html">About</a> · '
        f'<a href="{base}index.html">Calculator</a> · '
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
        f"<style>{CSS}</style></head><body>{nav}"
        f'<main class="wrap">{body}</main>{foot}'
        f"<script>{MOTION_JS}</script>{extra}</body></html>"
    )


FAVICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" rx="14" fill="#15161a"/>'
    '<path d="M20 26h24M20 36h14M20 46h9" stroke="#fbfaf7" stroke-width="3.4" stroke-linecap="round"/>'
    '<circle cx="45" cy="44" r="6" fill="#0f6b5c"/></svg>'
)


def calc_widget(default_cc: str, countries: list[dict]) -> str:
    options = "".join(
        f'<option value="{c["code"]}"{" selected" if c["code"] == default_cc else ""}>{c["name"]}</option>'
        for c in countries
    )
    years = "".join(f'<option value="{y}">{y}</option>' for y in YEARS)
    return (
        '<div class="calc" data-calc-root>'
        '<div class="calc-tabs">'
        '<button type="button" data-mode="between" class="on">Days between dates</button>'
        '<button type="button" data-mode="add">Add / subtract business days</button>'
        "</div>"
        '<div class="calc-row">'
        f'<label>Country<select data-country>{options}</select></label>'
        f'<label>Year<select data-year>{years}</select></label>'
        "</div>"
        '<div class="calc-row" data-panel="between">'
        '<label>Start date<input type="date" data-start></label>'
        '<label>End date<input type="date" data-end></label>'
        "</div>"
        '<div class="calc-row" data-panel="add" hidden>'
        '<label>Start date<input type="date" data-add-start></label>'
        '<label>Business days (negative to subtract)<input type="number" value="10" min="-365" max="365" data-add-n></label>'
        "</div>"
        '<button type="button" class="btn" data-calc>Calculate</button>'
        '<div class="calc-result" data-result></div>'
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
  setMode('between');
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

    countries = []
    for cc in sorted({r["country"] for r in rows}):
        name = COUNTRY_NAMES.get(cc, cc)
        countries.append({"code": cc, "name": name, "slug": slugify(name)})

    out = ROOT / "dist"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    urls: list[str] = []

    wk_js = (
        "<script>window.WK=" + json.dumps({"countries": countries, "years": YEARS}) + ";</script>"
        f"<script>{CALC_JS}</script>"
    )

    # homepage
    current_year = 2026
    cards = []
    for c in countries:
        total, _ = business_total(c["code"], current_year)
        if total <= 0:
            continue
        cards.append(
            f'<a class="card" href="{c["slug"]}/index.html"><div class="flag">{flag_emoji(c["code"])}</div>'
            f'<h3>{c["name"]}</h3><p>{total} business days in {current_year}</p></a>'
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
        '<p class="eyebrow">Business days · weekends · public holidays</p>'
        "<h1>Business days calculator</h1>"
        '<p class="lede">Count working days between two dates, or add business days to a date — for 95 countries, '
        "skipping weekends and public holidays (including China's 调休/补班 rules).</p>"
        '</section>'
        + calc_widget("US", countries)
        + '<section class="sec"><h2>Business days by country</h2>'
        '<p class="sub">How many business days are left in ' + str(current_year) + ", country by country.</p>"
        '<div class="grid">' + "".join(cards) + "</div></section>"
        '<section class="ad">[Ad slot]</section>'
        '<section class="sec"><h2>How it works</h2>'
        "<p>Pick a country and year, then either count the business days between two dates or add/subtract a number "
        "of business days. The calculator loads that country's public holidays and excludes them. Weekends are "
        "skipped automatically; China's make-up workdays (补班) are counted as working days.</p>"
        '<div class="callout">Tip: use it for delivery estimates, SLA deadlines, payroll periods, visa timelines and project planning.</div>'
        "</section>"
        '<section class="sec"><h2>FAQ</h2><dl class="faq">' + faq_html + "</dl></section>"
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
        cw = calc_widget(cc, countries)
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

    country_options = "".join(
        f'<option value="{c["code"]}"{" selected" if c["code"] == static_cc else ""}>{c["name"]}</option>'
        for c in countries
    )
    cd_body = (
        '<section class="cd-hero" id="hk-countdown" data-country="' + static_cc + '">'
        '<p class="eyebrow">Live business-day countdown</p>'
        f'<h1>Business days left in <span id="cd-year-label">{static_year}</span></h1>'
        '<p class="lede">Detected automatically from your location. Counts working days only — weekends and '
        "public holidays excluded (China's 补班 counted as working days).</p>"
        '<div class="cd-wrap">'
        '<div class="cd-ring" aria-hidden="true">'
        '<svg viewBox="0 0 120 120"><circle class="ring-bg" cx="60" cy="60" r="54"></circle>'
        '<circle class="ring-fg" cx="60" cy="60" r="54"></circle></svg>'
        '<div class="cd-ring-mid"><div class="cd-big" id="cd-year">' + str(static_left) + '</div>'
        '<span>business days left</span></div></div>'
        '<div class="cd-tiles">'
        '<div class="cd-tile"><div class="v" id="cd-month">' + str(static_month_left) + '</div>'
        '<div class="k">business days left this month</div></div>'
        '<div class="cd-tile"><div class="v" id="cd-next">' + (str(next_days) if next_days is not None else "—") + '</div>'
        '<div class="k">days until next public holiday</div></div>'
        '<div class="cd-tile"><div class="v" id="cd-total">' + str(static_total) + '</div>'
        '<div class="k">business days this year</div></div>'
        '<div class="cd-tile"><div class="v"><span class="dot-live"></span><span id="cd-clock">--:--:--</span></div>'
        '<div class="k">your local time</div></div>'
        "</div></div>"
        '<div class="cd-country"><label>Country <select data-cd-country>' + country_options + "</select></label>"
        '<span><strong id="cd-pct">' + str(static_pct) + '%</strong> of the year\'s business days done</span></div>'
        '<p class="cd-note">Location detected via Cloudflare edge geolocation · '
        '<a href="../index.html">business days calculator</a> · <a href="../about/index.html">about</a></p>'
        "</section>"
        '<section class="sec"><h2>What this counts</h2>'
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
    (out / "countdown" / "index.html").write_text(
        page("Business Days Left in " + str(static_year) + " — Live Countdown",
             "Live countdown of remaining business days in the year, auto-detected for your country. Weekends and public holidays excluded.",
             f"{site_url}/countdown/", cd_body, extra=wkdata + "<script>" + COUNTDOWN_JS + "</script>"),
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
        "</ul></section>"
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

    (out / "favicon.svg").write_text(FAVICON, encoding="utf-8")
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
