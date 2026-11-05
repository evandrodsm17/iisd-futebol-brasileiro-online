const durations = [1, 2, 2, 3, 20];
const total = durations.reduce((a, b) => a + b, 0);
const canvas = document.getElementById('keeper-throw-sequence');
const status = document.getElementById('keeper-throw-sequence-status');
const play = document.getElementById('keeper-throw-play');
const slider = document.getElementById('keeper-throw-tick');
const label = document.getElementById('keeper-throw-frame');
const ctx = canvas.getContext('2d');
const sheet = new Image();
let tick = 0, playing = true, last = null;
function draw() {
  let frame = Math.floor(tick), index = 0;
  while (index < durations.length - 1 && frame >= durations[index]) frame -= durations[index++];
  ctx.clearRect(0, 0, 96, 96);
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(sheet, index * 96, 0, 96, 96, 0, 0, 96, 96);
  slider.value = String(Math.floor(tick));
  label.textContent = `${Math.floor(tick) + 1} / ${total}`;
}
function animate(now) {
  if (last !== null && playing) tick = (tick + Math.min(100, Math.max(0, now - last)) * 60 / 1000) % total;
  last = now;
  draw();
  requestAnimationFrame(animate);
}
sheet.onload = () => {
  if (sheet.naturalWidth !== 480 || sheet.naturalHeight !== 96) {
    status.textContent = 'Arquivo local da sequência tem dimensões inválidas.';
    return;
  }
  play.disabled = false; slider.disabled = false;
  status.textContent = 'Cinco poses validadas; cadência observada em um replay, sem a continuação completa.';
  draw(); requestAnimationFrame(animate);
};
sheet.onerror = () => { status.textContent = 'Sequência local indisponível: gere os dados da ROM e das capturas validadas.'; };
play.addEventListener('click', () => {
  playing = !playing; play.textContent = playing ? 'Pausar' : 'Reproduzir'; last = null;
});
slider.addEventListener('input', () => {
  tick = Math.max(0, Math.min(total - 1, Number(slider.value) || 0));
  playing = false; play.textContent = 'Reproduzir'; last = null; draw();
});
sheet.src = '../assets/issd/slide-lab-local/goalkeeper-throw-sheet.png';
