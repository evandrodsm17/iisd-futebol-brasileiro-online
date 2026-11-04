const preview = document.getElementById('goalkeeper-catch-preview');
const status = document.getElementById('goalkeeper-catch-status');
preview.addEventListener('load', () => {
  preview.hidden = false;
  status.textContent = 'Pose da ROM conferida com os dados e a imagem do jogo.';
});
preview.addEventListener('error', () => {
  preview.hidden = true;
  status.textContent = 'Prévia local indisponível: gere-a a partir da ROM e da captura validadas.';
});
preview.src = '../assets/issd/goalkeeper-catch-local.png';
