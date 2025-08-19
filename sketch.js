// --- SETTINGS ---
const WIDTH = 900, HEIGHT = 640;
const NAME = 'Achai';
const WISH = 'Wishing you a year full of joy and adventure!';
const RAINBOW = [
  [255,80,80],[255,150,80],[255,220,100],[120,220,120],
  [100,180,255],[160,120,255],[240,120,200]
];
const SONGS = [
  {name: 'Birthday Song 1', file: 'song1.mp3', color: '#ffe09e'},
  {name: 'Birthday Song 2', file: 'song2.mp3', color: '#a9f5e4'},
  {name: 'Birthday Song 3', file: 'song3.mp3', color: '#e1bafd'},
  {name: 'Birthday Song 4', file: 'song4.mp3', color: '#ffb5b5'}
];

let started=false;
let stage = 0, t0 = 0, substageT0=0;
let matrixCols = [];
let matrixAlpha = 200, matrixColsCount=44; // a little less, but each column wider
let countdown = 3;
let dissolveParticles = [],ringHearts = [], mainHearts = [], risingHearts = [], confetti = [], cakeParticles = [], balloons = [];
let songModal = false, lastPlayedSongIdx = -1;
let mainSong, songObjs = [], isSongPlaying = false;
let wishesInput = '';
let uiButtons = [];
let funModalOn = false, exitModalOn = false, wishesModalOn = false, chooseSongModalOn = false;
const COUNTDOWN_DURATION = 3600; // slower (3.6s)
const BDAY_FADE = 3800, WISH_FADE = 3500; // slower text in+out
let seqTime=0, showButtons = false;

function preload() {
  mainSong = loadSound('MainSong.mp3');
  for (const s of SONGS) songObjs.push(loadSound(s.file));
}

function setup() {
  createCanvas(WIDTH, HEIGHT);
  textFont('monospace');
  pixelDensity(1);
  uiButtons = [
    {label:'Replay', y:38, color:'#2b9e4b', fn:doReplay},
    {label:'Exit', y:90, color:'#c03538', fn:doExit},
    {label:'Wishes', y:142, color:'#298be7', fn:doWishes},
    {label:'Little Fun', y:194, color:'#ad49d3', fn:doFun}
  ];
  resetAll();
}

function resetAll() {
  t0 = millis();
  seqTime = 0;
  stage = 0; countdown = 3; substageT0 = millis();
  matrixCols = [];
  // Matrix: more cinematic, larger text & gaps
  let colCharSize = 28; // larger
  let colPer = int(WIDTH / (colCharSize+4));
  matrixColsCount = max(26, colPer); // reduce so it's wider
  for (let i = 0; i < matrixColsCount; i++) {
    matrixCols.push({
      entries: Array.from({length: int(random(10,22))}, (_,k)=>({
        y: random(-HEIGHT*2.2, HEIGHT*1),
        ch: String.fromCharCode(random([...'0123456789abcdefghijklmnopqrstuvwxyz'.split('')]).charCodeAt(0))
      })),
      x: i * (WIDTH/matrixColsCount), speed: random(1.85, 3.8), fontSz:colCharSize
    });
  }
  mainHearts = [];
  let points = [];
  for (let a = 0; a < 360; a += 8) {
    let t = radians(a);
    let x = 16 * pow(sin(t), 3);
    let y = 13 * cos(t) - 5 * cos(2 * t) - 2 * cos(3 * t) - cos(4 * t);
    points.push([WIDTH/2+x*13, HEIGHT/2+-y*13-10]);
    mainHearts.push({x:WIDTH/2+x*13, y:HEIGHT/2+-y*13-10, p:random()});
  }
  ringHearts = [];
  // More sparkly, slower ring hearts
  for (let i=0; i<points.length; i+=2) {
    ringHearts.push({x:points[i][0],y:points[i][1],alpha:0,s:random(8,18),t:random(TWO_PI)});
  }
  risingHearts = [];
  dissolveParticles = [];
  confetti = [];
  cakeParticles = [];
  balloons = [];
  wishesInput = '';
  funModalOn = false; exitModalOn = false; wishesModalOn = false;
  showButtons = false;
}

function draw() {
  background(0);
  drawMatrix();
  if(!started) { drawStartOverlay(); return; }
  if (stage === 0) { drawCountdown(); showButtons=false; }
  else if(stage === 1) { drawHearts(); drawRingHearts(); drawConfetti(); drawBalloons(); drawCake(); drawBirthdayMsg(); showButtons=false;
    if(millis()-substageT0>BDAY_FADE+300) { stage=2; substageT0=millis();} }
  else if(stage === 2) { drawHearts(); drawRingHearts(); drawConfetti(); drawBalloons(); drawCake(); drawWishMsg(); showButtons=false; 
    if(millis()-substageT0>WISH_FADE+200) {stage=3; substageT0=millis(); showButtons=true;} }
  else if (stage === 3) { drawHearts(); drawRingHearts(); drawConfetti(); drawBalloons(); drawCake(); drawWithLove(); showButtons=true; }
  if(showButtons) drawUIButtons();
  if(chooseSongModalOn) drawSongModal();
  if(exitModalOn) drawExitModal();
  if(wishesModalOn) drawWishesModal();
}
function drawMatrix() {
  for (let col of matrixCols) {
    for (let eidx=0; eidx<col.entries.length; eidx++) {
      let e = col.entries[eidx];
      let t = eidx / (col.entries.length-1);
      let head = (eidx==col.entries.length-1);
      let c;
      if (head && random()<0.75) c=color(250,240,255,225);
      else if(head && random()<0.30) c=color(255,210,239,205);
      else if(random()<.055) c=color(255,220,240,145+random(60));
      else c=lerpColor(color(255,180-60*t,220-50*t), color(170,160+110*t,190+40*t), t*0.7+0.09*abs(sin(frameCount/27+col.x)));
      fill(c);
      textSize(col.fontSz+(head?2:0));
      let my = e.y;
      text(e.ch, col.x, my);
      e.y += col.speed*(1.03+0.46*sin(millis()/660+col.x));
      if (e.y > HEIGHT+36) {
        e.y = random(-240, -20);
        e.ch = String.fromCharCode(random([...'0123456789abcdefghijklmnopqrstuvwxyz'.split('')]).charCodeAt(0));
      }
      if (random()<0.042+0.03*head) e.ch = String.fromCharCode(random([...'0123456789abcdefghijklmnopqrstuvwxyz'.split('')]).charCodeAt(0));
    }
  }
  fill(0,0,0,matrixAlpha+10); rect(0,0,WIDTH,HEIGHT);
}
function drawCountdown() {
  let t = millis()-t0;
  let spacing = 1200;
  fill(255);textAlign(CENTER,CENTER);
  let which = Math.max(0, countdown-1);
  let prog = min(1, (t%spacing)/spacing);
  textSize(115*(1+.16*prog));
  let a = 252*(1-prog*prog);
  fill(255,a);
  if (countdown>0)
    text(countdown, WIDTH/2, HEIGHT/2);
  // Dissolve effect
  if(countdown>0&&prog>0.92&&dissolveParticles.length<30){
    for(let i=0;i<36;++i)dissolveParticles.push({
      x:WIDTH/2+random(-22,22),y:HEIGHT/2+random(-24,24),vx:random(-2.5,2.5),vy:random(-3.5,-0.8),a:255,col:color(random(170,255),random(80,200),random(100,220))
    });
  }
  for (let p of dissolveParticles) {
    fill(p.col);p.x+=p.vx;p.y+=p.vy;p.a-=9;
    fill(red(p.col),green(p.col),blue(p.col),max(0,p.a));
    ellipse(p.x,p.y, 14, 14);
  }
  dissolveParticles = dissolveParticles.filter(p=>p.a>0);
  if(t>spacing){
    countdown--;
    t0=millis();
    dissolveParticles=[];
    balloons.push({x:WIDTH/2+random(-18,18), y:HEIGHT/2+40, vx:random(-2.4,2.4), vy:-random(1.2,2.2), t:0, kind:'count', color:color(random(230,255),random(90,200),random(100,190))});
    if(countdown===0){ stage=1; substageT0=millis(); }
  }
  drawBalloons();
}
function drawBirthdayMsg() {
  let t=millis()-substageT0;
  let fadein = constrain(t/700,0,1), fadeout = constrain((BDAY_FADE-t)/800,0,1);
  let yoff = map(1-fadein,0,1,-72,0)+map(1-fadeout,0,1,0,-90);
  push();
  translate(0,yoff);
  let msg = "Happy Birthday, "+NAME+"!";
  textSize(56);
  textAlign(CENTER,CENTER);
  let totalW = 0;
  for(let i=0; i<msg.length; i++) totalW += textWidth(msg[i]);
  let startX = WIDTH/2 - totalW/2;
  let x = startX;
  for (let i = 0; i < msg.length; i++) {
    let alph = 255*fadein*fadeout;
    fill(...RAINBOW[i%RAINBOW.length],alph);
    text(msg.charAt(i), x + textWidth(msg[i])/2, 108);
    x += textWidth(msg[i]);
  }
  pop();
  if(t>BDAY_FADE*0.58&&balloons.filter(b=>b.kind=='bday').length<1) {
    balloons.push({x:WIDTH/2, y:108, vx:random(-2,2), vy:-random(1,2), t:0, kind:'bday', color:color(239,185,240,180)});
  }
}
function drawWishMsg() {
  let t=millis()-substageT0;
  let fadein = constrain(t/700,0,1), fadeout = constrain((WISH_FADE-t)/850,0,1);
  let yoff = map(1-fadein,0,1,-69,0)+map(1-fadeout,0,1,0,-88);
  push();
  translate(0,yoff);
  let msg = WISH;
  textSize(34);
  textAlign(CENTER,CENTER);
  let totalW = 0;
  for(let i=0; i<msg.length; i++) totalW += textWidth(msg[i]);
  let startX = WIDTH/2 - totalW/2;
  let x = startX;
  for(let i = 0; i < msg.length; i++) {
    let alph = 248*fadein*fadeout;
    fill(...RAINBOW[i%RAINBOW.length],alph);
    text(msg.charAt(i), x + textWidth(msg[i])/2, 184);
    x += textWidth(msg[i]);
  }
  pop();
  if(t>WISH_FADE*0.6&&balloons.filter(b=>b.kind=='wish').length<1) {
    balloons.push({x:WIDTH/2, y:184, vx:random(-2,2), vy:-random(1,2), t:0, kind:'wish', color:color(180,226,255,180)});
  }
}
function drawWithLove() {
  let msg = 'Happy Birthday, Achai! Distance may keep us apart, but nothing can stop me from sending you all my love and warm hugs. I hope today reminds you of how beautiful and special you are.';
  fill(255,220,240); textSize(25); textAlign(CENTER,CENTER);
  let y = HEIGHT/2+138;
  let wrapLines = wrapTextLines(msg, WIDTH-120); // leave margin
  for(let i=0; i<wrapLines.length; i++) {
    text(wrapLines[i], WIDTH/2, y+i*30);
  }
  fill(255,200,230);
  textSize(28);
  text('With all my love',WIDTH/2,y+wrapLines.length*31+8);
}
// Helper for word-wrapping text in canvas
function wrapTextLines(str, maxWidth) {
  textSize(25);
  let words = str.split(' ');
  let lines = [], line = '';
  for(let n=0; n<words.length; n++) {
    let testLine = line + words[n] + ' ';
    if (textWidth(testLine) > maxWidth && n > 0) {
      lines.push(line.trim());
      line = words[n] + ' ';
    } else {
      line = testLine;
    }
  }
  lines.push(line.trim());
  return lines;
}
function drawHearts() {
  noStroke();
  for (let h of mainHearts) {
    fill(255,70+random(80),110+random(80),210);
    ellipse(h.x, h.y, 22+random(-4,4),22+random(-4,4));
  }
  if (frameCount%7===0&&risingHearts.length<18) {
    risingHearts.push({x:random(WIDTH*0.16,WIDTH*0.85),y:HEIGHT+random(8,60),vx:random(-.5,.5),vy:-random(1.05,2.8),size:random(4,8),a:255});
  }
  for(let rh of risingHearts){
    push();fill(255,random(90,150),random(120,200),rh.a);
    let x=rh.x,y=rh.y,s=rh.size;
    ellipse(x-s/2,y-s/4,s,s); ellipse(x+s/2,y-s/4,s,s);
    triangle(x-s,y,x+s,y,x,y+s*1.14);
    pop();
    rh.x+=rh.vx;rh.y+=rh.vy;rh.a-=.77;}
  risingHearts = risingHearts.filter(rh=>rh.y>HEIGHT/2-23&&rh.a>22);
}
function drawRingHearts(){
  let base = int(millis()/290)%ringHearts.length;
  for(let i=0;i<ringHearts.length;++i){
    let delta = (i-base+ringHearts.length)%ringHearts.length;
    if(delta<6){
      let p=1-delta/6.0,e=1-(1-p)**3,alpha=215*e*e;
      let s=int(10+12*e*e+random(-2,2));
      let pulse = 1+0.10*sin(millis()/158+delta*1.9);
      let c=color(255,
        120+84*e*pulse*random(0.7,1.0),
        150+110*e*pulse*random(0.8,1.0),alpha*random(0.8,1));
      push(); noStroke(); fill(c);
      let {x,y}=ringHearts[i];
      ellipse(x-s*0.5,y-s*0.41,s*1.08,s*1.03); ellipse(x+s*0.5,y-s*0.41,s*1.07,s*1.03);
      triangle(x-s,y,x+s,y,x,y+s*1.13);
      pop();
    }
  }
}
function drawCake(){
  let cx = WIDTH/2, cy = HEIGHT/2+46;
  let cakeW = 193, cakeH = 90;
  let layers = [[250,200,230],[240,170,210],[255,220,200],[245,200,255]];
  for(let i=0;i<layers.length;++i){
    let ly = cy-12 + i*18;
    fill(40,20,35); rect(cx-cakeW/2+7,ly+6,cakeW-14,12,8);
    fill(...layers[i]); rect(cx-cakeW/2+10,ly,cakeW-20,12,8);
  }
  for (let i=0;i<18;++i){
    fill(random([color(255,120,180),color(255,200,80),color(180,255,220),color(200,200,255)]));
    ellipse(cx-cakeW/2+28+random(cakeW-56),cy-3+random(cakeH-18),5,5);
  }
  fill(255,255,230); rect(cx-8,cy-42,16,28,6);
  let f = (sin(millis()/180)+1)/2.0;
  fill(255,220+26*f,130);
  ellipse(cx, cy-44-8*f, 16, 24+11*f);
}
function drawConfetti(){
  if (confetti.length<140) for(let i=0;i<4;++i) confetti.push({x:random(WIDTH),y:random(-HEIGHT,0),size:random(3,8),c:color(random(200,255),random(70,255),random(70,255)),s:random(1.2,3.7),sway:random(TWO_PI)});
  for (let c of confetti){
    fill(c.c); push(); translate(c.x+sin(c.sway+frameCount*0.034)*8, c.y);
    rotate(sin(c.sway+frameCount*0.04)*0.28); rect(0, 0, c.size, c.size); pop();
    c.y += c.s; if (c.y > HEIGHT+8) {c.y = random(-60, 0); c.x = random(WIDTH);}
  }
}
function drawBalloons(){
  for(let b of balloons){
    b.y += b.vy; b.x += b.vx; b.t += 1;
    let sway = 7*sin((b.t)/43.0);
    stroke(230,220,210,140); strokeWeight(2);
    line(b.x, b.y, b.x+sway, b.y-29);
    noStroke(); fill(b.color);
    ellipse(b.x+sway, b.y-39, 34, 44);
  }
  balloons = balloons.filter(b=>b.y>-120);
}
function drawUIButtons() {
  for (let idx=0;idx<uiButtons.length;idx++) {
    let btn=uiButtons[idx];
    let bx=WIDTH-138,by=btn.y,bw=112,bh=47;
    fill(btn.color);
    stroke(255,244,255,40);
    rect(bx,by,bw,bh,11);
    noStroke();
    fill(255);
    textAlign(CENTER,CENTER);
    textSize(19);
    text(btn.label,bx+bw/2,by+bh/2+1);
  }
}
function doReplay() { resetAll(); if(mainSong.isPlaying()) mainSong.stop(); for(let s of songObjs) s.stop(); isSongPlaying=false; if (!mainSong.isPlaying()) { mainSong.play(); isSongPlaying=true; } }
function doExit() { exitModalOn = true; for(let s of songObjs) s.stop(); mainSong.stop(); isSongPlaying=false; }
function doWishes() { wishesInput=''; wishesModalOn=true; }
function doFun() { chooseSongModalOn=true; }
function drawStartOverlay() {
  fill(0,0,0,205); rect(0,0,WIDTH,HEIGHT);
  fill(255,246,252); stroke(180,100,255,90); strokeWeight(2);
  rect(WIDTH/2-200, HEIGHT/2-80, 405, 146, 30);
  noStroke(); fill(90,15,70); textAlign(CENTER,CENTER); textSize(33);
  text('Click to Start the Magic!', WIDTH/2, HEIGHT/2-16);
  textSize(22); fill(133,128,180);
  text('Music & Animation will begin 🎵', WIDTH/2, HEIGHT/2+29);
}

function mousePressed() {
  if(!started) {
    started=true;
    resetAll();
    stage=0;
    t0=millis();
    substageT0=millis();
    if (!mainSong.isPlaying()) {
      mainSong.play();
      isSongPlaying = true;
    }
    return;
  }
  if (chooseSongModalOn) {
    for(let i=0; i<SONGS.length; ++i){
      let rx=WIDTH/2-152,ry=HEIGHT/2-56+i*66;
      if(mouseX>rx&&mouseX<rx+294 && mouseY>ry&&mouseY<ry+56){
        if(songObjs[i].isPlaying()) songObjs[i].stop();
        for(let j=0;j<songObjs.length;++j)if(j!==i)songObjs[j].stop();
        mainSong.stop();
        songObjs[i].play();
        lastPlayedSongIdx=i;
        chooseSongModalOn=false;
        isSongPlaying = true;
        return;
      }
    }
    return;
  }
  if (showButtons) {
    for(let idx=0;idx<uiButtons.length;idx++) {
      let btn=uiButtons[idx];
      let bx=WIDTH-138,by=btn.y,bw=112,bh=47;
      if(mouseX>bx && mouseX<bx+bw && mouseY>by && mouseY<by+bh) {
        btn.fn();
        return;
      }
    }
  }
}
function keyPressed(){
  if(exitModalOn && (key==='Escape'||key==='q')) {exitModalOn=false;}
  if(wishesModalOn && (key==='Escape'||key==='q')) {wishesModalOn=false;wishesInput='';}
  if(chooseSongModalOn && (key==='Escape'||key==='q')) {chooseSongModalOn=false;}
}
function drawExitModal() {
  fill(30,0,45,224); rect(0,0,WIDTH,HEIGHT);
  fill(255); stroke(200,130,220,100); strokeWeight(2);
  rect(WIDTH/2-162,HEIGHT/2-50,332,100,34);
  noStroke(); fill(75,30,80); textAlign(CENTER,CENTER); textSize(25);
  text('Goodbye!\nReload page to restart.',WIDTH/2,HEIGHT/2);
}
function drawSongModal() {
  fill(0,0,0,182); rect(0,0,WIDTH,HEIGHT);
  fill(255, 249, 254); stroke(200,140,255,90); strokeWeight(3);
  rect(WIDTH/2-200, HEIGHT/2-168, 400, 312,30);
  noStroke(); fill(40,20,45); textAlign(CENTER,CENTER); textSize(34);
  text('Choose Birthday Song', WIDTH/2, HEIGHT/2-122);
  for (let i=0;i<SONGS.length;i++) {
    fill(SONGS[i].color); stroke(180,130,180,100); strokeWeight(2);
    rect(WIDTH/2-152, HEIGHT/2-56+i*66, 294, 56, 16);
    noStroke();fill(65,20,60); textSize(24);
    text(SONGS[i].name, WIDTH/2, HEIGHT/2-28+ i*66);
  }
  fill(80,60,130,80); noStroke();
  textSize(16); text('ESC to close',WIDTH/2,HEIGHT/2+139);
}
function drawWishesModal() {
  fill(220,210,245,238); rect(0,0,WIDTH,HEIGHT);
  fill(70,20,30,220); stroke(170,120,210,85); strokeWeight(3);
  rect(WIDTH/2-242,HEIGHT/2-72,484,136,24);
  noStroke(); fill(55,27,50); textAlign(CENTER,CENTER); textSize(25);
  text('Type your birthday wish below! (ENTER to send!)',WIDTH/2,HEIGHT/2-44);
  fill(240,250,220); stroke(160,150,205,80); rect(WIDTH/2-130,HEIGHT/2+8,260,48,13);
  noStroke(); fill(40,20,55); textAlign(CENTER,CENTER); textSize(22);
  text(wishesInput||' ',WIDTH/2,HEIGHT/2+33);
  textSize(15); fill(90,27,55); text('(Press ESC to cancel)',WIDTH/2,HEIGHT/2+78);
}
function keyTyped() {
  if(wishesModalOn) {
    if (keyCode===ENTER) {
      if(wishesInput.trim().length>0) {
        // Open WhatsApp with prefilled message
        window.open('https://wa.me/211917854654?text=' + encodeURIComponent(wishesInput), '_blank');
      }
      wishesModalOn=false;wishesInput=''; return false;
    }
    if(keyCode===BACKSPACE) wishesInput=wishesInput.slice(0,-1);
    else if(key.length===1 && wishesInput.length<80) wishesInput+=key;
    return false;
  }
}
