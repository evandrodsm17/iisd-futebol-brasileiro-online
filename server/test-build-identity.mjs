import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdir,mkdtemp,writeFile,rm} from 'node:fs/promises';
import path from 'node:path';
import {gameBuildIdentity} from './build-identity.mjs';

test('identity ignores line ending differences but changes with game code',async t=>{
 const workspace=path.resolve('analysis');await mkdir(workspace,{recursive:true});
 const root=await mkdtemp(path.join(workspace,'build-identity-'));
 t.after(async()=>{const relative=path.relative(workspace,root);assert.ok(relative&&!relative.startsWith('..')&&!path.isAbsolute(relative));await rm(root,{recursive:true,force:true});});
 const game=path.join(root,'game.js');await writeFile(game,'line1\nline2\n');const original=await gameBuildIdentity(root);
 await writeFile(game,'line1\r\nline2\r\n');assert.equal(await gameBuildIdentity(root),original);
 await writeFile(path.join(root,'online-build.mjs'),'generated');await writeFile(path.join(root,'test-a.mjs'),'test');assert.equal(await gameBuildIdentity(root),original);
 await writeFile(game,'line1\nchanged\n');assert.notEqual(await gameBuildIdentity(root),original);
});
