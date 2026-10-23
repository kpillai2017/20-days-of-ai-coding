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
