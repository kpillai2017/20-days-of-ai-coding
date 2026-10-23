/* Events and time live here; engine.js contains mechanics, renderer.js contains
   geometry. Keeping them separate lets tests examine mechanics without a browser. */
(() => {
  "use strict";
  const {getState,getStages,cycleDegrees,getEventCaptions}=globalThis.EngineModel;
  const canvas=document.getElementById("engine-view");
  const renderer=new globalThis.EngineRenderer(canvas);
  const playButton=document.getElementById("play");
  const angleInput=document.getElementById("angle");
  const speedInput=document.getElementById("speed");
  const stagePanel=document.getElementById("stages");
  const announcement=document.getElementById("announcement");
  const reduced=window.matchMedia("(prefers-reduced-motion: reduce)");
  let mode="four",angle=0,speed=1,playing=!reduced.matches;
  let lastTime=null,activePointer=null,previous=null,lastStage="",lastCaption="";
  let effectSeconds=0;

  function setPlaying(value) {
    playing=value;lastTime=null;
    playButton.textContent=playing?"Pause":"Play";
    playButton.setAttribute("aria-pressed",String(playing));
  }
  function text(id,value) {document.getElementById(id).textContent=value;}
  function paint() {
    const state=getState(mode,angle);
    renderer.render(state,effectSeconds);
    angleInput.value=String(Math.floor(state.angle));
    text("angle-output",`${Math.floor(state.angle)}° / ${state.cycleDegrees}°`);
    text("angle-value",`${Math.floor(state.angle)}°`);
    text("phase-title",state.title);
    // This caption belongs to the VIEWPORT, not a projected engine vertex:
    // it stays still while the piston moves and while the camera orbits.
    const down=state.crankAngle<180;
    const stroke=mode==="four"
      ? ["Intake stroke","Compression stroke","Power stroke","Exhaust stroke"][state.stageIndex]
      : down?"Power / transfer stroke":"Compression / induction stroke";
    text("stroke-name",stroke);
    text("stroke-direction",state.pistonDirection==="turning"?"At dead centre":down?"Downstroke":"Upstroke");
    text("stroke-events",getEventCaptions(mode,angle).join("\n"));
    // Live regions announce stage changes, not a caption at every animation frame.
    if(lastCaption!==state.caption) {text("caption",state.caption);lastCaption=state.caption;}
    text("direction",state.pistonDirection==="turning"?"At dead centre":state.pistonDirection==="down"?"Moving down ↓":"Moving up ↑");
    text("intake-state",(mode==="four"?state.intakeOpen:state.crankcaseIntakeOpen)?"Open":"Closed");
    text("exhaust-state",state.exhaustOpen?"Open":"Closed");
    text("transfer-state",state.transferOpen?"Open":"Closed");
    text("spark-state",state.spark?"Ignition cue":"Off");
    for(const button of stagePanel.children)button.setAttribute("aria-pressed",String(Number(button.dataset.index)===state.stageIndex));
    const stage=`${mode}:${state.phase}`;
    if(lastStage!==stage) {announcement.textContent=`${mode==="four"?"Four":"Two"}-stroke: ${state.title}.`;lastStage=stage;}
  }
  function choose(nextMode) {
    mode=nextMode;angle=0;effectSeconds=0;lastTime=null;
    angleInput.max=String(cycleDegrees(mode)-1);
    document.getElementById("four").setAttribute("aria-pressed",String(mode==="four"));
    document.getElementById("two").setAttribute("aria-pressed",String(mode==="two"));
    canvas.setAttribute("aria-label",`Rotatable 3D cutaway of a ${mode==="four"?"four":"two"}-stroke engine`);
    text("cycle-label",mode==="four"?"720° · two crank revolutions":"360° · one crank revolution");
    text("intake-label",mode==="four"?"Intake valve":"Crankcase reed inlet");
    text("exhaust-label",mode==="four"?"Exhaust valve":"Exhaust port");
    document.getElementById("transfer-row").hidden=mode!=="two";
    stagePanel.replaceChildren();
    getStages(mode).forEach((stage,index)=>{
      const button=document.createElement("button");button.type="button";
      button.textContent=stage.title;button.dataset.index=String(index);
      button.addEventListener("click",()=>{setPlaying(false);angle=stage.angle;paint();});
      stagePanel.append(button);
    });
    paint();
  }
  document.getElementById("four").addEventListener("click",()=>choose("four"));
  document.getElementById("two").addEventListener("click",()=>choose("two"));
  playButton.addEventListener("click",()=>setPlaying(!playing));
  document.getElementById("step").addEventListener("click",()=>{setPlaying(false);angle=(angle+15)%cycleDegrees(mode);paint();});
  document.getElementById("reset-cycle").addEventListener("click",()=>{setPlaying(false);angle=0;effectSeconds=0;paint();});
  angleInput.addEventListener("input",()=>{setPlaying(false);angle=Number(angleInput.value);paint();});
  speedInput.addEventListener("input",()=>{speed=Number(speedInput.value);text("speed-output",`${speed.toFixed(1)}×`);});
  const orbit=(x,y)=>{renderer.orbit(x,y);paint();};
  for(const [id,x,y] of [["orbit-left",-0.15,0],["orbit-right",0.15,0],["orbit-up",0,0.1],["orbit-down",0,-0.1]]) {
    document.getElementById(id).addEventListener("click",()=>orbit(x,y));
  }
  for(const [id,factor] of [["zoom-in",1.1],["zoom-out",1/1.1]])document.getElementById(id).addEventListener("click",()=>{renderer.zoomBy(factor);paint();});
  document.getElementById("reset-view").addEventListener("click",()=>{renderer.resetView();paint();});
  canvas.addEventListener("keydown",event=>{
    const directions={ArrowLeft:[-0.12,0],ArrowRight:[0.12,0],ArrowUp:[0,0.1],ArrowDown:[0,-0.1]};
    if(directions[event.key]){event.preventDefault();orbit(...directions[event.key]);}
  });
  canvas.addEventListener("pointerdown",event=>{
    if(!event.isPrimary||event.button!==0||activePointer!==null)return;
    activePointer=event.pointerId;previous=[event.clientX,event.clientY];
    canvas.setPointerCapture(event.pointerId);canvas.focus({preventScroll:true});
  });
  canvas.addEventListener("pointermove",event=>{
    if(event.pointerId!==activePointer)return;
    orbit((event.clientX-previous[0])*0.008,(event.clientY-previous[1])*0.006);
    previous=[event.clientX,event.clientY];
  });
  const end=event=>{if(event.pointerId===activePointer){activePointer=null;previous=null;}};
  for(const event of ["pointerup","pointercancel","lostpointercapture"])canvas.addEventListener(event,end);
  canvas.addEventListener("wheel",event=>{event.preventDefault();renderer.zoomBy(event.deltaY<0?1.06:1/1.06);paint();},{passive:false});
  window.addEventListener("resize",paint);
  document.addEventListener("visibilitychange",()=>{lastTime=null;});
  reduced.addEventListener("change",event=>{if(event.matches){setPlaying(false);paint();}});

  function animate(now) {
    // Elapsed seconds, not frame count, control speed. Clamp stalls; this visual
    // teaching animation skips catch-up rather than racing through hidden phases.
    if(lastTime!==null&&playing) {
      const dt=Math.min((now-lastTime)/1000,0.05);
      angle=(angle+dt*90*speed)%cycleDegrees(mode); // 360° / 4 seconds at 1×.
      effectSeconds+=dt*speed;
      paint();
    }
    lastTime=now;window.requestAnimationFrame(animate);
  }
  setPlaying(playing);choose(mode);window.requestAnimationFrame(animate);
})();
