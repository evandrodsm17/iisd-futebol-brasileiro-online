import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {prepareOnlineMatch} from './online-match-setup.mjs';
const catalog=JSON.parse(readFileSync(new URL('./data/issd-rom-catalog.json',import.meta.url),'utf8'));
const layouts=JSON.parse(readFileSync(new URL('./data/issd-stadium-layouts.json',import.meta.url),'utf8')).layouts;
const setup={epoch:'a'.repeat(32),build:'build',settings:{stadium:1,gameTime:1},sides:[{team:30,kit:'home'},{team:2,kit:'away'}]};
test('prepares independent copies of base teams, lineups and stadium',()=>{
 const first=prepareOnlineMatch(setup,catalog,layouts,'build'),second=prepareOnlineMatch(setup,catalog,layouts,'build');
 assert.deepEqual(first,second);assert.equal(first.teams[0].team.id,30);assert.equal(first.teams[1].kit,'away');assert.equal(first.teams[0].starters.length,11);assert.equal(first.stadium.id,1);assert.equal(first.gameTime,1);
 first.teams[0].team.name='alterado';assert.notEqual(first.teams[0].team.name,catalog.teams[30].name);assert.notEqual(first.teams[0].team.name,second.teams[0].team.name);
});
test('refuses incompatible build, incomplete catalog and invalid configuration',()=>{
 assert.equal(prepareOnlineMatch(setup,catalog,layouts,'other'),null);
 assert.equal(prepareOnlineMatch({...setup,epoch:'old'},catalog,layouts,'build'),null);
 assert.equal(prepareOnlineMatch({...setup,settings:{...setup.settings,stadium:999}},catalog,layouts,'build'),null);
 assert.equal(prepareOnlineMatch({...setup,settings:{...setup.settings,gameTime:9}},catalog,layouts,'build'),null);
 assert.equal(prepareOnlineMatch({...setup,sides:[setup.sides[0],{team:999,kit:'away'}]},catalog,layouts,'build'),null);
 assert.equal(prepareOnlineMatch({...setup,sides:[setup.sides[0],{team:2,kit:'third'}]},catalog,layouts,'build'),null);
 assert.equal(prepareOnlineMatch(setup,{teams:[]},layouts,'build'),null);
});
