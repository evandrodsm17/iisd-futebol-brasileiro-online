const canvas = document.querySelector('#penalty-keeper-preview');
const slider = document.querySelector('#penalty-keeper-frame');
const counter = document.querySelector('#penalty-keeper-counter');
const status = document.querySelector('#penalty-keeper-status');
const play = document.querySelector('#penalty-keeper-play');
const sample = document.querySelector('#penalty-keeper-sample');
const image = new Image();
let frameCount = 40;
let continuous = true;
let animation = 0;
let draw = () => {};

image.onload = () => {
  if (!image.naturalWidth || image.naturalWidth % frameCount !== 0 || !image.naturalHeight) {
    status.textContent = 'As poses locais não puderam ser carregadas.';
    return;
  }
  const width = image.naturalWidth / frameCount;
  const height = image.naturalHeight;
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  draw = () => {
    const index = Number(slider.value);
    context.clearRect(0, 0, width, height);
    context.imageSmoothingEnabled = false;
    context.drawImage(image, index * width, 0, width, height, 0, 0, width, height);
    counter.textContent = `${index + 1} / ${frameCount}`;
  };
  const stops = continuous ? Array.from({ length: frameCount }, (_, index) => index) : [0, 3, 7, 11, 26];
  play.onclick = () => {
    cancelAnimationFrame(animation);
    let start;
    const advance = now => {
      if (start === undefined) start = now;
      const tick = Math.floor((now - start) * 60 / 1000);
      let frame = 0;
      while (frame + 1 < stops.length && tick >= stops[frame + 1]) frame++;
      slider.value = String(frame);
      draw();
      if (frame < stops.length - 1) animation = requestAnimationFrame(advance);
    };
    animation = requestAnimationFrame(advance);
  };
  slider.disabled = false;
  slider.max = String(frameCount - 1);
  play.disabled = false;
  status.textContent = continuous
    ? 'Trecho capturado a 60 Hz. Nos ensaios direcionais, ambos os controles receberam o comando; a ação completa e outras variações ainda estão em investigação.'
    : 'Amostra de cinco poses, com intervalos dos seletores observados. A cadência visual completa ainda está em investigação.';
  draw();
};
image.onerror = () => {
  if (continuous && sample.value === 'base') {
    continuous = false;
    frameCount = 5;
    image.src = '../assets/issd/penalty-keeper-preview-local.png';
    return;
  }
  status.textContent = 'Prévia local indisponível. Gere as poses a partir da captura local para visualizá-las.';
};
slider.addEventListener('input', () => { cancelAnimationFrame(animation); draw(); });
sample.addEventListener('change', () => {
  cancelAnimationFrame(animation);
  slider.disabled = true;
  play.disabled = true;
  slider.value = '0';
  counter.textContent = '';
  canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
  status.textContent = 'Carregando poses locais…';
  continuous = true;
  frameCount = sample.value === 'left' ? 39 : 40;
  const file = sample.value === 'base' ? 'continuous' : sample.value;
  image.src = `../assets/issd/penalty-keeper-${file}-local.png`;
});
image.src = '../assets/issd/penalty-keeper-continuous-local.png';
