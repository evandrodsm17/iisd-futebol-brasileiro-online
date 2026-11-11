import {ONLINE_BUILD} from './online-build.mjs';
import {prepareOnlineMatch} from './online-match-setup.mjs';
const LOBBY_PROTOCOL = 2;

// A lobby is signalling only. It never starts or alters the local match.
export function setupOnlineLobby(doc, onBack, WebSocketClass = WebSocket, location = window.location) {
  const el = id => doc.getElementById(id);
  const status = el('online-status'), room = el('online-room'), code = el('online-code');
  const create = el('online-create'), join = el('online-join'), input = el('online-input'), leave = el('online-leave');
  let socket = null, inRoom = false, ready = false, teams = [], validationVersion = 0;
  const teamSelect = el('online-team'), kitSelect = el('online-kit');
  const stadiumSelect=el('online-stadium'),timeSelect=el('online-time');
  const readyButton = el('online-ready');
  function controls(connected) {
    create.disabled = !connected || inRoom; join.disabled = !connected || inRoom; input.disabled = !connected || inRoom;
    leave.hidden = !inRoom; room.hidden = !inRoom;
  }
  function disconnect() {
    const old = socket; socket = null; inRoom = false; ready = false; validationVersion++;el('online-validation').textContent='';controls(false);
    if (old) old.close();
  }
  function send(message) { if (socket?.readyState === WebSocketClass.OPEN) socket.send(JSON.stringify(message)); }
  async function validateSetup(setup,current){
    const version=++validationVersion,notice=el('online-validation');
    notice.textContent='Verificando dados básicos da partida neste navegador…';
    try {
      const base=`${location.protocol}//${location.host}`;
      const [catalogResponse,layoutsResponse]=await Promise.all([
        fetch(`${base}/data/issd-rom-catalog.json`),fetch(`${base}/data/issd-stadium-layouts.json`),
      ]);
      if(!catalogResponse.ok||!layoutsResponse.ok)throw new Error('dados indisponíveis');
      const [catalog,manifest]=await Promise.all([catalogResponse.json(),layoutsResponse.json()]);
      const prepared=prepareOnlineMatch(setup,catalog,manifest.layouts,ONLINE_BUILD);
      if(socket!==current||validationVersion!==version)return;
      notice.textContent=prepared?'Dados básicos de equipes, escalações e estádio verificados neste navegador.':'Não foi possível validar os dados básicos desta configuração.';
    } catch {
      if(socket===current&&validationVersion===version)notice.textContent='Dados básicos indisponíveis. Atualize a página e tente novamente.';
    }
  }

  create.addEventListener('click', () => send({type:'create',protocol:LOBBY_PROTOCOL,build:ONLINE_BUILD}));
  join.addEventListener('click', () => {
    const value = input.value.trim().toUpperCase();
    if (!/^[A-F0-9]{8}$/.test(value)) { status.textContent = 'Informe um código de 8 caracteres hexadecimais.'; return; }
    send({type:'join',code:value,protocol:LOBBY_PROTOCOL,build:ONLINE_BUILD});
  });
  function selectTeam() {
    if (teamSelect.value === '') return;
    send({type:'selection',team:Number(teamSelect.value),kit:Number(kitSelect.value)});
  }
  function selectSettings(){send({type:'settings',stadium:Number(stadiumSelect.value),gameTime:Number(timeSelect.value)});}
  stadiumSelect.addEventListener('change',selectSettings);timeSelect.addEventListener('change',selectSettings);
  teamSelect.addEventListener('change', selectTeam); kitSelect.addEventListener('change', selectTeam);
  readyButton.addEventListener('click', () => send({type:'ready',ready:!ready}));
  leave.addEventListener('click', () => send({type:'leave'}));
  el('online-back').addEventListener('click', () => { disconnect(); onBack(); });
  return { open() {
    disconnect(); status.textContent = 'Conectando ao servidor…';
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    let current;
    try { current = new WebSocketClass(`${protocol}//${location.host}/api/v1/lobby`); }
    catch { status.textContent = 'Não foi possível conectar ao servidor de salas.'; return; }
    socket = current;
    current.addEventListener('message', event => {
      if (socket !== current) return;
      let message; try { message = JSON.parse(event.data); } catch { return; }
      if (message.type === 'connected') {
        if (message.protocol !== LOBBY_PROTOCOL || !Array.isArray(message.teams) || !Array.isArray(message.stadiums) || !Array.isArray(message.gameTimes)) {
          status.textContent = 'Versão incompatível do servidor. Atualize a página ou reinicie o servidor.';
          return;
        }
        if (message.build !== ONLINE_BUILD) {
          status.textContent = 'Arquivos do jogo incompatíveis. Atualize a página ou gere a versão online novamente.';
          return;
        }
        teams = message.teams;
        teamSelect.replaceChildren(...[ {id:'',name:'SELECIONE'}, ...teams ].map(team => { const option=doc.createElement('option'); option.value=String(team.id); option.textContent=team.name; return option; }));
        stadiumSelect.replaceChildren(...message.stadiums.map(stadium=>{const option=doc.createElement('option');option.value=String(stadium.id);option.textContent=stadium.name;return option;}));
        timeSelect.replaceChildren(...message.gameTimes.map(value=>{const option=doc.createElement('option');option.value=String(value);option.textContent=`${String([3,5,7][value] ?? value).padStart(2,'0')}:00`;return option;}));
        controls(true); status.textContent = 'Conectado. Crie uma sala ou informe um código.'; }
      else if (message.type === 'room') {
        inRoom = true; controls(true); code.textContent = message.code;
        el('online-players').textContent = `Participantes: ${message.players} de ${message.capacity} · Você é ${message.seat}P`;
        stadiumSelect.value=String(message.settings.stadium);timeSelect.value=String(message.settings.gameTime);
        stadiumSelect.disabled=timeSelect.disabled=message.seat!==message.hostSeat;
        el('online-settings-note').textContent=message.seat===message.hostSeat?'Você configura estádio e tempo.':'O anfitrião configura estádio e tempo.';
        const self = message.participants.find(player => player.seat === message.seat);
        ready = self?.ready === true;
        teamSelect.value = self.team === null ? '' : String(self.team); kitSelect.value = String(self.kit);
        el('online-selections').textContent = message.participants.map(player => `${player.seat}P: ${teams.find(team => team.id === player.team)?.name ?? 'equipe não selecionada'}${player.team === null ? '' : ` · uniforme ${player.kit + 1}`}`).join(' | ');
        readyButton.textContent = ready ? 'CANCELAR PRONTO' : 'ESTOU PRONTO';
        readyButton.setAttribute('aria-pressed', String(ready));
        el('online-readiness').textContent = message.participants.map(player => `${player.seat}P: ${player.ready ? 'pronto' : 'aguardando'}`).join(' · ');
        if(message.phase==='ready'&&message.matchSetup)validateSetup(message.matchSetup,current);
        else { validationVersion++; el('online-validation').textContent=''; }
        status.textContent = message.phase === 'ready' ? 'Ambos estão prontos. A partida online ainda está em desenvolvimento.' : message.phase === 'selection' ? 'Escolham as equipes e confirmem quando estiverem prontos.' : 'Aguardando outro participante.';
      } else if (message.type === 'left') { validationVersion++;el('online-validation').textContent='';inRoom = false; ready = false; controls(true); status.textContent = 'Você saiu da sala.'; }
      else if (message.type === 'error') {
        const errors = {room_not_found:'Sala não encontrada.',room_full:'Esta sala está cheia.',invalid_room_code:'Código de sala inválido.',already_in_room:'Você já está em uma sala.',lobby_full:'O servidor está com o limite de salas atingido.',selection_required:'Selecione sua equipe antes de confirmar.',invalid_selection:'Equipe ou uniforme inválido.',protocol_mismatch:'Versão incompatível. Atualize a página.',build_mismatch:'Arquivos do jogo incompatíveis. Atualize a página.',host_only:'Somente o anfitrião pode alterar as configurações.',invalid_settings:'Estádio ou tempo inválido.'};
        status.textContent = errors[message.code] || 'O servidor não aceitou a operação.';
      }
    });
    current.addEventListener('close', () => { if (socket !== current) return; socket = null; inRoom = false; validationVersion++;el('online-validation').textContent='';controls(false); status.textContent = 'Conexão encerrada. Volte ao menu e tente novamente.'; });
    current.addEventListener('error', () => { if (socket === current) status.textContent = 'Não foi possível conectar ao servidor de salas.'; });
  }};
}
