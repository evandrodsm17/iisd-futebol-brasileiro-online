// A lobby is signalling only. It never starts or alters the local match.
export function setupOnlineLobby(doc, onBack, WebSocketClass = WebSocket, location = window.location) {
  const el = id => doc.getElementById(id);
  const status = el('online-status'), room = el('online-room'), code = el('online-code');
  const create = el('online-create'), join = el('online-join'), input = el('online-input'), leave = el('online-leave');
  let socket = null, inRoom = false, ready = false, teams = [];
  const teamSelect = el('online-team'), kitSelect = el('online-kit');
  const readyButton = el('online-ready');
  function controls(connected) {
    create.disabled = !connected || inRoom; join.disabled = !connected || inRoom; input.disabled = !connected || inRoom;
    leave.hidden = !inRoom; room.hidden = !inRoom;
  }
  function disconnect() {
    const old = socket; socket = null; inRoom = false; ready = false; controls(false);
    if (old) old.close();
  }
  function send(message) { if (socket?.readyState === WebSocketClass.OPEN) socket.send(JSON.stringify(message)); }
  create.addEventListener('click', () => send({type:'create'}));
  join.addEventListener('click', () => {
    const value = input.value.trim().toUpperCase();
    if (!/^[A-F0-9]{8}$/.test(value)) { status.textContent = 'Informe um código de 8 caracteres hexadecimais.'; return; }
    send({type:'join',code:value});
  });
  function selectTeam() {
    if (teamSelect.value === '') return;
    send({type:'selection',team:Number(teamSelect.value),kit:Number(kitSelect.value)});
  }
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
        teams = message.teams;
        teamSelect.replaceChildren(...[ {id:'',name:'SELECIONE'}, ...teams ].map(team => { const option=doc.createElement('option'); option.value=String(team.id); option.textContent=team.name; return option; }));
        controls(true); status.textContent = 'Conectado. Crie uma sala ou informe um código.'; }
      else if (message.type === 'room') {
        inRoom = true; controls(true); code.textContent = message.code;
        el('online-players').textContent = `Participantes: ${message.players} de ${message.capacity} · Você é ${message.seat}P`;
        const self = message.participants.find(player => player.seat === message.seat);
        ready = self?.ready === true;
        teamSelect.value = self.team === null ? '' : String(self.team); kitSelect.value = String(self.kit);
        el('online-selections').textContent = message.participants.map(player => `${player.seat}P: ${teams.find(team => team.id === player.team)?.name ?? 'equipe não selecionada'}${player.team === null ? '' : ` · uniforme ${player.kit + 1}`}`).join(' | ');
        readyButton.textContent = ready ? 'CANCELAR PRONTO' : 'ESTOU PRONTO';
        readyButton.setAttribute('aria-pressed', String(ready));
        el('online-readiness').textContent = message.participants.map(player => `${player.seat}P: ${player.ready ? 'pronto' : 'aguardando'}`).join(' · ');
        status.textContent = message.players === 2 ? 'Dois participantes conectados.' : 'Aguardando outro participante.';
      } else if (message.type === 'left') { inRoom = false; ready = false; controls(true); status.textContent = 'Você saiu da sala.'; }
      else if (message.type === 'error') {
        const errors = {room_not_found:'Sala não encontrada.',room_full:'Esta sala está cheia.',invalid_room_code:'Código de sala inválido.',already_in_room:'Você já está em uma sala.',lobby_full:'O servidor está com o limite de salas atingido.',selection_required:'Selecione sua equipe antes de confirmar.',invalid_selection:'Equipe ou uniforme inválido.'};
        status.textContent = errors[message.code] || 'O servidor não aceitou a operação.';
      }
    });
    current.addEventListener('close', () => { if (socket !== current) return; socket = null; inRoom = false; controls(false); status.textContent = 'Conexão encerrada. Volte ao menu e tente novamente.'; });
    current.addEventListener('error', () => { if (socket === current) status.textContent = 'Não foi possível conectar ao servidor de salas.'; });
  }};
}
