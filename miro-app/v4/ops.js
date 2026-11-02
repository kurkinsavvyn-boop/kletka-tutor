// Временный помощник переноса: только читает доску и отвечает сообщением странице доски.
// Ничего на доске не создаёт и не меняет.
const note=m=>parent.postMessage(Object.assign({kletka:1},m),'*');
const SKIP=new Set(['paint','connector','unsupported']);
const OPS={
  // объекты (кроме рисунков от руки) снизу вверх по слоям; id сжаты в base36
  async order(){const items=(await miro.board.get()).filter(i=>!SKIP.has(i.type));const L=[];
    for(const it of items){try{L.push([await miro.board.getLayerIndex(it),it.id])}catch(e){}}
    L.sort((a,b)=>a[0]-b[0]);
    return {n:L.length,ids:L.map(x=>BigInt(x[1]).toString(36)).join(',')}},
  async info(){const i=await miro.board.getInfo();return {id:i.id}}
};
addEventListener('message',async e=>{const d=e.data;if(!d||!d.kletkaOp||e.origin!=='https://miro.com'||!OPS[d.kletkaOp])return;
  try{note({t:'res',id:d.id,v:await OPS[d.kletkaOp](d.args||{})})}catch(err){note({t:'res',id:d.id,err:err.message})}});
note({t:'ready'});
