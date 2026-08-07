#!/usr/bin/env python3
"""
Generates tools/photo-matcher.html — a self-contained page for pairing
inbox photos with inventory SKUs by eye.

Matching photos to items is the one step in this pipeline that can't be
automated: nothing in a phone filename (IMG_2109-Photoroom.jpg) says
which garment it is, and a wrong pairing ships the wrong picture to a
real buyer. This makes the human pass fast instead of removing it.

Output is a plain list of `filename -> SKU` lines, which feed
`lib/assign-photo.ts`.

    python3 tools/build-photo-matcher.py
    # then open tools/photo-matcher.html

Requires Pillow (`pip install Pillow`) for thumbnailing. Thumbnails are
embedded as data URIs so the page works with no server and no network.
"""
import base64
import io
import json
import os
import sys

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is required: python3 -m pip install Pillow")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INBOX = os.path.join(ROOT, "photo-inbox")
PRODUCTS = os.path.join(ROOT, "preview", "src", "products.json")
OUT = os.path.join(HERE, "photo-matcher.html")

THUMB_PX = 460
QUALITY = 72


def thumbnails() -> dict:
    out = {}
    for name in sorted(f for f in os.listdir(INBOX) if not f.lower().endswith(".md")):
        im = Image.open(os.path.join(INBOX, name))
        # Phone photos carry EXIF rotation; without this some land sideways.
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((THUMB_PX, THUMB_PX), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=QUALITY, optimize=True)
        out[name] = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return out


def main() -> None:
    thumbs = thumbnails()
    products = json.load(open(PRODUCTS))
    slim = [
        {
            "sku": p["sku"],
            "name": p["name"],
            "brand": p["brand"],
            "gender": p["gender"],
            "type": p["type"],
            "size": p["size"],
            "color": p["color"],
            "price": p["price"],
        }
        for p in products
        if p.get("available")
    ]

    html = TEMPLATE.replace("__THUMBS__", json.dumps(thumbs)).replace(
        "__PRODUCTS__", json.dumps(slim)
    )
    with open(OUT, "w") as f:
        f.write(html)

    size_mb = os.path.getsize(OUT) / 1024 / 1024
    print(f"Wrote {os.path.relpath(OUT, ROOT)} — {len(thumbs)} photo(s), "
          f"{len(slim)} item(s), {size_mb:.1f} MB")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Old Light — photo matcher</title>
<style>
  :root{
    --void:#0a0a14; --panel:#15162c; --gold:#c9a24e; --chalk:#ede6d8;
    --ash:#948fb0; --line:#2a2b45; --ember:#b6633f; --good:#5f9e6e;
    --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--void);color:var(--chalk);
       font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,sans-serif}
  header{position:sticky;top:0;z-index:5;background:var(--void);
         border-bottom:1px solid var(--line);padding:10px 16px;
         display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between}
  .brand{font-family:Georgia,serif;font-size:20px;letter-spacing:.06em}
  .brand span{color:var(--gold)}
  .counts{font-family:var(--mono);font-size:11px;color:var(--ash);letter-spacing:.12em;text-transform:uppercase}
  .wrap{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px;padding:16px;max-width:1400px;margin:0 auto}
  @media(max-width:860px){.wrap{grid-template-columns:1fr}}
  .photo{border:1px solid var(--line);background:var(--panel);padding:10px;position:sticky;top:64px;align-self:start}
  .photo img{width:100%;height:auto;display:block;background:#fff}
  .fname{font-family:var(--mono);font-size:11px;color:var(--gold);margin-top:8px;word-break:break-all}
  .meta{font-family:var(--mono);font-size:10px;color:var(--ash);text-transform:uppercase;letter-spacing:.12em;margin-top:4px}
  input,select,button{font:inherit}
  .search{width:100%;padding:9px 10px;background:transparent;color:var(--chalk);
          border:1px solid var(--line);font-family:var(--mono);font-size:13px}
  .search:focus{outline:none;border-color:var(--gold)}
  .filters{display:flex;gap:8px;margin:8px 0}
  .filters select{flex:1;padding:8px;background:var(--void);color:var(--chalk);border:1px solid var(--line);
                  font-family:var(--mono);font-size:11px;text-transform:uppercase;letter-spacing:.1em}
  .list{max-height:none;display:flex;flex-direction:column;gap:6px;margin-top:10px}
  .item{display:flex;justify-content:space-between;gap:10px;align-items:flex-start;
        border:1px solid var(--line);background:var(--void);padding:9px 10px;cursor:pointer;text-align:left}
  .item:hover{border-color:var(--gold)}
  .item.taken{opacity:.45}
  .item h4{margin:0;font-size:13px;font-weight:600;line-height:1.3}
  .item .sub{font-family:var(--mono);font-size:10px;color:var(--ash);text-transform:uppercase;letter-spacing:.1em;margin-top:3px}
  .item .sku{font-family:var(--mono);font-size:10px;color:var(--gold);white-space:nowrap}
  .bar{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
  .btn{padding:9px 14px;border:1px solid var(--line);background:transparent;color:var(--chalk);
       font-family:var(--mono);font-size:11px;text-transform:uppercase;letter-spacing:.12em;cursor:pointer}
  .btn:hover{border-color:var(--gold);color:var(--gold)}
  .btn.primary{background:var(--gold);color:var(--void);border-color:var(--gold);font-weight:700}
  .btn.warn:hover{border-color:var(--ember);color:var(--ember)}
  .done{border:1px solid var(--line);padding:12px;margin:0 16px 24px;max-width:1400px}
  .done h3{margin:0 0 8px;font-family:Georgia,serif;font-size:18px;letter-spacing:.04em}
  textarea{width:100%;height:170px;background:var(--panel);color:var(--chalk);border:1px solid var(--line);
           font-family:var(--mono);font-size:12px;padding:10px;resize:vertical}
  .hint{font-size:12px;color:var(--ash);line-height:1.6}
  .pill{display:inline-block;font-family:var(--mono);font-size:10px;letter-spacing:.1em;
        text-transform:uppercase;border:1px solid var(--line);padding:2px 7px;margin-right:6px}
  .pill.ok{border-color:var(--good);color:var(--good)}
  .empty{color:var(--ash);font-size:13px;padding:20px 0}
</style>
</head>
<body>
<header>
  <div class="brand">OLD <span>LIGHT</span> — photo matcher</div>
  <div class="counts" id="counts"></div>
</header>

<div class="wrap">
  <div class="photo">
    <img id="shot" alt="" />
    <div class="fname" id="fname"></div>
    <div class="meta" id="pmeta"></div>
    <div class="bar">
      <button class="btn" id="prev">← Prev</button>
      <button class="btn" id="skip">Skip →</button>
      <button class="btn warn" id="reject">Not a product photo</button>
    </div>
    <p class="hint" style="margin-top:10px">
      Pick the item this photo shows. Assigning several photos to the same SKU is
      fine — they'll be numbered in the order you assign them, so lead with the
      best full-garment shot.
    </p>
  </div>

  <div>
    <input class="search" id="q" placeholder="Search brand, item, colour, SKU…" autocomplete="off" />
    <div class="filters">
      <select id="gender"><option value="">All departments</option></select>
      <select id="hide">
        <option value="">Show all items</option>
        <option value="1">Hide already-matched</option>
      </select>
    </div>
    <div class="list" id="list"></div>
  </div>
</div>

<div class="done">
  <h3>Your matches</h3>
  <p class="hint" id="summary"></p>
  <textarea id="out" readonly placeholder="Matches will appear here as you go…"></textarea>
  <div class="bar">
    <button class="btn primary" id="copy">Copy all</button>
    <button class="btn" id="undo">Undo last</button>
    <button class="btn warn" id="reset">Clear all</button>
  </div>
  <p class="hint" style="margin-top:10px">
    Paste that list back into the conversation and the photos get committed to
    the right SKUs. Your progress is saved in this browser, so you can close the
    tab and pick it up later.
  </p>
</div>

<script>
const THUMBS = __THUMBS__;
const PRODUCTS = __PRODUCTS__;
const FILES = Object.keys(THUMBS);
const KEY = 'oldlight-photo-matches-v1';

let idx = 0;
let matches = {};      // filename -> SKU  ('__REJECT__' = not a product photo)
try { matches = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { matches = {}; }

const el = (id) => document.getElementById(id);

const genders = [...new Set(PRODUCTS.map(p => p.gender))].sort();
genders.forEach(g => {
  const o = document.createElement('option'); o.value = g; o.textContent = g; el('gender').appendChild(o);
});

function save() { localStorage.setItem(KEY, JSON.stringify(matches)); }

function assignedCount() {
  return Object.values(matches).filter(v => v !== '__REJECT__').length;
}

function skuPhotoCount(sku) {
  return Object.values(matches).filter(v => v === sku).length;
}

function render() {
  if (idx < 0) idx = 0;
  if (idx >= FILES.length) idx = FILES.length - 1;
  const f = FILES[idx];
  el('shot').src = THUMBS[f];
  el('fname').textContent = f;

  const cur = matches[f];
  let meta = `Photo ${idx + 1} of ${FILES.length}`;
  if (cur === '__REJECT__') meta += ' · marked not a product';
  else if (cur) meta += ` · matched to ${cur}`;
  el('pmeta').textContent = meta;

  const rejected = Object.values(matches).filter(v => v === '__REJECT__').length;
  el('counts').textContent =
    `${assignedCount()} matched · ${rejected} rejected · ${FILES.length - Object.keys(matches).length} left`;

  renderList();
  renderOut();
}

function renderList() {
  const q = el('q').value.trim().toLowerCase();
  const g = el('gender').value;
  const hide = el('hide').value;
  const list = el('list');
  list.innerHTML = '';

  let items = PRODUCTS;
  if (g) items = items.filter(p => p.gender === g);
  if (hide) items = items.filter(p => skuPhotoCount(p.sku) === 0);
  if (q) items = items.filter(p =>
    [p.name, p.brand, p.type, p.color, p.sku, p.size].some(v => (v || '').toLowerCase().includes(q)));

  if (!items.length) {
    list.innerHTML = '<p class="empty">No items match that. Clear the search or switch department.</p>';
    return;
  }

  items.slice(0, 300).forEach(p => {
    const n = skuPhotoCount(p.sku);
    const b = document.createElement('button');
    b.className = 'item' + (n ? ' taken' : '');
    b.innerHTML =
      '<span><h4>' + esc(p.name || '(untitled)') + '</h4><span class="sub">' +
      esc([p.brand, p.size && ('Size ' + p.size), p.color, '$' + p.price].filter(Boolean).join(' · ')) +
      (n ? ' · <span style="color:var(--good)">' + n + ' photo' + (n > 1 ? 's' : '') + '</span>' : '') +
      '</span></span><span class="sku">' + esc(p.sku) + '</span>';
    b.onclick = () => { matches[FILES[idx]] = p.sku; save(); next(); };
    list.appendChild(b);
  });
}

function esc(s) {
  return String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

function renderOut() {
  const lines = Object.entries(matches)
    .filter(([, v]) => v !== '__REJECT__')
    .map(([f, sku]) => f + ' -> ' + sku);
  el('out').value = lines.join('\n');
  const rejected = Object.entries(matches).filter(([, v]) => v === '__REJECT__').map(([f]) => f);
  el('summary').innerHTML =
    '<span class="pill ok">' + lines.length + ' matched</span>' +
    (rejected.length ? '<span class="pill">' + rejected.length + ' rejected</span>' : '') +
    'Distinct items covered: ' + new Set(Object.values(matches).filter(v => v !== '__REJECT__')).size +
    ' of ' + PRODUCTS.length + '.';
}

function next() { idx = Math.min(idx + 1, FILES.length - 1); render(); }

el('prev').onclick = () => { idx = Math.max(0, idx - 1); render(); };
el('skip').onclick = next;
el('reject').onclick = () => { matches[FILES[idx]] = '__REJECT__'; save(); next(); };
el('q').oninput = renderList;
el('gender').onchange = renderList;
el('hide').onchange = renderList;
el('undo').onclick = () => {
  const keys = Object.keys(matches);
  if (!keys.length) return;
  const last = keys[keys.length - 1];
  delete matches[last];
  save();
  idx = FILES.indexOf(last);
  render();
};
el('reset').onclick = () => {
  if (!confirm('Clear every match you have made so far?')) return;
  matches = {}; save(); idx = 0; render();
};
el('copy').onclick = async () => {
  el('out').select();
  try { await navigator.clipboard.writeText(el('out').value); }
  catch (e) { document.execCommand('copy'); }
  el('copy').textContent = 'Copied';
  setTimeout(() => (el('copy').textContent = 'Copy all'), 1200);
};
document.addEventListener('keydown', (e) => {
  if (document.activeElement === el('q')) return;
  if (e.key === 'ArrowRight') next();
  if (e.key === 'ArrowLeft') el('prev').click();
});

// Start on the first photo that hasn't been dealt with yet.
const firstOpen = FILES.findIndex(f => !(f in matches));
idx = firstOpen === -1 ? 0 : firstOpen;
render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
