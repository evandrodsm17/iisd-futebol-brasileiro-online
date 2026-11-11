// Compare the local USA ROM goal-region tables with the browser approximation.
// This is a scale diagnostic, not proof that a band denotes the goal mouth.
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {nativeDimensions,fieldDimensions} from '../dist/native-field.mjs';
import {nativeGoalBands,nativeGoalBandBranch,nativeGoalEntryBranch} from '../dist/native-goal-bands.mjs';
const romPath=new URL('../International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc',import.meta.url);
const rom=readFileSync(romPath),game=readFileSync(new URL('../dist/game.js',import.meta.url),'utf8');
const match=game.match(/const field\s*=\s*\{[^}]*goalH:\s*(\d+(?:\.\d+)?)/);
if(!match)throw new Error('Browser goalH not found');
const browserGoalH=Number(match[1]),cases=[];
for(let stadium=0;stadium<8;stadium++){
 const [w,h]=nativeDimensions[stadium],world=fieldDimensions(stadium),b=nativeGoalBands(stadium);
 if(rom.readUInt16LE(0xec47+stadium*4)!==w||rom.readUInt16LE(0xec49+stadium*4)!==h)throw new Error(`Native dimensions mismatch ${stadium}`);
 for(const [i,value] of Object.values(b).entries())if(rom.readUInt16LE(0xa833+i*16+stadium*2)!==value)throw new Error(`Native band mismatch ${stadium}:${i}`);
 const boundaries=Object.fromEntries([b.outerLow-1,b.outerLow,b.innerLow-1,b.innerLow,b.innerHigh-1,b.innerHigh,b.outerHigh-1,b.outerHigh].map(value=>[value,nativeGoalBandBranch(stadium,value)]));
 const scale=world.h/h;
 cases.push({stadium,nativeWidth:w,nativeHeight:h,nativeBands:b,nativeCentralBandWidth:b.innerHigh-b.innerLow,nativeOuterBandWidth:b.outerHigh-b.outerLow,browserFieldHeight:world.h,browserGoalHeight:browserGoalH,assumingLinearFieldScale:{worldUnitsPerNativeY:scale,centralBandWorldHeight:(b.innerHigh-b.innerLow)*scale,outerBandWorldHeight:(b.outerHigh-b.outerLow)*scale,browserGoalToCentralBandRatio:browserGoalH/((b.innerHigh-b.innerLow)*scale)},boundaries});
}
const out={schema:'issd-goal-geometry-audit/v1',source:{rom:'USA unheadered; local only',romSha256:createHash('sha256').update(rom).digest('hex'),dimensionsLoRomOffset:'0x00EC47',thresholdsLoRomOffsets:['0x00A833','0x00A843','0x00A853','0x00A863'],branch:'83:8BAB..83:8BC8',furtherChecks:'83:8D76..83:8DA0'},browser:{goalHeight:browserGoalH,comparison:'visual projection and field scale are approximations'},cases,limitations:['The central branch is not alone a goal decision; additional logic and side effects apply.','Linear conversion follows browser field scaling and is an unverified assumption for native ball coordinates.','Post contact, crossbar height and scoring require dynamic evidence; no collision behavior is established by this comparison.','Original ROM is not included in this report.']};
writeFileSync(new URL('../docs/issd-goal-geometry-audit.json',import.meta.url),JSON.stringify(out,null,2)+'\n');
console.log(`OK: dimensions and 32 thresholds checked against local ROM; USA browser goal ${browserGoalH}, scaled central band ${cases[1].assumingLinearFieldScale.centralBandWorldHeight.toFixed(3)} (conditional)`);
