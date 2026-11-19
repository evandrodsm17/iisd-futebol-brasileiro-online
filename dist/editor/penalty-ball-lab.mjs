const canvas = document.querySelector('#penalty-ball-preview');
const direction = document.querySelector('#penalty-ball-direction');
const play = document.querySelector('#penalty-ball-play');
const slider = document.querySelector('#penalty-ball-frame');
const counter = document.querySelector('#penalty-ball-counter');
const status = document.querySelector('#penalty-ball-status');
const ctx = canvas.getContext('2d');
let data, image, animation = 0;

function draw() {
  const capture = data.captures.find(item => item.input === direction.value);
  const index = Number(slider.value) - 1;
  const frame = capture.frames[index];
  const available = capture.frames.filter(Boolean).length;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (frame) {
    ctx.imageSmoothingEnabled = false;
    const captureIndex = data.captures.indexOf(capture);
    ctx.drawImage(image, (captureIndex * data.frame_count + index) * 16, 0, 16, 16, frame.x, frame.y, 16, 16);
  }
  counter.textContent = `${index + 1} / ${data.frame_count}`;
  status.textContent = frame
    ? `${available} de ${data.frame_count} quadros validados. A posição e os pixels foram capturados no jogo; ambos os controles receberam a direção.`
    : `Quadro sem associação segura. ${available} de ${data.frame_count} quadros foram validados; mova o controle para ver outro.`;
}
function stop() { cancelAnimationFrame(animation); animation = 0; }
slider.addEventListener('input', () => { stop(); draw(); });
direction.addEventListener('change', () => { stop(); slider.value = '1'; draw(); });
play.addEventListener('click', () => {
  stop();
  let start;
  const animate = now => {
    if (start === undefined) start = now;
    const tick = Math.min(data.frame_count - 1, Math.floor((now - start) * 60 / 1000));
    slider.value = String(tick + 1);
    draw();
    if (tick < data.frame_count - 1) animation = requestAnimationFrame(animate);
  };
  animation = requestAnimationFrame(animate);
});
try {
  const response = await fetch('../assets/issd/penalty-ball-observed-local.json');
  if (!response.ok) throw new Error('manifest unavailable');
  data = await response.json();
  if (data.schema !== 'issd-penalty-ball-preview/v1' || data.frame_count !== 40 ||
      !Array.isArray(data.captures) || data.captures.length !== 2 ||
      !['Left', 'Right'].every(name => data.captures.some(capture => capture.input === name && capture.frames?.length === 40))) throw new Error('invalid manifest');
  image = new Image();
  image.src = '../assets/issd/penalty-ball-observed-local.png';
  await image.decode();
  if (image.naturalWidth !== 1280 || image.naturalHeight !== 16) throw new Error('invalid image');
  direction.disabled = slider.disabled = play.disabled = false;
  slider.value = String(data.captures[0].frames.findIndex(Boolean) + 1);
  draw();
} catch {
  status.textContent = 'Amostras locais indisponíveis. Gere a prévia a partir das capturas locais para visualizá-las.';
}
