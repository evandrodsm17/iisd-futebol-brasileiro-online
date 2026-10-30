// Native-style menu state only; the browser does not yet alter match rosters.
// Retail USA test evidence confirms 3 substitutions; validate on BizHawk next.
export function createSubstitutionFlow({maxChanges=3}={}){
 if(!Number.isInteger(maxChanges)||maxChanges<0||maxChanges>11)throw RangeError('invalid cap');
 let state='live',completed=0,selected=null;
 const retired=new Set(),introduced=new Set();
 function request(){if(state!=='live')return false;state='requested';return true;}
 function cancelRequest(){if(state!=='requested')return false;state='live';return true;}
 function admitAtStoppage(){if(state!=='requested')return false;state='options';return true;}
 function openSquad(){if(state!=='options')return false;state='choose-out';selected=null;return true;}
 function cancel(){if(!['choose-out','choose-in'].includes(state))return false;state='options';selected=null;return true;}
 function choose(id,{isStarter=false,isAvailable=true,sentOff=false}={}){
  if(!Number.isInteger(id)||id<0||!isAvailable||sentOff||retired.has(id))return {ok:false,reason:'unavailable'};
  if(completed>=maxChanges)return {ok:false,reason:'limit'};
  if(state==='choose-out'){
   if(!isStarter)return {ok:false,reason:'not-starter'};
   selected=id;state='choose-in';return {ok:true,committed:false};
  }
  if(state!=='choose-in')return {ok:false,reason:'menu-not-open'};
  if(isStarter||introduced.has(id)||id===selected)return {ok:false,reason:'not-eligible'};
  const change={out:selected,in:id};retired.add(selected);introduced.add(id);
  selected=null;completed++;state='options';return {ok:true,committed:true,change};
 }
 function resume(){if(state!=='options')return false;state='live';return true;}
 function snapshot(){return {state,completed,remaining:maxChanges-completed,selected,retired:[...retired],introduced:[...introduced]};}
 return {request,cancelRequest,admitAtStoppage,openSquad,choose,cancel,resume,snapshot};
}
