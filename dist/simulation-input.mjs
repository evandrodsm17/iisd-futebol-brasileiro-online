// Browser action edges, consumed once at a simulation boundary.
export function createActionQueue() {
  const actions = new Set(['KeyR', 'KeyQ', 'Space', 'KeyX', 'KeyF']);
  let pending = [];
  return {
    push(code, repeat = false) {
      if (!repeat && actions.has(code) && pending.length < 32) pending.push(code);
    },
    drain(dispatch) {
      const current = pending;
      pending = [];
      for (const code of current) dispatch(code);
    },
    clear() { pending = []; },
  };
}
