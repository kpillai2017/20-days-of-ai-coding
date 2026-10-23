// The model is independent of rendering: assert exact angles without a browser.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const m=require('../engine.js');
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);
test('slider crank TDC/BDC and pin radius',()=>{
 near(m.pistonPosition(0),2.4);near(m.pistonPosition(180),1.2);
 for(let angle=-720;angle<=1440;angle+=3){
  const c=m.crankPosition(angle),p=m.pistonPosition(angle);
  near(Math.hypot(c.x,c.y),m.CRANK_RADIUS);
  near(Math.hypot(c.x,p-c.y),m.ROD_LENGTH);
  assert.ok(p>=1.2-1e-9&&p<=2.4+1e-9);
  near(p,m.pistonPosition(angle+360));
 }
});
test('piston moves DOWN on first half revolution and UP on second',()=>{
 for(let a=1;a<180;a++)assert.equal(m.getState('two',a).pistonDirection,'down');
 for(let a=181;a<360;a++)assert.equal(m.getState('two',a).pistonDirection,'up');
 for(const a of [0,180,360,540])assert.equal(m.getState('four',a).pistonDirection,'turning');
});
for(const [angle,phase,intake,exhaust] of [[0,'intake',true,false],[179,'intake',true,false],[180,'compression',false,false],[359,'compression',false,false],[360,'power',false,false],[539,'power',false,false],[540,'exhaust',false,true],[719,'exhaust',false,true]]){
 test(`four-stroke phase and valves at ${angle} degrees`,()=>{
  const s=m.getState('four',angle);assert.equal(s.phase,phase);
  assert.equal(s.intakeOpen,intake);assert.equal(s.exhaustOpen,exhaust);
  assert.equal(s.transferOpen,false);assert.equal(s.crankcaseIntakeOpen,false);
 });
}
for(const [angle,phase,exhaust,transfer] of [[0,'power',false,false],[104,'power',false,false],[105,'blowdown',true,false],[119,'blowdown',true,false],[120,'scavenging',true,true],[239,'scavenging',true,true],[240,'exhaust-closing',true,false],[254,'exhaust-closing',true,false],[255,'compression',false,false],[349,'compression',false,false],[350,'ignition',false,false]]){
 test(`two-stroke phase/port boundaries at ${angle} degrees`,()=>{
  const s=m.getState('two',angle);assert.equal(s.phase,phase);
  assert.equal(s.exhaustOpen,exhaust);assert.equal(s.transferOpen,transfer);assert.equal(s.intakeOpen,false);
 });
}
test('port heights and closing angles symmetric about BDC',()=>{
 near(m.pistonPosition(105),m.pistonPosition(255));near(m.pistonPosition(120),m.pistonPosition(240));
 assert.ok(m.pistonPosition(105)>m.pistonPosition(120));
});
test('reed inlet is illustrative upstroke interval',()=>{
 for(const [a,open] of [[189,false],[190,true],[349,true],[350,false]])assert.equal(m.getState('two',a).crankcaseIntakeOpen,open);
});
test('spark cues cross compression/power boundary',()=>{
 for(const [a,on] of [[349,false],[350,true],[369,true],[370,false]])assert.equal(m.getState('four',a).spark,on);
 for(const [a,on] of [[0,true],[9,true],[10,false],[349,false],[350,true],[359,true]])assert.equal(m.getState('two',a).spark,on);
});
test('periods differ but mechanics repeat every turn',()=>{
 assert.equal(m.cycleDegrees('four'),720);assert.equal(m.cycleDegrees('two'),360);
 assert.equal(m.getState('four',360).phase,'power');assert.equal(m.getState('four',0).phase,'intake');
 assert.deepEqual(m.getState('four',45),m.getState('four',765));
 assert.deepEqual(m.getState('two',45),m.getState('two',405));
 assert.equal(m.getState('four',-1).angle,719);assert.equal(m.getState('two',-1).angle,359);
});
test('every state is finite, captioned and bounded; stage definitions are independent',()=>{
 for(const mode of ['four','two'])for(let a=0;a<m.cycleDegrees(mode);a++){
  const s=m.getState(mode,a);assert.ok(s.title&&s.caption);assert.ok(s.burn>=0&&s.burn<=1);
  assert.ok(Number.isFinite(s.pistonY));assert.ok(s.stageIndex>=0&&s.stageIndex<4);
 }
 const stages=m.getStages('four');stages[0].title='changed';assert.equal(m.getStages('four')[0].title,'Intake');
 assert.deepEqual(m.getStages('two').map(s=>s.angle),[0,110,150,290]);
});
for(const value of [NaN,Infinity,-Infinity,null,'90',undefined]){
 test(`invalid angle ${String(value)} is rejected`,()=>{
  assert.throws(()=>m.getState('four',value));assert.throws(()=>m.pistonPosition(value));assert.throws(()=>m.crankPosition(value));
 });
}
for(const mode of ['diesel',null,{},3])test(`invalid mode ${String(mode)} is rejected`,()=>assert.throws(()=>m.getState(mode,0)));
test('normalization accepts negative turns but rejects invalid periods',()=>{
 assert.equal(m.normalizedAngle(-360),0);assert.equal(m.normalizedAngle(-721,720),719);
 for(const period of [0,-1,NaN,Infinity])assert.throws(()=>m.normalizedAngle(0,period));
});

test('fixed event captions follow intake, spark, power and exhaust',()=>{
 assert.ok(m.getEventCaptions('four',90).includes('Air–fuel mixture enters'));
 assert.ok(m.getEventCaptions('four',355).includes('Spark ignites the charge'));
 assert.ok(m.getEventCaptions('four',450).includes('Expanding gases push the piston down'));
 assert.ok(m.getEventCaptions('four',630).includes('Burnt gases leave the cylinder'));
 assert.ok(!m.getEventCaptions('four',270).some(s=>s.includes('Spark')));
});
test('two-stroke event captions distinguish transfer and crankcase induction',()=>{
 assert.ok(m.getEventCaptions('two',150).includes('Fresh mixture transfers from crankcase to cylinder'));
 assert.ok(m.getEventCaptions('two',245).includes('Transfer port closes; exhaust is still open'));
 assert.ok(m.getEventCaptions('two',290).includes('Fresh mixture enters the crankcase'));
 assert.ok(m.getEventCaptions('two',355).includes('Spark ignites the charge'));
});
test('crank main journals and webs clear the connecting rod plane throughout a turn',()=>{
 // Record renderer primitives without a DOM or graphics library. This tests the
 // geometry the renderer actually emits, not a separate unused clearance value.
 const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
 const context={EngineModel:m};vm.createContext(context);
 vm.runInContext(fs.readFileSync(path.join(__dirname,'../renderer.js'),'utf8'),context);
 const renderer=new context.EngineRenderer({getContext:()=>({})});
 for(let angle=0;angle<360;angle+=5){
  const tubes=[];renderer.tube=(a,b,radius,color)=>tubes.push({a,b,radius,color});
  renderer.box=()=>{};renderer.arrow=()=>{};renderer.label=()=>{};
  const state=m.getState('four',angle);renderer.build(state,0);
  const rod=tubes.find(t=>t.color==='#acbed0'&&t.a[1]===state.pistonY&&t.b[1]===state.crank.y);
  assert.ok(rod);assert.equal(rod.a[2],0);assert.equal(rod.b[2],0);
  const journals=tubes.filter(t=>t.a[0]===0&&t.b[0]===0&&t.a[1]===0&&t.b[1]===0&&t.radius===0.12);
  assert.equal(journals.length,2);
  for(const journal of journals){
   assert.ok(journal.a[2]*journal.b[2]>0,'no central shaft across rod plane');
   assert.ok(Math.min(Math.abs(journal.a[2]),Math.abs(journal.b[2]))>rod.radius);
  }
  const webs=tubes.filter(t=>t.radius===0.14);
  assert.equal(webs.length,2);
  for(const web of webs)assert.ok(Math.abs(web.a[2])>web.radius+rod.radius);
  const pin=tubes.find(t=>t.a[0]===state.crank.x&&t.a[1]===state.crank.y&&t.a[2]===-0.32&&t.b[2]===0.32);
  assert.ok(pin,'offset crank pin connects the webs at the rod big end');
 }
});

test('fixed captions name head-valve and piston-port states accurately',()=>{
 assert.ok(m.getEventCaptions('four',90).includes('Intake valve open; exhaust valve closed'));
 assert.ok(m.getEventCaptions('four',630).includes('Exhaust valve open; intake valve closed'));
 for(const a of [270,450])assert.ok(m.getEventCaptions('four',a).includes('Both valves closed'));
 assert.ok(m.getEventCaptions('two',150).includes('Exhaust port open'));
 assert.ok(m.getEventCaptions('two',150).includes('Transfer port open'));
 assert.ok(m.getEventCaptions('two',245).includes('Transfer port closed'));
 assert.ok(m.getEventCaptions('two',290).includes('Crankcase reed inlet open'));
 assert.ok(m.getEventCaptions('two',90).includes('Crankcase reed inlet closed'));
});
