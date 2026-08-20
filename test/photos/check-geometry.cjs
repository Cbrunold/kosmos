const { chromium } = require(process.env.PW || 'playwright');
const fs = require('fs');
(async () => {
  const F = JSON.parse(fs.readFileSync(require('path').join(__dirname,'railbirds-geometry.json'),'utf8'));
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('file:///home/user/kosmos/public/billiards.html');
  await page.waitForTimeout(400);
  // a blank frame of the same size, so the canvas scales exactly as it would for the real photo
  const png = await page.evaluate(({W,H}) => {
    const c = document.createElement('canvas'); c.width=W; c.height=H;
    const x=c.getContext('2d'); x.fillStyle='#ececec'; x.fillRect(0,0,W,H);
    return c.toDataURL('image/png').split(',')[1];
  }, {W:F.imgW,H:F.imgH});
  fs.writeFileSync(require('path').join(require('os').tmpdir(),'blank.png'), Buffer.from(png,'base64'));
  await page.setInputFiles('#photofile',require('path').join(require('os').tmpdir(),'blank.png'));
  await page.waitForTimeout(800);

  const out = await page.evaluate((F) => {
    const { ph, phSolve, phGround, phCentre, phBallRadius, phcv } = window.kosmosPhoto;
    const sc = phcv.width / F.imgW;
    ph.corners = F.corners.map(c => [c[0]*sc, c[1]*sc]);
    if (!phSolve()) return { err: 'camera solve failed' };
    const L=2.54, W=1.27;
    const rows = F.balls.map(b => {
      const p = phGround([b.px[0]*sc, b.px[1]*sc]);
      const back = phCentre(p);
      return { name: b.name, p: [ +p[0].toFixed(3), +p[1].toFixed(3) ],
               inside: p[0]>0 && p[0]<L && p[1]>0 && p[1]<W,
               r: +phBallRadius(p).toFixed(1),
               reproj: +Math.hypot(back[0]-b.px[0]*sc, back[1]-b.px[1]*sc).toFixed(1) };
    });
    return { cam: { h:+ph.cam.h.toFixed(2), assumed: !!ph.cam.assumed, xy: ph.cam.xy.map(v=>+v.toFixed(2)) },
             canvas: [phcv.width, phcv.height], rows };
  }, F);

  if (out.err) { console.log(out.err); await browser.close(); return; }
  console.log(`canvas ${out.canvas.join('x')} | camera ${out.cam.h} m high${out.cam.assumed?' (lens assumed)':''}, standing at (${out.cam.xy.join(', ')}) in table metres`);
  console.log('\nball                table position (m)      on the cloth?   ball radius   re-projects to');
  for (const r of out.rows)
    console.log(`  ${r.name.padEnd(10)}  (${r.p[0].toFixed(2)}, ${r.p[1].toFixed(2)})            ${r.inside?'yes':'NO '}           ${String(r.r).padStart(4)} px      ${r.reproj} px off`);
  console.log('\nERRORS:', errors.length ? errors : 'none');
  await browser.close();
})();
