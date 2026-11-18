const canvas = document.querySelector('#penalty-keeper-preview');
const slider = document.querySelector('#penalty-keeper-frame');
const counter = document.querySelector('#penalty-keeper-counter');
const status = document.querySelector('#penalty-keeper-status');
const image = new Image();

image.onload = () => {
  if (!image.naturalWidth || image.naturalWidth % 5 !== 0 || !image.naturalHeight) {
    status.textContent = 'As poses locais não puderam ser carregadas.';
    return;
  }
  const width = image.naturalWidth / 5;
  const height = image.naturalHeight;
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  const draw = () => {
    const index = Number(slider.value);
    context.clearRect(0, 0, width, height);
    context.imageSmoothingEnabled = false;
    context.drawImage(image, index * width, 0, width, height, 0, 0, width, height);
    counter.textContent = `${index + 1} / 5`;
  };
  slider.addEventListener('input', draw);
  slider.disabled = false;
  status.textContent = 'Cinco poses da cena original de pênalti, com uma aparência e direção. A sequência completa e o tempo ainda estão em investigação.';
  draw();
};
image.onerror = () => {
  status.textContent = 'Prévia local indisponível. Gere as poses a partir da captura local para visualizá-las.';
};
image.src = '../assets/issd/penalty-keeper-preview-local.png';
