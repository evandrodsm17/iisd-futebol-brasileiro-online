// Projection measured from white lines of three exported stadium previews.
// This is not yet a reconstruction of the original SNES Mode 7 camera.
export const stadiumPitches=Object.freeze({
 0:Object.freeze({topY:222,bottomY:801,leftXMinusY:-64,rightXMinusY:1728}),
 1:Object.freeze({topY:190,bottomY:833,leftXMinusY:-32,rightXMinusY:1824}),
 3:Object.freeze({topY:190,bottomY:833,leftXMinusY:-32,rightXMinusY:2016}),
});
export const layout1Pitch=stadiumPitches[1];

export function projectPitchToSource(x,y,field,layout=1){
 if(![x,y,field?.x,field?.y,field?.w,field?.h].every(Number.isFinite)||field.w<=0||field.h<=0)throw new RangeError('Campo inválido');
 const pitch=stadiumPitches[layout];if(!pitch)throw new RangeError('Projeção de estádio não medida');
 const u=(x-field.x)/field.w,v=(y-field.y)/field.h;
 const sourceY=pitch.topY+v*(pitch.bottomY-pitch.topY);
 return {x:sourceY+pitch.leftXMinusY+u*(pitch.rightXMinusY-pitch.leftXMinusY),y:sourceY};
}

export function unprojectSourceToPitch(x,y,field,layout=1){
 if(![x,y,field?.x,field?.y,field?.w,field?.h].every(Number.isFinite)||field.w<=0||field.h<=0)throw new RangeError('Campo inválido');
 const pitch=stadiumPitches[layout];if(!pitch)throw new RangeError('Projeção de estádio não medida');
 const v=(y-pitch.topY)/(pitch.bottomY-pitch.topY);
 const u=(x-y-pitch.leftXMinusY)/(pitch.rightXMinusY-pitch.leftXMinusY);
 return {x:field.x+u*field.w,y:field.y+v*field.h};
}

// Presentation-space mapping uses the same crop and destination as drawImage.
// The source geometry is calibrated from the preview, not from Mode 7.
export function projectPitchToCanvas(x,y,field,crop,layout=1){
 if(![crop?.x,crop?.y,crop?.w,crop?.h].every(Number.isFinite)||crop.w<=0||crop.h<=0)throw new RangeError('Recorte inválido');
 const p=projectPitchToSource(x,y,field,layout);
 return {x:field.x+(p.x-crop.x)*field.w/crop.w,y:field.y+(p.y-crop.y)*field.h/crop.h};
}

export function unprojectCanvasToPitch(x,y,field,crop,layout=1){
 if(![crop?.x,crop?.y,crop?.w,crop?.h].every(Number.isFinite)||crop.w<=0||crop.h<=0)throw new RangeError('Recorte inválido');
 if(![x,y,field?.x,field?.y,field?.w,field?.h].every(Number.isFinite)||field.w<=0||field.h<=0)throw new RangeError('Campo inválido');
 return unprojectSourceToPitch(crop.x+(x-field.x)*crop.w/field.w,crop.y+(y-field.y)*crop.h/field.h,field,layout);
}

// Directions have no origin; subtracting projected points removes translation.
export function canvasDirectionToPitch(dx,dy,field,crop,layout=1){
 if(![dx,dy].every(Number.isFinite))throw new RangeError('Direção inválida');
 const origin=unprojectCanvasToPitch(field.x,field.y,field,crop,layout);
 const target=unprojectCanvasToPitch(field.x+dx,field.y+dy,field,crop,layout);
 return {x:target.x-origin.x,y:target.y-origin.y};
}
