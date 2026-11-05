function loadPose(name, message) {
  const preview = document.getElementById(`goalkeeper-${name}-preview`);
  const status = document.getElementById(`goalkeeper-${name}-status`);
  preview.addEventListener('load', () => {
    preview.hidden = false;
    status.textContent = message;
  });
  preview.addEventListener('error', () => {
    preview.hidden = true;
    status.textContent = 'Prévia local indisponível: gere-a a partir da ROM e da captura validadas.';
  });
  preview.src = `../assets/issd/goalkeeper-${name}-local.png`;
}
loadPose('catch', 'Pose da ROM conferida com os dados e a imagem do jogo.');
loadPose('throw', 'Quadro do lançamento conferido com os dados e a imagem do jogo.');
