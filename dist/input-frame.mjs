// Capture browser input at a fixed simulation tick without retaining DOM key objects.
// Action order is preserved; held directions and run remain active on later ticks.
export function captureInputFrame(keys,bindings,queue) {
 const actions=[];
 queue.drain(action=>actions.push(action));
 return {
  up:keys.has(bindings.up),down:keys.has(bindings.down),
  left:keys.has(bindings.left),right:keys.has(bindings.right),
  run:keys.has(bindings.run),actions,
 };
}

// Raw screen axes preserve opposing-key cancellation and are shared by actions.
export function inputAxes(frame) {
 return {x:Number(frame.right)-Number(frame.left),y:Number(frame.down)-Number(frame.up)};
}
