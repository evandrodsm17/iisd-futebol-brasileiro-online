// Browser control convention; this is not a claim about the original ROM.
export function contextualPassAction(actor, owner, input, handlers) {
 if (!actor) return;
 if (owner === actor) handlers.pass(actor, input);
 else if (!owner || owner.team !== actor.team) handlers.press(actor, input);
}
