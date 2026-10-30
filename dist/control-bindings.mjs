// Controls use KeyboardEvent.code (physical keyboard position), not event.key.
export const CONTROL_LABELS = Object.freeze({
  up: 'Mover para cima',
  down: 'Mover para baixo',
  left: 'Mover para esquerda',
  right: 'Mover para direita',
  run: 'Correr',
  shot: 'Chutar',
  pass: 'Passar',
  press: 'Pressionar / desarmar',
  switch: 'Trocar jogador',
  reset: 'Reiniciar jogada',
});
export const DEFAULT_BINDINGS = Object.freeze({
  up: 'KeyW', down: 'KeyS', left: 'KeyA', right: 'KeyD',
  run: 'ShiftLeft', shot: 'Space', pass: 'KeyX',
  press: 'KeyF', switch: 'KeyQ', reset: 'KeyR',
});
const STORAGE_KEY = 'issd-web-controls-v1';
const SUPPORTED = /^(?:Key[A-Z]|Digit[0-9]|Numpad[0-9]|Arrow(?:Up|Down|Left|Right)|Shift(?:Left|Right)|Space|Enter|Backspace)$/;

export function supportedKey(code) { return typeof code === 'string' && SUPPORTED.test(code); }
export function validBindings(value) {
  return value != null && typeof value === 'object'
    && Object.keys(DEFAULT_BINDINGS).every(action => supportedKey(value[action]))
    && new Set(Object.keys(DEFAULT_BINDINGS).map(action => value[action])).size === Object.keys(DEFAULT_BINDINGS).length;
}
export function assignBinding(current, action, code) {
  if (!Object.hasOwn(DEFAULT_BINDINGS, action)) return { ok: false, message: 'Ação desconhecida.' };
  if (!supportedKey(code)) return { ok: false, message: 'Tecla não permitida. Use letras, números, setas, Shift, Espaço ou Enter.' };
  const occupied = Object.keys(DEFAULT_BINDINGS).find(other => other !== action && current[other] === code);
  if (occupied) return { ok: false, message: 'Tecla já usada por: ' + CONTROL_LABELS[occupied] + '.' };
  return { ok: true, bindings: { ...current, [action]: code } };
}
export function loadBindings(storage = globalThis.localStorage) {
  try {
    const stored = JSON.parse(storage.getItem(STORAGE_KEY));
    return validBindings(stored) ? { ...stored } : { ...DEFAULT_BINDINGS };
  } catch {
    return { ...DEFAULT_BINDINGS };
  }
}
export function saveBindings(bindings, storage = globalThis.localStorage) {
  if (!validBindings(bindings)) return false;
  try { storage.setItem(STORAGE_KEY, JSON.stringify(bindings)); return true; }
  catch { return false; }
}
export function keyLabel(code) {
  if (code.startsWith('Key') || code.startsWith('Digit')) return code.replace(/^Key|^Digit/, '');
  const names = { Space: 'ESPAÇO', ShiftLeft: 'SHIFT ESQ.', ShiftRight: 'SHIFT DIR.', ArrowUp: '↑', ArrowDown: '↓', ArrowLeft: '←', ArrowRight: '→', Enter: 'ENTER', Backspace: 'BACKSPACE' };
  return names[code] || code;
}
export function actionForCode(bindings, code) {
  return Object.keys(DEFAULT_BINDINGS).find(action => bindings[action] === code) ?? null;
}
