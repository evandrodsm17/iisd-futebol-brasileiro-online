import assert from 'node:assert/strict';
import {BALL_SPRITE_PATH,BALL_SOURCE_SIZE,INDICATOR_ARROW_BLUE_PATH,INDICATOR_ARROW_RED_PATH,arrowPathForTeam,INDICATOR_ARROW_WIDTH,INDICATOR_ARROW_HEIGHT,playerDisplayName,readIndicatorMode,saveIndicatorMode} from '../dist/ball-indicator.mjs';
assert.equal(BALL_SOURCE_SIZE,12);
assert.equal(BALL_SPRITE_PATH,'./assets/issd/ball/ball-readable-12x12.png');
assert.equal(playerDisplayName({roster:{name:'  Nome   Novo  '}}),'Nome Novo');
assert.equal(playerDisplayName({number:9}),'JOGADOR 9');
const state=new Map();const storage={getItem:k=>state.get(k)??null,setItem:(k,v)=>state.set(k,v)};
assert.equal(readIndicatorMode(storage),'arrow-name');
assert.equal(saveIndicatorMode('arrow',storage),true);
assert.equal(readIndicatorMode(storage),'arrow');
assert.throws(()=>saveIndicatorMode('broken',storage));
console.log('OK: original ball path, selected player names and persisted visibility options');

assert.equal(INDICATOR_ARROW_BLUE_PATH,'./assets/issd/ui/controlled-arrow-blue.png');
assert.equal(INDICATOR_ARROW_RED_PATH,'./assets/issd/ui/controlled-arrow-red.png');
assert.equal(arrowPathForTeam(0),INDICATOR_ARROW_BLUE_PATH);
assert.equal(arrowPathForTeam(1),INDICATOR_ARROW_RED_PATH);
assert.equal(INDICATOR_ARROW_WIDTH,18);
assert.equal(INDICATOR_ARROW_HEIGHT,15);
