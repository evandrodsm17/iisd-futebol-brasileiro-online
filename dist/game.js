import { resizeField } from './native-field.mjs';
import { createSimulationClock } from './simulation-clock.mjs';
import { createActionQueue } from './simulation-input.mjs';
const actionQueue = createActionQueue();
const canvas = document.querySelector('#game');
const ctx = canvas.getContext('2d');
const W = canvas.width, H = canvas.height;
const stadiumImage = new Image();
// The USA ROM initialises Open Game with Stadium USA (layout 1).
stadiumImage.src = './assets/issd/stadium/layout-1.png';
let stadiumCrop = { x: 48, y: 80, w: 2688, h: 848 };
const keys = new Set();
const blueScore = document.querySelector('#blue-score');
const redScore = document.querySelector('#red-score');
const blueTeamName = document.querySelector('#blue-team-name');
const redTeamName = document.querySelector('#red-team-name');
const teamFlags = [document.querySelector('#blue-team-flag'), document.querySelector('#red-team-flag')];
const clock = document.querySelector('#clock');
const toast = document.querySelector('#goal-toast');
const blueTeamSelect = document.querySelector('#blue-team-select');
const redTeamSelect = document.querySelector('#red-team-select');
const blueKitSelect = document.querySelector('#blue-kit-select');
const redKitSelect = document.querySelector('#red-kit-select');
const stadiumSelect = document.querySelector('#stadium-select');
const matchOptions = document.querySelector('#match-options');
const matchOptionsNotice = document.querySelector('#match-options-notice');
const kitNotice = document.querySelector('#kit-notice');
const lineups = document.querySelector('#lineups');
const catalogStatus = document.querySelector('#catalog-status');
const modeMenu = document.querySelector('#mode-menu');
const modeDescription = document.querySelector('#mode-description');
const modeNotice = document.querySelector('#mode-notice');
const confirmMode = document.querySelector('#confirm-mode');
const startMatch = document.querySelector('#start-match');
const returnMenu = document.querySelector('#return-menu');

// The player sheets are decoded from the local ISS Deluxe ROM extraction.
// Their artwork is shared; their 16-colour OBJ palettes are team/kit-specific.
// Direction used by the Canvas is clockwise: up, up-right, right, down-right,
// down, down-left, left, up-left.  The ROM locomotion pointer tables use a
// different order.  Keep the conversion explicit: the PNG suffix is the ROM
// table index, never the Canvas direction index.
const romSheetIndexByScreenDirection = [6, 7, 0, 1, 2, 3, 4, 5];
const fallbackByRomSheetIndex = ['side', 'diagonaldown', 'down', 'diagonaldown', 'side', 'diagonalup', 'up', 'diagonalup'];
const playerSheetCache = new Map();
// Every catalogue team has an exported OAM sheet for both ROM kit palettes.
// Keep the membership explicit so a missing future export falls back to the
// older generic sheet instead of requesting an invented asset path.
const oamMotionTeams = new Set(Array.from({ length: 36 }, (_, teamId) => teamId));
function playerSheet(team, direction) {
  const teamId = selectedTeamIds[team];
  const kit = selectedKits[team];
  const key = `${teamId}/${kit}/${direction.motion ?? direction}/${direction.index ?? direction}`;
  if (!playerSheetCache.has(key)) {
    const image = new Image();
    // There is no validated idle sheet yet. Keep the still fallback isolated
    // from the future $82:D6DB composition instead of requesting an invented
    // asset path.
    const sourceMotion = direction.motion === 'idle' ? 'walking' : (direction.motion ?? direction);
    image.src = oamMotionTeams.has(teamId)
      ? `./assets/issd/oam-teams/${String(teamId).padStart(2, '0')}/${kit}/${sourceMotion}-${direction.index}.png`
      : `./assets/issd/teams/${String(teamId).padStart(2, '0')}/${kit}/issd-player-${direction.fallback}.png`;
    playerSheetCache.set(key, image);
  }
  return playerSheetCache.get(key);
}

const field = { x: 65, y: 52, w: 1150, h: 523, goalW: 62, goalH: 168 };
let fieldMidX = field.x + field.w / 2;
let fieldMidY = field.y + field.h / 2;
let score = [0, 0], elapsed = 0, last = performance.now(), resetAt = 0;
let simulationTick = 0;
function simulationNow() { return simulationTick * (1000 / 60); }
let matchClockBcd = 0x0500, matchClockFrames = 0;
let clockInitialBcdByGameTime = [0x0300, 0x0500, 0x0700];
function fromBcd(byte) { return ((byte >> 4) * 10) + (byte & 0x0f); }
function renderClock() {
  const minutes = fromBcd((matchClockBcd >> 8) & 0xff);
  const seconds = fromBcd(matchClockBcd & 0xff);
  clock.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}
function initializeMatchClock() {
  // CODE_83:B02C clears $00A8, selecting the first (zero) table at A4:A4926F.
  // Restarts keep this value; phase transitions remain blocked on further ROM work.
  const setting = selectedMatchSettings.game_time;
  matchClockBcd = clockInitialBcdByGameTime[setting] ?? clockInitialBcdByGameTime[1];
  matchClockFrames = 0;
  renderClock();
}
const player = { x: 490, y: 370, homeX: 490, homeY: 370, vx: 0, vy: 0, team: 0, controlled: true, number: 10 };
// The ROM models the ball as an independent fixed-point actor.  These Canvas
// values are a navigable placeholder only; they are not yet a recovered ROM
// trajectory, collision or bounce implementation.
const ball = { x: 515, y: 385, z: 0, vx: 0, vy: 0, vz: 0, gravity: .125, owner: player, r: 9 };
// Simulation radii stay in world units. Rendering uses the same source-space
// scale for every actor so a player cannot visually dwarf a goal from the ROM
// stadium scene.
const actorVisual = {
  player: { w: 28, h: 38, offsetX: -14, offsetY: -29, shadowX: 10, shadowY: 4, controlRing: 11 },
  ball: { r: 5.5, patch: 1.8, shadowX: 6, shadowY: 2.5 },
};
let controlled = player, lastKick = 0, lastTackle = 0, lastTouchTeam = 0;

// The native match buffer is 256×224. It is presented as a 4:3 image on a
// television, so the reference profile keeps that window centred in the web
// canvas. "widescreen" is deliberately isolated as an enhancement: it must
// never become the source for match rules or camera calibration.
const cameraProfiles = {
  reference: {
    viewport: { x: (W - H * 4 / 3) / 2, y: 0, w: H * 4 / 3, h: H },
    zoom: 1.58,
    followRate: 5.5,
  },
  widescreen: {
    viewport: { x: 0, y: 0, w: W, h: H },
    zoom: 1.35,
    followRate: 5.5,
  },
};
let cameraMode = 'reference';
const camera = { x: fieldMidX, y: fieldMidY, zoom: cameraProfiles.reference.zoom };

const base = [
  [205, 190],[285, 480],[390, 250],[390, 520],[520, 330],[640, 200],[670, 510],[790, 310],[850, 480],[1000, 270],[1040, 450],
  [1010, 190],[930, 480],[830, 250],[820, 525],[700, 335],[570, 205],[570, 515],[445, 300],[385, 475],[260, 265],[210, 455]
];
const players = base.map((p, i) => i === 0 ? player : ({ x:p[0], y:p[1], homeX:p[0], homeY:p[1], team:i < 11 ? 0 : 1, number:(i % 11)+1, controlled:false, phase:i*.7 }));
let catalog = null;
let selectedTeamIds = [30, 2]; // Brazil × England: real ROM team IDs.
let selectedKits = ['home', 'away'];
let selectedStadiumId = 1;
const selectedMatchSettings = { game_level: 2, game_time: 1, fouls: 0, yellow_cards: 0, offside: 0, overtime: 0, time_of_day: 0, weather: 1, referee: 0 };
let stadiumLayouts = [];
let selectedMode = 'open-game';
let gameStarted = false;
const flagIds = {
  Italy:'italy', Holland:'holland', England:'england', Norway:'norway', Spain:'spain', Ireland:'ireland', Portugal:'portugal', Denmark:'denmark', Germany:'germany', France:'france', Belgium:'belgium', Sweden:'sweden', Romania:'romania', Bulgaria:'bulgaria', Russia:'russia', Swiss:'swiss', Greece:'greece', Croatia:'croatia', Austria:'austria', Wales:'wales', Scotland:'scotland', 'N.Ireland':'northern-ireland', 'Czech Rep.':'czech-republic', Poland:'poland', Japan:'japan', 'S.Korea':'south-korea', Turkey:'turkey', Nigeria:'nigeria', Cameroon:'cameroon', Morocco:'morocco', Brazil:'brazil', Argentina:'argentina', Columbia:'columbia', Mexico:'mexico', 'U.S.A':'usa', Uruguay:'uruguay',
};
// These role bases are the three lines used by ISSD.  The per-player depth
// and width values come directly from each team's 31-byte formation record.
// The scales are a world projection; camera profiles only decide how much of
// that same world is visible.
const formationRoleDepth = { 1: 26, 5: 20, 2: 0, 6: -6, 3: -28 };
const formationProjection = { depth: 8, width: 6.6 };
const modeDetails = {
  'open-game': ['OPEN GAME', 'Partida de exibição com seleção de equipes e regras.', true],
  'international-cup': ['INTERNATIONAL CUP', 'Torneio internacional da ROM. A estrutura de fases será conectada depois da partida-base.', false],
  'world-series': ['WORLD SERIES', 'Temporada longa contra as principais seleções. O calendário original ainda está sendo modelado.', false],
  training: ['TRAINING', 'Treinos de drible, chute, escanteio e defesa. Rota identificada, conteúdo ainda não iniciado.', false],
  scenario: ['SCENARIO', 'Cenários históricos com condição de recuperação. Dados de cada cenário ainda serão extraídos.', false],
  'penalty-kick': ['PENALTY KICK', 'Competição de pênaltis. Rota identificada, regras de goleiro ainda pendentes.', false],
  options: ['OPTIONS', 'Tempo, nível, faltas e áudio: serão incorporados à configuração de partida.', false],
  password: ['PASSWORD', 'Sistema de senha da campanha. Será tratado junto com os modos de torneio.', false],
};

function optionLabel(team) { return `${String(team.id + 1).padStart(2, '0')} · ${team.name}`; }
function applySelectedStadium() {
  const stadium = stadiumLayouts.find(layout => layout.id === selectedStadiumId);
  if (!stadium) return;
  resizeField(field, selectedStadiumId, [...players, ball, camera]);
  fieldMidX = field.x + field.w / 2;
  fieldMidY = field.y + field.h / 2;
  stadiumCrop = stadium.crop;
  stadiumImage.src = stadium.asset;
  stadiumSelect.value = String(stadium.id);
}
async function loadStadiumLayouts() {
  try {
    const response = await fetch('./data/issd-stadium-layouts.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    if (!Array.isArray(payload.layouts) || payload.layouts.length !== 8) throw new Error('manifesto de estádio inválido');
    stadiumLayouts = payload.layouts;
    stadiumSelect.replaceChildren(...stadiumLayouts.map(layout => new Option(layout.name.toUpperCase(), layout.id, false, layout.id === selectedStadiumId)));
    stadiumSelect.addEventListener('change', () => { selectedStadiumId = Number(stadiumSelect.value); applySelectedStadium(); });
    applySelectedStadium();
  } catch (error) {
    stadiumSelect.disabled = true;
    console.error('ISSD stadium manifest failed to load', error);
  }
}
const settingLabels = { game_level:'NÍVEL', game_time:'TEMPO', fouls:'FALTAS', yellow_cards:'CARTÕES', offside:'IMPEDIMENTO', overtime:'PRORROGAÇÃO', time_of_day:'HORÁRIO', weather:'CLIMA', referee:'ÁRBITRO' };
function settingEntries(setting) { return Array.isArray(setting.values) ? setting.values.map(value=>[value,String(value)]) : Object.entries(setting.values); }
async function loadMatchOptions() {
  try {
    const response = await fetch('./data/issd-match-settings.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    matchOptions.replaceChildren(...Object.entries(settingLabels).map(([key,label]) => {
      const select = document.createElement('select'); select.setAttribute('aria-label', label);
      select.replaceChildren(...settingEntries(payload.settings[key]).map(([value,text]) => new Option(text, value, false, Number(value) === selectedMatchSettings[key])));
      select.addEventListener('change', () => { selectedMatchSettings[key] = Number(select.value); });
      const wrapper = document.createElement('label'); wrapper.append(label, select); return wrapper;
    }));
    matchOptionsNotice.textContent = 'OPÇÕES DA ROM REGISTRADAS — EFEITOS DE REGRAS AINDA DEPENDEM DO MOTOR FIEL.';
  } catch (error) { matchOptions.hidden = true; matchOptionsNotice.textContent = 'OPÇÕES DA ROM INDISPONÍVEIS.'; console.error('ISSD match settings failed to load', error); }
}
function rosterTeam(side) { return catalog?.teams.find(team => team.id === selectedTeamIds[side]) ?? null; }
function rgb(hex) { return [1, 3, 5].map(index => Number.parseInt(hex.slice(index, index + 2), 16)); }
function kitDistance(a, b) { return Math.min(...a.shirt.slice(0, 3).map(left => Math.min(...b.shirt.slice(0, 3).map(right => Math.hypot(...rgb(left).map((value, index) => value - rgb(right)[index])))))); }
function suggestKits(teams) {
  const home = teams[0]?.kit?.home, away = teams[1]?.kit?.away;
  if (!home || !away || !teams[1]?.kit?.home) return ['home', 'away'];
  return kitDistance(home, teams[1].kit.home) < kitDistance(home, away) ? ['home', 'away'] : ['home', 'home'];
}
function formationHome(team, side, playerIndex) {
  const direction = side === 0 ? 1 : -1; // blue attacks right; red attacks left.
  if (playerIndex === 0) return { x: side === 0 ? field.x + 90 : field.x + field.w - 90, y: fieldMidY, role: 'GK' };
  const slot = team.formation?.outfield_slots?.[playerIndex - 1];
  if (!slot) return { x: fieldMidX, y: fieldMidY, role: 'unknown' };
  const lineDepth = (formationRoleDepth[slot.role_code] ?? 0) + slot.depth;
  return {
    x: fieldMidX - direction * lineDepth * formationProjection.depth,
    y: fieldMidY + slot.width * formationProjection.width,
    role: slot.role_code,
  };
}
function applyFormation(team, side) {
  players.filter(fieldPlayer => fieldPlayer.team === side).forEach((fieldPlayer, index) => {
    const home = formationHome(team, side, index);
    fieldPlayer.homeX = home.x;
    fieldPlayer.homeY = home.y;
    fieldPlayer.formationRole = home.role;
  });
}
function renderLineup(team, side) {
  if (!team) return '';
  const colour = side ? 'VERMELHO' : 'AZUL';
  const kit = team.kit?.[selectedKits[side]];
  const swatches = kit ? `<i class="kit-swatches" aria-label="Cores do uniforme">${[...kit.shirt, ...kit.shorts, ...kit.socks].map(hex => `<b style="background:${hex}"></b>`).join('')}</i>` : '';
  const starters = team.players.slice(0, 11);
  return `<article class="lineup"><h3>${team.name}<span>${colour} · ${team.formation.label ?? 'FORM.'}${swatches}</span></h3><ol>${starters.map(member => `<li><b>${String(member.shirt_number).padStart(2, '0')}</b><span title="${member.name.trim()}">${member.name.trim()}</span><em>${member.position}</em></li>`).join('')}</ol></article>`;
}
function applySelectedTeams() {
  if (!catalog) return;
  const teams = [rosterTeam(0), rosterTeam(1)];
  if (teams.some(team => !team)) return;
  [blueKitSelect, redKitSelect].forEach((select, side) => {
    const options = Object.keys(teams[side].kit ?? {});
    select.replaceChildren(...options.map(kind => new Option(kind === 'home' ? 'MANDANTE' : 'VISITANTE', kind, false, kind === selectedKits[side])));
    select.value = selectedKits[side];
  });
  const distance = kitDistance(teams[0].kit[selectedKits[0]], teams[1].kit[selectedKits[1]]);
  kitNotice.textContent = distance < 80 ? 'UNIFORMES PRÓXIMOS — SUGESTÃO: ALTERE O VISITANTE.' : 'UNIFORMES COM BOA SEPARAÇÃO DE CORES.';
  [blueTeamName.textContent, redTeamName.textContent] = teams.map(team => team.name.toUpperCase());
  teamFlags.forEach((flag, side) => {
    const team = teams[side];
    const flagId = flagIds[team.name];
    flag.src = `./assets/issd/flags/${flagId}.png`;
    flag.alt = `Bandeira da seleção ${team.name}`;
  });
  document.querySelectorAll('.crest').forEach((crest, side) => {
    const kit = teams[side].kit?.[selectedKits[side]];
    if (!kit) return;
    crest.style.color = kit.shirt[0];
    crest.style.backgroundColor = kit.shirt[2];
  });
  players.forEach((fieldPlayer, index) => {
    const side = fieldPlayer.team;
    const rosterMember = teams[side].players[index % 11];
    fieldPlayer.number = rosterMember.shirt_number;
    fieldPlayer.roster = rosterMember;
    fieldPlayer.kit = teams[side].kit?.[selectedKits[side]] ?? null;
  });
  teams.forEach(applyFormation);
  lineups.innerHTML = teams.map(renderLineup).join('');
  reset();
}
async function loadCatalog() {
  try {
    const response = await fetch('./data/issd-rom-catalog.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    catalog = await response.json();
    if (!Array.isArray(catalog.teams) || catalog.teams.length !== 36) throw new Error('catálogo inválido');
    [blueTeamSelect, redTeamSelect].forEach((select, side) => {
      select.replaceChildren(...catalog.teams.map(team => new Option(optionLabel(team), team.id, false, team.id === selectedTeamIds[side])));
      select.addEventListener('change', () => {
        selectedTeamIds[side] = Number(select.value);
        if (selectedTeamIds[0] === selectedTeamIds[1]) {
          selectedTeamIds[1 - side] = (selectedTeamIds[side] + 1) % catalog.teams.length;
          (side ? blueTeamSelect : redTeamSelect).value = selectedTeamIds[1 - side];
        }
        applySelectedTeams();
      });
    });
    [blueKitSelect, redKitSelect].forEach((select, side) => select.addEventListener('change', () => { selectedKits[side] = select.value; applySelectedTeams(); }));
    selectedKits = suggestKits([rosterTeam(0), rosterTeam(1)]);
    catalogStatus.textContent = `${catalog.teams.length} seleções · ${catalog.teams.reduce((sum, team) => sum + team.players.length, 0)} jogadores · ROM USA`;
    applySelectedTeams();
  } catch (error) {
    catalogStatus.textContent = 'Catálogo indisponível — usando elenco temporário.';
    console.error('ISSD catalog failed to load', error);
  }
}
loadCatalog();
loadStadiumLayouts();
loadMatchOptions();
async function loadNativeMatchClock() {
  try {
    const response = await fetch('./data/issd-match-clock.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const values = (await response.json())?.facts?.initial_countdown_bcd?.when_00a8_is_zero;
    if (!Array.isArray(values) || values.length < 3 || values.slice(0, 3).some(value => !/^[0-9A-F]{4}$/.test(value))) throw new Error('tabela inicial BCD inválida');
    clockInitialBcdByGameTime = values.slice(0, 3).map(value => Number.parseInt(value, 16));
  } catch (error) {
    console.warn('ISSD match clock manifest unavailable; using validated first-phase fallback', error);
  }
}
loadNativeMatchClock();

function chooseMode(mode) {
  selectedMode = mode;
  const [label, description, ready] = modeDetails[mode];
  document.querySelectorAll('.mode-choice').forEach(button => button.classList.toggle('selected', button.dataset.mode === mode));
  modeDescription.textContent = description;
  confirmMode.textContent = ready ? `CONFIRMAR ${label}` : `${label} · EM MAPEAMENTO`;
  confirmMode.disabled = !ready;
  modeNotice.textContent = ready
    ? 'Open Game segue para a seleção de equipes da ROM e preparação da partida.'
    : 'Esta rota pertence ao fluxo original, mas não abre um modo incompleto antes de termos suas regras e dados validados.';
}
function openGameSetup() {
  if (selectedMode !== 'open-game') return;
  gameStarted = false;
  modeMenu.classList.add('hidden');
  toast.textContent = 'SELECIONE AS EQUIPES';
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 700);
}
function beginMatch() {
  if (!catalog) return;
  actionQueue.clear();
  keys.clear();
  simulationTick = 0;
  elapsed = 0;
  lastKick = lastTackle = -Infinity;
  gameStarted = true;
  // CODE_83:B02C also clears both scores before the kickoff sequence.
  score = [0, 0];
  blueScore.textContent = '0';
  redScore.textContent = '0';
  initializeMatchClock();
  reset();
  toast.textContent = 'KICK OFF';
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 700);
}
document.querySelectorAll('.mode-choice').forEach(button => button.addEventListener('click', () => chooseMode(button.dataset.mode)));
confirmMode.addEventListener('click', openGameSetup);
startMatch.addEventListener('click', beginMatch);
returnMenu.addEventListener('click', () => { gameStarted = false; actionQueue.clear(); keys.clear(); modeMenu.classList.remove('hidden'); });

addEventListener('keydown', e => { if(['KeyW','KeyA','KeyS','KeyD','ShiftLeft','ShiftRight','KeyQ','KeyX','KeyF','Space','KeyR'].includes(e.code)) e.preventDefault(); keys.add(e.code); if(gameStarted) actionQueue.push(e.code, e.repeat); });
addEventListener('keyup', e => keys.delete(e.code));

function reset() { players.forEach((p,i)=>{p.x=p.homeX ?? 490;p.y=p.homeY ?? fieldMidY;p.vx=p.vy=0;p.facingDirection=p.team===0?2:6;}); controlled=player; players.forEach(p=>p.controlled=p===controlled); ball.x=controlled.x+12; ball.y=controlled.y+5; ball.z=ball.vx=ball.vy=ball.vz=0; ball.gravity=.125; ball.owner=controlled; snapCameraToBall(); resetAt=simulationNow()+1000; }
function switchPlayer() { const candidates=players.filter(p=>p.team===0); const next=candidates.reduce((best,p)=>Math.hypot(p.x-ball.x,p.y-ball.y)<Math.hypot(best.x-ball.x,best.y-ball.y)?p:best,candidates[0]); controlled=next;players.forEach(p=>p.controlled=p===controlled); }
function shoot() { if(ball.owner !== controlled || simulationNow() < resetAt) return; const direction=controlled.team===0?1:-1; lastTouchTeam=controlled.team; ball.owner=null; ball.vx=direction*(7+Math.abs(controlled.vx)*.35); ball.vy=controlled.vy*.42; ball.vz=-4.5; ball.gravity=.125; lastKick=simulationNow(); }
function pass() { if(ball.owner !== controlled || simulationNow() < resetAt) return; const direction=controlled.team===0?1:-1; const options=players.filter(p=>p.team===controlled.team&&p!==controlled); const target=options.sort((a,b)=>{const av=(a.x-controlled.x)*direction, bv=(b.x-controlled.x)*direction;return Math.abs(av-125)-Math.abs(bv-125);})[0]; const dx=target.x-controlled.x,dy=target.y-controlled.y,mag=Math.hypot(dx,dy)||1; lastTouchTeam=controlled.team; ball.owner=null;ball.vx=dx/mag*5.8;ball.vy=dy/mag*5.8;ball.vz=-1.5;ball.gravity=.09375;lastKick=simulationNow(); }
function press() { if(simulationNow()-lastTackle<420)return;lastTackle=simulationNow();const rival=players.filter(p=>p.team!==controlled.team).reduce((best,p)=>Math.hypot(p.x-controlled.x,p.y-controlled.y)<Math.hypot(best.x-controlled.x,best.y-controlled.y)?p:players.find(q=>q.team!==controlled.team)); if(ball.owner===rival&&Math.hypot(rival.x-controlled.x,rival.y-controlled.y)<32){ball.owner=null;ball.vx=(rival.x-controlled.x)*.27;ball.vy=(rival.y-controlled.y)*.27;lastKick=simulationNow();}}
function steer(p, tx, ty, speed, dt) { const dx=tx-p.x,dy=ty-p.y,mag=Math.hypot(dx,dy)||1;p.vx+=(dx/mag*speed-p.vx)*Math.min(1,dt*4.5);p.vy+=(dy/mag*speed-p.vy)*Math.min(1,dt*4.5);p.x+=p.vx*dt*60;p.y+=p.vy*dt*60; }
function restart(kind, x, y, team) { const receiver=players.filter(p=>p.team===team).reduce((best,p)=>Math.hypot(p.x-x,p.y-y)<Math.hypot(best.x-x,best.y-y)?p:players.find(q=>q.team===team)); receiver.x=x;receiver.y=y;ball.x=x;ball.y=y;ball.z=ball.vx=ball.vy=ball.vz=0;ball.owner=receiver;lastTouchTeam=team;toast.textContent=kind;toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),700); }
function activeCameraProfile() { return cameraProfiles[cameraMode]; }
function cameraTarget() {
  const { viewport, zoom } = activeCameraProfile();
  const halfW = viewport.w / (2 * zoom), halfH = Math.min(field.h / 2, viewport.h / (2 * zoom));
  const minX = field.x + halfW, maxX = field.x + field.w - halfW;
  const minY = field.y + halfH, maxY = field.y + field.h - halfH;
  return {
    x: Math.max(minX, Math.min(maxX, ball.x)),
    y: Math.max(minY, Math.min(maxY, ball.y)),
  };
}
function snapCameraToBall() {
  const profile = activeCameraProfile();
  const target = cameraTarget();
  camera.zoom = profile.zoom;
  camera.x = target.x;
  camera.y = target.y;
}
function updateCamera(dt) {
  const profile = activeCameraProfile();
  const target = cameraTarget();
  camera.zoom = profile.zoom;
  const easing = Math.min(1, dt * profile.followRate);
  camera.x += (target.x - camera.x) * easing;
  camera.y += (target.y - camera.y) * easing;
}
function update(dt) {
  if (!gameStarted) return;
  simulationTick++;
  actionQueue.drain(code => {
    if (code === 'KeyR') reset();
    else if (code === 'KeyQ') switchPlayer();
    else if (code === 'Space') shoot();
    else if (code === 'KeyX') pass();
    else if (code === 'KeyF') press();
  });
  elapsed += dt;
  // CODE_A4:A49401 advances once per 60 eligible frames and delegates the
  // decimal decrement to A493CC. Browser phase/restart blockers are not
  // recovered yet, so every in-play browser frame is currently eligible.
  if (matchClockBcd > 0) {
    matchClockFrames += dt * 60;
    while (matchClockFrames >= 60 && matchClockBcd > 0) {
      matchClockBcd = (matchClockBcd & 0x00ff) ? matchClockBcd - 0x0001 : matchClockBcd - 0x0041;
      matchClockFrames -= 60;
    }
  }
  renderClock();
  let ax=(keys.has('KeyD')?1:0)-(keys.has('KeyA')?1:0), ay=(keys.has('KeyS')?1:0)-(keys.has('KeyW')?1:0); const len=Math.hypot(ax,ay)||1; ax/=len; ay/=len;
  // Passive ROM capture: directional masks select heading; held $4000 selects
  // $82:CF9F running while unmodified movement normally uses $82:CEF8 walking.
  // These Canvas magnitudes are deliberately provisional until native units map.
  const running = keys.has('ShiftLeft') || keys.has('ShiftRight');
  const targetSpeed = running ? 2 : 1.25;
  const response = running ? 6 : 4.5;
  controlled.vx += (ax*targetSpeed-controlled.vx)*Math.min(1,dt*response); controlled.vy += (ay*targetSpeed-controlled.vy)*Math.min(1,dt*response); controlled.x += controlled.vx*dt*60; controlled.y += controlled.vy*dt*60;
  players.forEach(p => { if(p===controlled)return; const own=ball.owner===p; const chaser=players.filter(q=>q.team===p.team).sort((a,b)=>Math.hypot(a.x-ball.x,a.y-ball.y)-Math.hypot(b.x-ball.x,b.y-ball.y))[0]===p; const attacking=ball.owner?.team===p.team; let tx=p.homeX,ty=p.homeY; if(own){tx=p.team===0?field.x+field.w-60:field.x+60;ty=fieldMidY;} else if(chaser&&!attacking){tx=ball.x;ty=ball.y;} else if(attacking){tx=p.homeX+(p.team===0?35:-35);ty=p.homeY;} steer(p,tx,ty,chaser?2.4:1.7,dt); });
  players.forEach(p=>{p.x=Math.max(field.x+15,Math.min(field.x+field.w-15,p.x));p.y=Math.max(field.y+15,Math.min(field.y+field.h-15,p.y));});
  // Temporary possession model.  The recovered collision dispatch will replace
  // this proximity shortcut before the browser mechanics are considered final.
  if(ball.owner) {
    const carrier = ball.owner;
    lastTouchTeam = carrier.team;
    const distance = Math.hypot(carrier.x - ball.x, carrier.y - ball.y);
    if(distance >= 24 || ball.z < 0) {
      ball.owner = null;
    } else if(distance < 16 && Math.hypot(carrier.vx, carrier.vy) > .25) {
      const speed = Math.hypot(carrier.vx, carrier.vy);
      const headingX = speed > .25 ? carrier.vx / speed : (carrier.team === 0 ? 1 : -1);
      const headingY = speed > .25 ? carrier.vy / speed : 0;
      const touchSpeed = 3.2 + Math.min(.6, speed * .12);
      ball.vx = headingX * touchSpeed;
      ball.vy = headingY * touchSpeed;
    }
  }

  const frames = dt * 60;
  ball.x += ball.vx * frames;
  ball.y += ball.vy * frames;
  ball.z += ball.vz * frames;
  if(ball.z < 0) {
    ball.vz += ball.gravity * frames;
  } else {
    if(ball.vz > .25) {
      ball.z = 0;
      ball.vz *= -.75; // placeholder restitution; ROM value is still pending
    } else {
      ball.z = ball.vz = 0;
      const speed = Math.hypot(ball.vx, ball.vy);
      const nextSpeed = Math.max(0, speed - .03125 * frames); // rolling friction / frame
      if(speed) { ball.vx *= nextSpeed / speed; ball.vy *= nextSpeed / speed; }
    }
  }
  const goalTop=fieldMidY-field.goalH/2,goalBottom=fieldMidY+field.goalH/2;
  if(ball.x>field.x+field.w+20 && ball.y>goalTop && ball.y<goalBottom) goal(0);
  else if(ball.x<field.x-20 && ball.y>goalTop && ball.y<goalBottom) goal(1);
  else if(ball.y<field.y-16||ball.y>field.y+field.h+16) restart('LATERAL',Math.max(field.x+28,Math.min(field.x+field.w-28,ball.x)),ball.y<field.y?field.y+12:field.y+field.h-12,lastTouchTeam===0?1:0);
  else if(ball.x<field.x-16||ball.x>field.x+field.w+16){const exitsRight=ball.x>field.x+field.w;const defending=exitsRight?1:0;const corner=lastTouchTeam===defending;restart(corner?'ESCANTEIO':'TIRO DE META',exitsRight?field.x+field.w-18:field.x+18,ball.y<fieldMidY?field.y+18:field.y+field.h-18,corner?lastTouchTeam===0?1:0:defending);}
  else if(!ball.owner && ball.z === 0 && simulationNow()-lastKick>260){const nearest=players.reduce((best,p)=>Math.hypot(p.x-ball.x,p.y-ball.y)<Math.hypot(best.x-ball.x,best.y-ball.y)?p:best,players[0]);if(Math.hypot(nearest.x-ball.x,nearest.y-ball.y)<16)ball.owner=nearest;}
  updateCamera(dt);
}
function goal(team) { score[team]++; blueScore.textContent=score[0];redScore.textContent=score[1]; toast.textContent='GOOOL!';toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),1100);reset(); }
function line(x1,y1,x2,y2,w=3) {ctx.lineWidth=w;ctx.strokeStyle='#eff6c9cc';ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();}
function draw() {
  ctx.clearRect(0,0,W,H);ctx.fillStyle='#062b23';ctx.fillRect(0,0,W,H);
  const viewport = activeCameraProfile().viewport;
  ctx.save();
  ctx.beginPath();
  ctx.rect(viewport.x, viewport.y, viewport.w, viewport.h);
  ctx.clip();
  ctx.translate(viewport.x + viewport.w / 2, viewport.y + viewport.h / 2);
  ctx.scale(camera.zoom, camera.zoom);
  ctx.translate(-camera.x, -camera.y);
  if(stadiumImage.complete && stadiumImage.naturalWidth) {
    // Crop only the non-transparent source scene, then project it through the
    // active camera profile. The source still comes entirely from ROM tilemaps.
    ctx.imageSmoothingEnabled=false;
    ctx.drawImage(stadiumImage, stadiumCrop.x, stadiumCrop.y, stadiumCrop.w, stadiumCrop.h, field.x, field.y, field.w, field.h);
  } else {
    ctx.fillStyle='#197045';ctx.fillRect(field.x,field.y,field.w,field.h);
    for(let i=0;i<10;i++){ctx.fillStyle=i%2?'#237b4a':'#1d7445';ctx.fillRect(field.x+i*field.w/10,field.y,field.w/10,field.h);}
    ctx.strokeStyle='#eff6c9cc';ctx.lineWidth=3;ctx.strokeRect(field.x,field.y,field.w,field.h);line(W/2,field.y,W/2,field.y+field.h);ctx.beginPath();ctx.arc(W/2,fieldMidY,78,0,Math.PI*2);ctx.stroke();ctx.beginPath();ctx.arc(W/2,fieldMidY,4,0,Math.PI*2);ctx.fillStyle='#eff6c9';ctx.fill();
    [[field.x,1],[field.x+field.w,-1]].forEach(([x,d])=>{ctx.strokeStyle='#ecf1d0bb';ctx.strokeRect(x-(d===1?0:92),fieldMidY-115,92,230);ctx.strokeRect(x-(d===1?0:42),fieldMidY-56,42,112);ctx.strokeStyle='#cfd7c066';ctx.strokeRect(x-(d===1?13:105),fieldMidY-field.goalH/2,18,field.goalH);});
  }
  players.forEach(drawPlayer); drawBall();
  ctx.restore();
}
function playerDirection(p){const x=p.vx||0,y=p.vy||0,speed=Math.hypot(x,y),motion=speed<.25?'idle':speed<1.85?'walking':'running';let screenIndex;if(speed<.25){screenIndex=p.facingDirection ?? (p.team===0?2:6);}else if(Math.abs(x)>Math.abs(y)*1.6)screenIndex=x>0?2:6;else if(Math.abs(y)>Math.abs(x)*1.6)screenIndex=y<0?0:4;else if(y<0)screenIndex=x>0?1:7;else screenIndex=x>0?3:5;p.facingDirection=screenIndex;const index=romSheetIndexByScreenDirection[screenIndex];return {index,motion,fallback:fallbackByRomSheetIndex[index]};}
// Decoded from $82:CEF8/$82:CF9F. These are SNES frame ticks (60 Hz), not
// presentation rates chosen by the browser.
let locomotionTiming = { walking: Array(10).fill(3), running: [4, 3, 3, 3, 4, 3, 3, 3] };
function nativeLocomotionTiming(payload) {
  const walking = payload?.cycles?.walking?.timing;
  const running = payload?.cycles?.running?.timing;
  if (walking?.kind !== 'constant' || walking.ticks !== 3 || !Array.isArray(running?.ticks)) return null;
  const walkingFrames = payload.cycles.walking.directions?.[0]?.descriptors?.length;
  if (walkingFrames !== 10 || running.ticks.length !== 8 || running.ticks.some(tick => !Number.isInteger(tick) || tick <= 0)) return null;
  return { walking: Array(walkingFrames).fill(walking.ticks), running: [...running.ticks] };
}
async function loadNativeLocomotionTiming() {
  try {
    const response = await fetch('./data/issd-locomotion-scripts.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const timing = nativeLocomotionTiming(await response.json());
    if (!timing) throw new Error('cadência nativa inválida');
    locomotionTiming = timing;
  } catch (error) {
    // The fallback is the same ROM-validated CEF8/CF9F timing above; it keeps
    // offline previews usable without replacing native data with guessed FPS.
    console.warn('ISSD locomotion timing manifest unavailable; using validated fallback', error);
  }
}
loadNativeLocomotionTiming();
function locomotionFrame(motion, seconds, phase = 0) { if(motion === 'idle') return 0; const durations=locomotionTiming[motion],cycle=durations.reduce((sum,value)=>sum+value,0);let tick=(Math.floor((seconds+phase)*60)%cycle+cycle)%cycle;for(let index=0;index<durations.length;index+=1){if(tick<durations[index])return index;tick-=durations[index];}return 0; }
function drawPlayer(p) { const c=p.team?'#d94b3f':'#2787d4',direction=playerDirection(p),sheet=playerSheet(p.team,direction),visual=actorVisual.player,oam=oamMotionTeams.has(selectedTeamIds[p.team]);ctx.save();ctx.translate(p.x,p.y);ctx.fillStyle='#0005';ctx.beginPath();ctx.ellipse(0,8,visual.shadowX,visual.shadowY,0,0,Math.PI*2);ctx.fill();if(sheet.complete&&sheet.naturalWidth){const timingMotion=direction.motion==='idle'?'walking':direction.motion;const frames=locomotionTiming[timingMotion].length;const frame=locomotionFrame(direction.motion,elapsed,p.phase||0),sourceW=oam?sheet.naturalWidth/frames:48,sourceH=sheet.naturalHeight;const targetH=visual.h,targetW=oam?sourceW*targetH/sourceH:visual.w,targetX=oam?-targetW/2:visual.offsetX;ctx.imageSmoothingEnabled=false;ctx.drawImage(sheet,frame*sourceW,0,sourceW,sourceH,targetX,visual.offsetY,targetW,targetH);}else{ctx.fillStyle='#f1b37e';ctx.beginPath();ctx.arc(0,-7,4.5,0,Math.PI*2);ctx.fill();ctx.fillStyle=c;ctx.fillRect(-5,-1,10,12);ctx.fillStyle='#e8eff0';ctx.font='700 8px DM Mono';ctx.textAlign='center';ctx.fillText(p.number,0,8);ctx.fillStyle='#142d3c';ctx.fillRect(-4,11,3,6);ctx.fillRect(1,11,3,6);}if(p.controlled){ctx.strokeStyle='#f9da62';ctx.lineWidth=2;ctx.beginPath();ctx.arc(0,4,visual.controlRing,0,Math.PI*2);ctx.stroke();}ctx.restore(); }
function drawBall(){const visual=actorVisual.ball;ctx.save();ctx.translate(ball.x,ball.y);const airborne=Math.min(1,Math.abs(ball.z)/80);ctx.fillStyle=`rgba(0,0,0,${.32-airborne*.15})`;ctx.beginPath();ctx.ellipse(1,6,visual.shadowX-airborne*2,visual.shadowY-airborne*.5,0,0,Math.PI*2);ctx.fill();ctx.translate(0,ball.z);ctx.fillStyle='#f4f0dc';ctx.beginPath();ctx.arc(0,0,visual.r,0,Math.PI*2);ctx.fill();ctx.fillStyle='#243331';ctx.beginPath();ctx.arc(0,0,visual.patch,0,Math.PI*2);ctx.fill();ctx.restore();}
const simulationClock = createSimulationClock(update);
document.addEventListener('visibilitychange', () => {
  simulationClock.reset();
  actionQueue.clear();
  last = performance.now();
  if (document.hidden) keys.clear();
});
addEventListener('blur', () => { keys.clear(); actionQueue.clear(); });
function frame(now){const dt=(now-last)/1000;last=now;if(!document.hidden)simulationClock.advance(dt);draw();requestAnimationFrame(frame);} requestAnimationFrame(frame);
