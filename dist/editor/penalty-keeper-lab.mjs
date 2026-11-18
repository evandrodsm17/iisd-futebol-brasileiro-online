const canvas = document.querySelector('#penalty-keeper-preview');
const slider = document.querySelector('#penalty-keeper-frame');
const counter = document.querySelector('#penalty-keeper-counter');
const status = document.querySelector('#penalty-keeper-status');
const play = document.querySelector('#penalty-keeper-play');
const image = new Image();
let frameCount = 40;
let continuous = true;

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
  const draw = () => {
    const index = Number(slider.value);
    context.clearRect(0, 0, width, height);
    context.imageSmoothingEnabled = false;
    context.drawImage(image, index * width, 0, width, height, 0, 0, width, height);
    counter.textContent = `${index + 1} / ${frameCount}`;
  };
  let animation = 0;
  const stops = continuous ? Array.from({ length: frameCount }, (_, index) => index) : [0, 3, 7, 11, 26];
  slider.addEventListener('input', () => { cancelAnimationFrame(animation); draw(); });
  play.addEventListener('click', () => {
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
  });
  slider.disabled = false;
  slider.max = String(frameCount - 1);
  play.disabled = false;
  status.textContent = continuous
    ? 'Trecho de 40 quadros capturados a 60 Hz, com uma aparência e direção. A ação completa e outras variações ainda estão em investigação.'
    : 'Amostra de cinco poses, com intervalos dos seletores observados. A cadência visual completa ainda está em investigação.';
  draw();
};
image.onerror = () => {
  if (continuous) {
    continuous = false;
    frameCount = 5;
    image.src = '../assets/issd/penalty-keeper-preview-local.png';
    return;
  }
  status.textContent = 'Prévia local indisponível. Gere as poses a partir da captura local para visualizá-las.';
};
image.src = '../assets/issd/penalty-keeper-continuous-local.png';
