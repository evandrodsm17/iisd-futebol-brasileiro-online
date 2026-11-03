// Model of 8B:D151's selected color write; null means no write, not black.
export function teamDetailColor(manifest,team,kit){
 if(manifest?.schema!=='issd-team-detail-colors/v1'||!Number.isInteger(team)||team<0||team>=36||!['home','away'].includes(kit))throw new RangeError('Equipe ou uniforme inválido');
 const row=manifest.teams?.[team],entry=row?.[kit];
 if(row?.team_id!==team||!entry||!Number.isInteger(entry.selector))throw new Error('Tabela de cor inválida');
 if(entry.selector===0){if(entry.bgr555!==null)throw new Error('Seletor sem escrita inválido');return null;}
 if(!Number.isInteger(entry.bgr555)||entry.bgr555<0||entry.bgr555>0x7fff)throw new Error('Cor BGR555 inválida');
 return [0,5,10].map(shift=>{const n=(entry.bgr555>>shift)&31;return (n<<3)|(n>>2);});
}
