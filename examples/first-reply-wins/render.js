// Render film.html frame by frame with Playwright (Node).
//   node render.js probe t1 t2 ...        -> probe/sheet.png (stills at those seconds)
//   node render.js chunk k n              -> frames of chunk k of n into sub/ (SUB subframes per frame, blended later)
//   node render.js encode                 -> out/video.mp4 (tmix motion blur, BT.709 TV range)
// Serve the folder first: python3 -m http.server 8765 (FILM_URL overrides).
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');
const HERE = __dirname, URL = process.env.FILM_URL || 'http://localhost:8765/film.html';
const FPS = 30, SUB = +(process.env.SUB || 6), SHUTTER = 0.5, T = 80 * 60 / 105;
const NF = Math.round(T * FPS);

async function openPage() {
  const b = await chromium.launch({ args: ['--font-render-hinting=none', '--force-color-profile=srgb', '--disable-gpu-vsync'] });
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  const errs = [];
  pg.on('pageerror', e => errs.push(String(e)));
  pg.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  await pg.goto(URL);
  await pg.waitForFunction('window.ready === true', null, { timeout: 120000 });
  return { b, pg, errs };
}
async function shot(pg, t, file, type = 'png') {
  await pg.evaluate(t => window.seek(t), t);
  await pg.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
  const el = await pg.$('#stage');
  await el.screenshot({ path: file, type, ...(type === 'jpeg' ? { quality: 93 } : {}) });
}
const ff = args => execFileSync('ffmpeg', ['-v', 'error', '-y', ...args], { stdio: 'inherit' });

(async () => {
  const [cmd, ...rest] = process.argv.slice(2);
  if (cmd === 'probe') {
    const dir = path.join(HERE, process.env.PROBE || 'probe'); fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
    const { b, pg, errs } = await openPage();
    for (let i = 0; i < rest.length; i++) await shot(pg, parseFloat(rest[i]), path.join(dir, `p_${String(i).padStart(2, '0')}.png`));
    await b.close();
    if (errs.length) console.log('PAGE ERRORS', errs.slice(0, 8));
    const cols = Math.min(rest.length, +(process.env.COLS || 4)), rows = Math.ceil(rest.length / cols);
    ff(['-i', path.join(dir, 'p_%02d.png'), '-vf', `scale=360:-1,tile=${cols}x${rows}:padding=6:color=white`, '-frames:v', '1', path.join(dir, 'sheet.png')]);
    console.log('probe ->', path.join(dir, 'sheet.png'));
  } else if (cmd === 'chunk') {
    const k = +rest[0], n = +rest[1], dir = path.join(HERE, process.env.SUBDIR || 'sub'); fs.mkdirSync(dir, { recursive: true });
    const a = Math.floor(NF * k / n), z = Math.floor(NF * (k + 1) / n);
    const { b, pg, errs } = await openPage();
    for (let f = a; f < z; f++) {
      for (let j = 0; j < SUB; j++) {
        const file = path.join(dir, `s_${String(f * SUB + j).padStart(6, '0')}.jpg`);
        if (fs.existsSync(file)) continue;
        const t = Math.min(T - 1e-4, Math.max(0, (f + (j - (SUB - 1) / 2) / SUB * SHUTTER) / FPS));
        await shot(pg, t, file, 'jpeg');
      }
      if ((f - a) % 30 === 0) console.log(`chunk ${k}: frame ${f}/${z}`);
    }
    await b.close();
    if (errs.length) console.log('PAGE ERRORS', errs.slice(0, 8));
  } else if (cmd === 'encode') {
    fs.mkdirSync(path.join(HERE, 'out'), { recursive: true });
    ff(['-framerate', String(FPS * SUB), '-i', path.join(HERE, process.env.SUBDIR || 'sub', 's_%06d.jpg'),
      '-vf', `tmix=frames=${SUB},select='eq(mod(n\\,${SUB})\\,${SUB - 1})',setpts=N/${FPS}/TB,scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p`,
      '-r', String(FPS), '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
      path.join(HERE, 'out', process.env.OUT || 'video.mp4')]);
    console.log('video -> out/video.mp4', NF, 'frames');
  }
})();
