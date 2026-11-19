import {replayCapturedPenaltyMotion} from '../penalty-motion-replay.mjs';
import {nativePenaltyPostCrossing} from '../penalty-post-crossing.mjs';
import {replayPenaltySceneScore} from '../penalty-scene-score.mjs';
import {projectPenaltyAfterFreeFlight,projectPenaltyAfterObservedBounce} from '../penalty-motion-projection.mjs';
import {nativeOamProjectionPart} from '../native-oam-projection.mjs';
const canvas = document.querySelector('#penalty-ball-preview');
const direction = document.querySelector('#penalty-ball-direction');
const play = document.querySelector('#penalty-ball-play');
const slider = document.querySelector('#penalty-ball-frame');
const counter = document.querySelector('#penalty-ball-counter');
const status = document.querySelector('#penalty-ball-status');
const showKeeper = document.querySelector('#penalty-scene-keeper');
const projectionShow = document.querySelector('#penalty-projection-show');
const motionReplay = document.querySelector('#penalty-motion-replay');
const motionReplayStatus = document.querySelector('#penalty-motion-replay-status');
const projectionStatus = document.querySelector('#penalty-projection-status');
const motionStatus = document.querySelector('#penalty-motion-status');
const sceneScore = document.querySelector('#penalty-scene-score');
const ctx = canvas.getContext('2d');
let data, image, projection, motion, exceptions, launches, scores, animation = 0, keepers = new Map(), replayTrajectories = new Map();

function draw() {
  const capture = data.captures.find(item => item.input === direction.value);
  const index = Number(slider.value) - 1;
  const frame = capture.frames[index];
  const available = capture.frames.filter(Boolean).length;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const keeper = keepers.get(capture.input);
  if (showKeeper.checked && keeper?.data.frames[index]) {
    const pose = keeper.data;
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(keeper.image, index * pose.width, 0, pose.width, pose.height, pose.x, pose.y, pose.width, pose.height);
  }
  const trajectory = replayTrajectories.get(capture.input)?.[index];
  const drawFrame = motionReplay.checked ? trajectory : frame;
  if (frame && drawFrame) {
    ctx.imageSmoothingEnabled = false;
    const captureIndex = data.captures.indexOf(capture);
    ctx.drawImage(image, (captureIndex * data.frame_count + index) * 16, 0, 16, 16, drawFrame.x, drawFrame.y, 16, 16);
  }
  motionReplayStatus.textContent = trajectory && frame && trajectory.x===frame.x && trajectory.y===frame.y && trajectory.size===frame.size
    ? `Trajetória contínua calculada: (${trajectory.x}, ${trajectory.y}), coincide com a captura. Parte do vetor inicial da ROM; ramos e flag de gol vêm da gravação.`
    : 'Sem trajetória contínua validada neste quadro.';
  const sample = projection?.captures.find(item => item.input === capture.input && item.graphics_sha256 === capture.graphics_sha256)?.frames[index];
  if (frame && sample) {
    const point = nativeOamProjectionPart(sample);
    const x = point.x & 255, y = point.y & 255;
    const matches = x === frame.x && y === frame.y && sample.size === frame.size && x === sample.oamX && y === sample.oamY;
    projectionStatus.textContent = matches ? `Projeção calculada: (${x}, ${y}) · coincide com a captura · peça ${sample.size}×${sample.size}.` : 'Projeção incompatível com esta captura.';
    if (projectionShow.checked && matches) { ctx.strokeStyle = '#ffe96a'; ctx.lineWidth = 1; ctx.strokeRect(x - 0.5, y - 0.5, sample.size + 1, sample.size + 1); }
  } else projectionStatus.textContent = 'Não há projeção validada para este quadro.';
  const motionSample = motion?.captures.find(item => item.input === capture.input && item.graphics_sha256 === capture.graphics_sha256)?.samples[index];
  if (frame && motionSample) {
    const {before,partX,partY,size,oamX,oamY} = motionSample;
    const calculated = projectPenaltyAfterFreeFlight(before,motion.gravity,{partX,partY,size});
    const matches = calculated.oam.x === frame.x && calculated.oam.y === frame.y && calculated.oam.x === oamX && calculated.oam.y === oamY && size === frame.size;
    motionStatus.textContent = matches ? `Um passo calculado de voo + projeção coincide: (${calculated.oam.x}, ${calculated.oam.y}).` : 'Cálculo de trajetória incompatível com esta captura.';
  } else {
    const exceptional = exceptions?.captures.find(item => item.input === capture.input && item.graphics_sha256 === capture.graphics_sha256)?.cases.find(item => item.index === index);
    if (frame && exceptional) {
      const {before,partX,partY,size,oamX,oamY,kind} = exceptional;
      const calculate = kind === 'ground_bounce' ? projectPenaltyAfterObservedBounce : projectPenaltyAfterFreeFlight;
      const calculated = calculate(before,exceptions.gravity,{partX,partY,size});
      const matches = calculated.oam.x === frame.x && calculated.oam.y === frame.y && calculated.oam.x === oamX && calculated.oam.y === oamY && size === frame.size;
      if (matches && kind === 'goal_crossing') {
        const post=nativePenaltyPostCrossing({flags:exceptional.postFlags,height:exceptional.postHeight,vx:calculated.state.vx,vy:calculated.state.vy,vz:calculated.state.vz});
        const stopped=post.route==='8e25' && post.vx===exceptional.after.vx && post.vy===exceptional.after.vy;
        motionStatus.textContent=stopped ? 'Quadro de gol: posição coincide; parada horizontal compatível com a regra nativa e a flag do quadro seguinte.' : 'Quadro de gol: posição coincide; parada horizontal não validada.';
      } else motionStatus.textContent = matches ? 'Quique observado: posição calculada coincide com a captura.' : 'Cálculo de trajetória incompatível com esta captura.';
    } else motionStatus.textContent = 'Trajetória não validada neste quadro; não há cálculo disponível.';
  }
  const scoring = scores?.find(item => item.input === capture.input && item.graphics_sha256 === capture.graphics_sha256);
  if (scoring) {
    const goal=scoring.replay.steps.at(-1), after=index>=scoring.replay.goalFrameIndex;
    const score=after?goal.after:goal.before;
    sceneScore.textContent = `Placar registrado ${after?'depois':'antes'} do gol: ${score[0]} × ${score[1]}. Transição alinhada à bola; o tempo do placar na imagem não foi validado.`;
  } else sceneScore.textContent='Placar correspondente indisponível.';
  counter.textContent = `${index + 1} / ${data.frame_count}`;
  status.textContent = frame
    ? `${available} de ${data.frame_count} quadros da bola validados. ${showKeeper.checked && keeper ? 'Goleiro e bola pertencem à mesma captura. ' : ''}Ambos os controles receberam a direção.`
    : `Quadro sem associação segura para a bola. ${available} de ${data.frame_count} quadros foram validados; mova o controle para ver outro.`;
}
function stop() { cancelAnimationFrame(animation); animation = 0; }
slider.addEventListener('input', () => { stop(); draw(); });
showKeeper.addEventListener('change', draw);
projectionShow.addEventListener('change', draw);
motionReplay.addEventListener('change', draw);
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
  try {
    const sceneResponse = await fetch('../assets/issd/penalty-scene-observed-local.json');
    if (!sceneResponse.ok) throw new Error('scene unavailable');
    const scene = await sceneResponse.json();
    if (scene.schema !== 'issd-penalty-scene-preview/v1' || scene.frame_count !== 40 || !Array.isArray(scene.captures)) throw new Error('invalid scene');
    for (const capture of data.captures) {
      const pose = scene.captures.find(item => item.input === capture.input && item.graphics_sha256 === capture.graphics_sha256);
      if (!pose || pose.frames?.length !== 40 || !Number.isInteger(pose.width) || !Number.isInteger(pose.height) || pose.width <= 0 || pose.height <= 0) continue;
      const sprite = new Image();
      sprite.src = `../assets/issd/penalty-scene-keeper-${capture.input.toLowerCase()}-local.png`;
      try {
        await sprite.decode();
        if (sprite.naturalWidth === pose.width * 40 && sprite.naturalHeight === pose.height) keepers.set(capture.input, {data:pose, image:sprite});
      } catch { /* Ball preview remains available if a local keeper asset is absent. */ }
    }
    showKeeper.disabled = keepers.size === 0;
  } catch { /* Ball preview remains available without the optional keeper layers. */ }
  try {
    const response = await fetch('../data/issd-penalty-projection-samples.json');
    if (!response.ok) throw new Error('projection unavailable');
    const samples = await response.json();
    if (samples.schema !== 'issd-penalty-projection-samples/v1' || !Array.isArray(samples.captures) || samples.captures.some(item => item.frames?.length !== 40)) throw new Error('invalid projection');
    projection = samples;
    projectionShow.disabled = false;
  } catch { projectionStatus.textContent = 'Projeção capturada indisponível.'; }
  try {
    const response = await fetch('../data/issd-penalty-motion-projection.json');
    if (!response.ok) throw new Error('motion unavailable');
    const samples = await response.json();
    if (samples.schema !== 'issd-penalty-motion-projection/v1' || !Array.isArray(samples.captures) || samples.captures.some(item => item.samples?.length !== 40)) throw new Error('invalid motion');
    motion = samples;
  } catch { motionStatus.textContent = 'Cálculo da trajetória indisponível.'; }
  try {
    const response = await fetch('../data/issd-penalty-motion-exceptions.json');
    if (!response.ok) throw new Error('exceptions unavailable');
    const samples = await response.json();
    if (samples.schema !== 'issd-penalty-motion-exceptions/v1' || !Array.isArray(samples.captures)) throw new Error('invalid exceptions');
    exceptions = samples;
  } catch { /* The free-flight comparison remains available. */ }
  try {
    const response=await fetch('../data/issd-penalty-scene-score.json');
    if(!response.ok)throw new Error('score unavailable');
    const payload=await response.json();
    if(payload.schema!=='issd-penalty-scene-score/v1'||!Array.isArray(payload.captures))throw new Error('invalid score');
    scores=payload.captures.map(item=>({input:item.input,graphics_sha256:item.graphics_sha256,replay:replayPenaltySceneScore(item)}));
  } catch { /* Ball and motion previews remain available. */ }
  try {
    const response=await fetch('../data/issd-penalty-launch-replay.json');
    if(!response.ok)throw new Error('launch unavailable');
    const payload=await response.json();
    if(payload.schema!=='issd-penalty-launch-replay/v1' || !Array.isArray(payload.captures) || payload.gravity!==motion?.gravity)throw new Error('invalid launch');
    launches=payload.captures;
  } catch { /* Captured position previews remain available. */ }
  if (motion && exceptions && launches && motion.gravity===exceptions.gravity) {
    for (const capture of data.captures) {
      try {
        const moves=motion.captures.find(item=>item.input===capture.input && item.graphics_sha256===capture.graphics_sha256);
        const events=exceptions.captures.find(item=>item.input===capture.input && item.graphics_sha256===capture.graphics_sha256);
        const launch=launches.find(item=>item.input===capture.input && item.graphics_sha256===capture.graphics_sha256);
        if(!launch)throw new Error('launch mismatch');
        const frames=replayCapturedPenaltyMotion(moves,events,motion.gravity,launch);
        if(frames.some((item,index)=>item && (!capture.frames[index] || item.x!==capture.frames[index].x || item.y!==capture.frames[index].y || item.size!==capture.frames[index].size))) throw new Error('trajectory mismatch');
        replayTrajectories.set(capture.input,frames);
      } catch { /* Do not substitute an unverified trajectory. */ }
    }
    motionReplay.disabled=replayTrajectories.size===0;
  }
  direction.disabled = slider.disabled = play.disabled = false;
  slider.value = String(data.captures[0].frames.findIndex(Boolean) + 1);
  draw();
} catch {
  status.textContent = 'Amostras locais indisponíveis. Gere a prévia a partir das capturas locais para visualizá-las.';
}
