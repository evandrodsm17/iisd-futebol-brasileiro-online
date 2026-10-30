// Browser action edges are logical action IDs rather than hardcoded key codes.
export function createActionQueue() {
  const actions = new Set(['reset','switch','shot','pass','press']);
  let pending = [];
  return {
    push(action, repeat = false) {
      if (!repeat && actions.has(action) && pending.length < 32) pending.push(action);
    },
    drain(dispatch) { const current = pending; pending = []; for (const action of current) dispatch(action); },
    clear() { pending = []; },
  };
}
