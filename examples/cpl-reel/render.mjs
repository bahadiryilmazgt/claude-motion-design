// CPL reel renderer (Node Playwright).
//   node render.mjs probe 0.5 2.4 3.3 ...   -> probe/sheet.png (stills, 4 per row)
//   node render.mjs chunk k n               -> frames of chunk k/n into sub/ (SUB subframes per frame on a 180 deg shutter)
//   node render.mjs encode                  -> blend subframes (tmix) -> out/video.mp4
//   node render.mjs draft                   -> 15 fps, 1 capture per frame, half size -> out/draft.mp4
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
const HERE = path.dirname(new URL(import.meta.url).pathname);
const URL_ = 'http://localhost:8771/film.html';
const FPS = 30, T = 30, SUB = 4, SHUTTER = 0.5;
const CUTS = [];

async function open() {
  const b = await chromium.launch({ args: ['--force-color-profile=srgb', '--font-render-hinting=none', '--disable-threaded-animation'] });
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  const errs = [];
  pg.on('pageerror', e => errs.push(String(e)));
  pg.on('console', m => { if (['error', 'warning'].includes(m.type())) errs.push('console: ' + m.text()); });
  await pg.goto(URL_);
  await pg.waitForFunction('window.ready === true', null, { timeout: 120000 });
  await pg.addStyleTag({ content: '*,*::before,*::after{transition:none!important}' });
  await pg.evaluate('document.getAnimations().forEach(a => a.pause())');
  return { b, pg, errs };
}
async function shot(pg, t, file, type = 'jpeg') {
  await pg.evaluate(`window.seek(${t})`);
  await pg.evaluate('new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))');
  const el = await pg.$('#stage');
  await el.screenshot({ path: file, type, ...(type === 'jpeg' ? { quality: 94 } : {}) });
}
const ff = (...a) => execFileSync('ffmpeg', ['-v', 'error', '-y', ...a], { stdio: 'inherit' });
const cmd = process.argv[2];
if (cmd === 'probe') {
  const dir = path.join(HERE, process.env.PROBE || 'probe'); fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir);
  const times = process.argv.slice(3).map(Number);
  const { b, pg, errs } = await open();
  for (let i = 0; i < times.length; i++) await shot(pg, times[i], path.join(dir, `p_${String(i).padStart(2, '0')}.png`), 'png');
  await b.close(); if (errs.length) console.log('PAGE ERRORS', errs.slice(0, 8));
  const cols = Math.min(4, times.length), rows = Math.ceil(times.length / cols);
  ff('-i', path.join(dir, 'p_%02d.png'), '-vf', `scale=360:-1,tile=${cols}x${rows}:padding=6:color=white`, '-frames:v', '1', path.join(dir, 'sheet.png'));
  console.log('probe ->', path.join(dir, 'sheet.png'));
} else if (cmd === 'chunk') {
  const k = +process.argv[3], n = +process.argv[4], N = FPS * T, a = Math.floor(N * k / n), z = Math.floor(N * (k + 1) / n);
  const dir = path.join(HERE, 'sub'); fs.mkdirSync(dir, { recursive: true });
  const offs = Array.from({ length: SUB }, (_, j) => (j - (SUB - 1) / 2) * SHUTTER / (FPS * SUB));
  const { b, pg, errs } = await open();
  for (let i = a; i < z; i++) {
    for (let j = 0; j < SUB; j++) {
      let t = Math.min(T - 1e-3, Math.max(0, i / FPS + offs[j]));
      for (const c of CUTS) if ((t < c) !== (i / FPS < c)) t = i / FPS >= c ? c : c - 1e-4;
      await shot(pg, t, path.join(dir, `s_${String(i * SUB + j).padStart(6, '0')}.jpg`));
    }
    if (i % 30 === 0) console.log(`chunk ${k}: frame ${i}/${z}`);
  }
  await b.close(); if (errs.length) console.log('PAGE ERRORS', errs.slice(0, 8));
  console.log(`chunk ${k} done`);
} else if (cmd === 'encode') {
  fs.mkdirSync(path.join(HERE, 'out'), { recursive: true });
  ff('-framerate', String(FPS * SUB), '-i', path.join(HERE, 'sub/s_%06d.jpg'),
    '-vf', `tmix=frames=${SUB},select='eq(mod(n\\,${SUB})\\,${SUB - 1})',setpts=N/${FPS}/TB`, '-r', String(FPS),
    '-c:v', 'libx264', '-crf', '14', '-preset', 'slow', '-pix_fmt', 'yuv420p', path.join(HERE, 'out/video.mp4'));
  console.log('video -> out/video.mp4');
} else if (cmd === 'draft') {
  const dir = path.join(HERE, 'sub_draft'); fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir);
  const fps = 15, { b, pg, errs } = await open();
  for (let i = 0; i < fps * T; i++) await shot(pg, i / fps, path.join(dir, `d_${String(i).padStart(5, '0')}.jpg`));
  await b.close(); if (errs.length) console.log('PAGE ERRORS', errs.slice(0, 8));
  ff('-framerate', String(fps), '-i', path.join(dir, 'd_%05d.jpg'), '-vf', 'scale=540:-2', '-c:v', 'libx264', '-crf', '23', '-pix_fmt', 'yuv420p', path.join(HERE, 'out/draft.mp4'));
}
