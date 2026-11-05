// Projection measured from white lines of eight stadium previews.
// This is not yet a reconstruction of the original SNES Mode 7 camera.
export const stadiumPitches=Object.freeze({
 0:Object.freeze({topY:222,bottomY:801,leftXMinusY:-64,rightXMinusY:1728}),
 1:Object.freeze({topY:190,bottomY:833,leftXMinusY:-32,rightXMinusY:1824}),
 3:Object.freeze({topY:190,bottomY:833,leftXMinusY:-32,rightXMinusY:2016}),
 4:Object.freeze({topY:190,bottomY:833,leftXMinusY:-32,rightXMinusY:1888}),
 5:Object.freeze({topY:222,bottomY:801,leftXMinusY:-64,rightXMinusY:1856}),
 6:Object.freeze({topY:158,bottomY:865,leftXMinusY:0,rightXMinusY:1792}),
 7:Object.freeze({topY:158,bottomY:865,leftXMinusY:0,rightXMinusY:2176}),
});
export const layout1Pitch=stadiumPitches[1];
// Layout 2 is a distinct perspective image. These corners are line-fit
// estimates, not original ROM geometry or exact goal-post positions.
export const layout2Corners=Object.freeze([[233.628,207.5],[1968.567,207.5],[829.392,837],[2667.131,837]].map(Object.freeze));
function perspectiveCoefficients(){
 const [[x0,y0],[x1,y1],[x2,y2],[x3,y3]]=layout2Corners;
 const dx1=x1-x3,dx2=x2-x3,dx3=x0-x1+x3-x2,dy1=y1-y3,dy2=y2-y3,dy3=y0-y1+y3-y2;
 const denominator=dx1*dy2-dx2*dy1,g=(dx3*dy2-dx2*dy3)/denominator,h=(dx1*dy3-dx3*dy1)/denominator;
 return {a:x1-x0+g*x1,b:x2-x0+h*x2,c:x0,d:y1-y0+g*y1,e:y2-y0+h*y2,f:y0,g,h};
}
const perspective=perspectiveCoefficients();

export function projectPitchToSource(x,y,field,layout=1){
 if(![x,y,field?.x,field?.y,field?.w,field?.h].every(Number.isFinite)||field.w<=0||field.h<=0)throw new RangeError('Campo inválido');
 const u=(x-field.x)/field.w,v=(y-field.y)/field.h;
 if(layout===2){const {a,b,c,d,e,f,g,h}=perspective,den=g*u+h*v+1;if(Math.abs(den)<1e-12)throw new RangeError('Projeção indefinida');return {x:(a*u+b*v+c)/den,y:(d*u+e*v+f)/den};}
 const pitch=stadiumPitches[layout];if(!pitch)throw new RangeError('Projeção de estádio não medida');
 const sourceY=pitch.topY+v*(pitch.bottomY-pitch.topY);
 return {x:sourceY+pitch.leftXMinusY+u*(pitch.rightXMinusY-pitch.leftXMinusY),y:sourceY};
}

export function unprojectSourceToPitch(x,y,field,layout=1){
 if(![x,y,field?.x,field?.y,field?.w,field?.h].every(Number.isFinite)||field.w<=0||field.h<=0)throw new RangeError('Campo inválido');
 if(layout===2){const {a,b,c,d,e,f,g,h}=perspective,A=a-x*g,B=b-x*h,C=x-c,D=d-y*g,E=e-y*h,F=y-f,det=A*E-B*D;if(Math.abs(det)<1e-12)throw new RangeError('Projeção indefinida');return {x:field.x+(C*E-B*F)/det*field.w,y:field.y+(A*F-C*D)/det*field.h};}
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
export function canvasDirectionToPitch(dx,dy,field,crop,layout=1,anchor={x:field.x,y:field.y}){
 if(![dx,dy].every(Number.isFinite))throw new RangeError('Direção inválida');
 const origin=unprojectCanvasToPitch(anchor.x,anchor.y,field,crop,layout);
 const target=unprojectCanvasToPitch(anchor.x+dx,anchor.y+dy,field,crop,layout);
 return {x:target.x-origin.x,y:target.y-origin.y};
}
