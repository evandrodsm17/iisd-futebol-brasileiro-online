const sources = {
  '0': {path:'../assets/issd/slide-lab-local/goalkeeper-throw-sheet.png', durations:[1, 2, 2, 3, 20]},
  '7': {path:'../assets/issd/slide-lab-local/goalkeeper-throw-7.png', durations:[2, 2, 2, 2, 20]},
  '1': {path:'../assets/issd/slide-lab-local/goalkeeper-throw-1.png', durations:[2, 2, 2, 3, 22]}
};
const canvas = document.getElementById('keeper-throw-sequence');
const status = document.getElementById('keeper-throw-sequence-status');
const direction = document.getElementById('keeper-throw-direction');
const play = document.getElementById('keeper-throw-play');
const slider = document.getElementById('keeper-throw-tick');
const label = document.getElementById('keeper-throw-frame');
const ctx = canvas.getContext('2d');
let sheet = null, durations = [], total = 0, tick = 0, playing = true, last = null, generation = 0;
function draw() {
  if (!sheet) return;
  let frame = Math.floor(tick), index = 0;
  while (index < durations.length - 1 && frame >= durations[index]) frame -= durations[index++];
  ctx.clearRect(0, 0, 96, 96);
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(sheet, index * 96, 0, 96, 96, 0, 0, 96, 96);
  slider.value = String(Math.floor(tick));
  const release = direction.value === '0' && Math.floor(tick) === 5 ? ' · vínculo com o goleiro liberado neste replay' : '';
  label.textContent = `${Math.floor(tick) + 1} / ${total}${release}`;
}
function loadDirection() {
  const selected = sources[direction.value]; const current = ++generation;
  sheet = null; tick = 0; last = null; play.disabled = true; slider.disabled = true;
  ctx.clearRect(0, 0, 96, 96); label.textContent = '';
  if (!selected) { status.textContent = 'Orientação indisponível.'; return; }
  status.textContent = 'Carregando sequência local…';
  const image = new Image();
  image.onload = () => {
    if (current !== generation) return;
    if (image.naturalWidth !== 480 || image.naturalHeight !== 96) { status.textContent = 'Arquivo local da sequência tem dimensões inválidas.'; return; }
    sheet = image; durations = selected.durations; total = durations.reduce((a, b) => a + b, 0);
    slider.max = String(total - 1); play.disabled = false; slider.disabled = false;
    status.textContent = 'Cinco poses validadas; cadência observada em um replay, sem a continuação completa.'; draw();
  };
  image.onerror = () => { if (current === generation) status.textContent = 'Sequência local indisponível: gere os dados da ROM e das capturas validadas.'; };
  image.src = selected.path;
}
function animate(now) {
  if (last !== null && playing && sheet) tick = (tick + Math.min(100, Math.max(0, now - last)) * 60 / 1000) % total;
  last = now; draw(); requestAnimationFrame(animate);
}
direction.addEventListener('change', loadDirection);
play.addEventListener('click', () => { playing = !playing; play.textContent = playing ? 'Pausar' : 'Reproduzir'; last = null; });
slider.addEventListener('input', () => {
  if (!sheet) return;
  tick = Math.max(0, Math.min(total - 1, Number(slider.value) || 0));
  playing = false; play.textContent = 'Reproduzir'; last = null; draw();
});
loadDirection(); requestAnimationFrame(animate);
