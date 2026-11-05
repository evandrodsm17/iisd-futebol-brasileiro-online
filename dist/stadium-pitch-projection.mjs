// Projection measured from white lines of the exported layout-1 preview.
// This is not yet a reconstruction of the original SNES Mode 7 camera.
export const layout1Pitch=Object.freeze({topY:190,bottomY:833,leftXMinusY:-32,rightXMinusY:1824});

export function projectPitchToSource(x,y,field){
 if(![x,y,field?.x,field?.y,field?.w,field?.h].every(Number.isFinite)||field.w<=0||field.h<=0)throw new RangeError('Campo inválido');
 const u=(x-field.x)/field.w,v=(y-field.y)/field.h;
 const sourceY=layout1Pitch.topY+v*(layout1Pitch.bottomY-layout1Pitch.topY);
 return {x:sourceY+layout1Pitch.leftXMinusY+u*(layout1Pitch.rightXMinusY-layout1Pitch.leftXMinusY),y:sourceY};
}

export function unprojectSourceToPitch(x,y,field){
 if(![x,y,field?.x,field?.y,field?.w,field?.h].every(Number.isFinite)||field.w<=0||field.h<=0)throw new RangeError('Campo inválido');
 const v=(y-layout1Pitch.topY)/(layout1Pitch.bottomY-layout1Pitch.topY);
 const u=(x-y-layout1Pitch.leftXMinusY)/(layout1Pitch.rightXMinusY-layout1Pitch.leftXMinusY);
 return {x:field.x+u*field.w,y:field.y+v*field.h};
}
