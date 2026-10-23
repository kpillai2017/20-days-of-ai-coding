/* A small SOFTWARE 3D renderer: geometry really has x/y/z coordinates. We rotate
   an orbit camera, project onto 2D, then paint far faces before near faces.
   No WebGL, downloaded assets, libraries, or pre-rendered movie are involved. */
(() => {
  "use strict";
  const C = { metal: "#9aaec4", dark: "#40566c", piston: "#d7e4ed", rod: "#acbed0",
    fresh: "#66c8ff", transfer: "#77e8b4", exhaust: "#ff8d91", hot: "#ffcb68", gas: "#8c9bb7" };
  const add = (a,b) => a.map((v,i) => v+b[i]);
  const sub = (a,b) => a.map((v,i) => v-b[i]);
  const scale = (a,s) => a.map(v => v*s);
  const dot = (a,b) => a.reduce((s,v,i) => s+v*b[i],0);
  const cross = (a,b) => [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const unit = a => scale(a,1/Math.hypot(...a));

  class EngineRenderer {
    constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.resetView();
    }
    resetView() { this.yaw = 0.38; this.pitch = 0.16; this.zoom = 1; }
    orbit(dx,dy) {
      this.yaw += dx;
      // Avoid pointing exactly along world up, which makes a camera basis singular.
      this.pitch = Math.max(-0.8,Math.min(0.95,this.pitch+dy));
    }
    zoomBy(factor) { this.zoom = Math.max(0.65,Math.min(1.7,this.zoom*factor)); }

    setupCamera() {
      const rect = this.canvas.getBoundingClientRect();
      this.width = Math.max(1,rect.width); this.height = Math.max(1,rect.height);
      const ratio = Math.min(window.devicePixelRatio || 1,2);
      const width = Math.round(this.width*ratio), height = Math.round(this.height*ratio);
      if (this.canvas.width !== width || this.canvas.height !== height) {
        this.canvas.width = width; this.canvas.height = height;
      }
      // Work in CSS pixels; the transform handles high-density screens.
      this.ctx.setTransform(ratio,0,0,ratio,0,0);
      this.target = [0,1.3,0];
      const direction = [Math.sin(this.yaw)*Math.cos(this.pitch),Math.sin(this.pitch),Math.cos(this.yaw)*Math.cos(this.pitch)];
      this.eye = add(this.target,scale(direction,8));
      this.forward = unit(sub(this.target,this.eye));
      this.right = unit(cross(this.forward,[0,1,0]));
      this.up = cross(this.right,this.forward);
      this.focal = Math.min(this.width*0.95,this.height*1.65)*this.zoom;
    }
    project(point) {
      const relative = sub(point,this.eye), depth = dot(relative,this.forward);
      return { x:this.width/2+dot(relative,this.right)*this.focal/depth,
        y:this.height/2-dot(relative,this.up)*this.focal/depth, depth };
    }
    face(vertices,color,alpha=1) { this.faces.push({vertices,color,alpha}); }
    quad(a,b,c,d,color,alpha=1) {
      // Triangles are planar even when a complex surface is curved.
      this.face([a,b,c],color,alpha);this.face([a,c,d],color,alpha);
    }
    box(center,size,color,alpha=1) {
      const [x,y,z]=center,[a,b,c]=size.map(v=>v/2);
      const p=[[-a,-b,-c],[a,-b,-c],[a,b,-c],[-a,b,-c],[-a,-b,c],[a,-b,c],[a,b,c],[-a,b,c]].map(v=>add([x,y,z],v));
      for (const indices of [[0,1,2,3],[4,7,6,5],[0,4,5,1],[3,2,6,7],[0,3,7,4],[1,5,6,2]]) {
        this.quad(...indices.map(i=>p[i]),color,alpha);
      }
    }
    tube(a,b,radius,color,{segments=20,start=0,end=Math.PI*2,caps=true,alpha=1}={}) {
      const axis=unit(sub(b,a));
      const u=unit(cross(axis,Math.abs(axis[1])>0.9?[1,0,0]:[0,1,0]));
      const v=cross(axis,u);
      const point=(center,t)=>add(center,add(scale(u,radius*Math.cos(t)),scale(v,radius*Math.sin(t))));
      for(let i=0;i<segments;i++) {
        const t=start+(end-start)*i/segments,n=start+(end-start)*(i+1)/segments;
        const p=point(a,t),q=point(a,n),r=point(b,n),s=point(b,t);
        this.quad(p,q,r,s,color,alpha);
        if(caps){this.face([a,q,p],color,alpha);this.face([b,s,r],color,alpha);}
      }
    }
    arrow(points,color,label,progress=0) {
      // Arrows are a teaching overlay, deliberately visible through the cutaway.
      // They indicate net flow/force, not measured fluid trajectories.
      this.arrows.push({points,color,label,progress});
    }
    label(point,text,color="#dce8f5") {this.labels.push({point,text,color});}

    build(state,seconds) {
      const top=state.pistonY+0.25;
      // Static rear half of the cylinder is retained; front is removed so the
      // internal mechanism remains visible. Orbiting behind it reveals the shell.
      this.tube([0,1.1,0],[0,2.92,0],0.83,C.dark,{start:-Math.PI/2,end:Math.PI/2,caps:false});
      this.tube([0,2.92,0],[0,3.05,0],0.87,C.metal);
      this.tube([0,state.pistonY-0.18,0],[0,top,0],0.72,C.piston);
      // A narrow dark ring at the piston crown makes its motion easy to follow.
      this.tube([0,top-0.045,0],[0,top,0],0.735,C.dark);
      const crank=[state.crank.x,state.crank.y,0];
      this.tube([0,state.pistonY,0.04],add(crank,[0,0,0.04]),0.105,C.rod);
      this.tube([0,0,-0.36],[0,0,0.4],0.12,C.metal);
      this.tube([0,0,-0.2],[state.crank.x,state.crank.y,-0.2],0.15,C.dark);
      this.tube([state.crank.x,state.crank.y,-0.28],[state.crank.x,state.crank.y,0.2],0.12,C.metal);
      this.tube([0,0,-0.5],[0,0,-0.38],0.67,C.dark);
      this.box([0,-0.83,0],[2.3,0.16,1.5],C.dark);
      // A translucent charge volume is only a phase cue, not a pressure field.
      const gasColor=state.burn>0.1?C.hot:state.charge==="exhaust"?C.exhaust:state.charge==="compressed"?C.hot:C.fresh;
      const gasHeight=Math.max(0.02,2.88-top);
      this.tube([0,top+0.015,0],[0,top+gasHeight,0],0.69,gasColor,{alpha:0.14});
      // Spark plug and brief ignition rays.
      this.tube([0,2.96,0],[0,3.38,0],0.09,C.piston);
      if(state.spark) {
        for(let i=0;i<6;i++) {
          const t=i*Math.PI/3;
          this.arrow([[0,2.84,0],[0.25*Math.cos(t),2.65+0.12*Math.sin(t),0.18]],C.hot,i===0?"Spark":"");
        }
      }
      const pulse=(seconds*0.8)%1;
      if(state.mode==="four") {
        // Schematic poppet valves move DOWN to open into the chamber.
        for(const [x,open,color] of [[-0.47,state.intakeOpen,C.fresh],[0.47,state.exhaustOpen,C.exhaust]]) {
          const y=2.94-(open?0.18:0);
          this.tube([x,y,0],[x,y+0.6,0],0.055,C.metal);
          this.tube([x,y-0.04,0],[x,y+0.025,0],0.19,open?color:C.metal);
        }
        this.tube([-1.5,3.08,0],[-0.47,3.08,0],0.16,C.fresh);
        this.tube([0.47,3.08,0],[1.5,3.08,0],0.16,C.exhaust);
        if(state.intakeOpen) this.arrow([[-1.65,3.18,0.3],[-0.5,3.15,0.3],[-0.35,2.55,0.35]],C.fresh,"Fresh mixture IN",pulse);
        if(state.exhaustOpen) this.arrow([[0.3,2.6,0.35],[0.5,3.18,0.3],[1.65,3.18,0.3]],C.exhaust,"Exhaust OUT",pulse);
      } else {
        // Port roof heights derive from the SAME piston geometry as timing.
        // Crown drops below exhaust roof at 105°, transfer roof at 120°.
        const exhaustY=EngineModel.pistonPosition(105)+0.25;
        const transferY=EngineModel.pistonPosition(120)+0.25;
        this.box([0,-0.05,-0.38],[2.05,1.65,0.18],C.dark);
        this.tube([0.82,exhaustY-0.06,0],[1.55,exhaustY-0.06,0],0.14,C.exhaust);
        const transferPath=[[-0.8,-0.1,0],[-1.18,0.25,0],[-1.18,transferY-0.1,0],[-0.8,transferY-0.1,0]];
        for(let i=1;i<transferPath.length;i++) this.tube(transferPath[i-1],transferPath[i],0.11,C.transfer);
        this.tube([-1.65,0.25,0],[-0.75,0.25,0],0.12,C.fresh);
        // Exposed/covered indicator on the cut cylinder edge, not a head valve.
        this.box([0.79,exhaustY-0.06,0.12],[0.13,0.18,0.22],state.exhaustOpen?C.exhaust:C.dark);
        this.box([-0.79,transferY-0.1,0.12],[0.13,0.18,0.22],state.transferOpen?C.transfer:C.dark);
        if(state.exhaustOpen) this.arrow([[0.15,exhaustY,0.4],[0.8,exhaustY,0.4],[1.65,exhaustY,0.4]],C.exhaust,"Exhaust OUT",pulse);
        if(state.transferOpen) this.arrow([[-0.65,0.15,0.35],[-1.2,0.3,0.35],[-1.2,transferY,0.35],[-0.5,transferY,0.35],[0,transferY+0.45,0.35]],C.transfer,"Crankcase → cylinder",pulse);
        if(state.crankcaseIntakeOpen) this.arrow([[-1.75,0.3,0.4],[-0.55,0.3,0.4]],C.fresh,"Fresh mixture → crankcase",pulse);
        if(state.crankAngle>10 && state.crankAngle<105) this.arrow([[-0.45,0.7,0.45],[-0.45,0.05,0.45]],C.hot,"Crankcase charge squeezed",pulse);
      }
      if(state.phase==="compression") this.arrow([[0,top+0.12,0.8],[0,Math.min(2.8,top+0.48),0.8]],C.hot,"Compression ↑",pulse);
      if(state.phase==="power") this.arrow([[0,2.77,0.8],[0,Math.max(top+0.07,2.1),0.8]],C.hot,"Expansion force ↓",pulse);
      this.label([0,top,0.75],"Piston");
      this.label([state.crank.x,state.crank.y,0.4],"Crank pin");
      this.label([0,3.5,0],state.mode==="four"?"Spark + head valves":"Spark + piston ports");
    }

    render(state,seconds=0) {
      this.setupCamera();this.faces=[];this.arrows=[];this.labels=[];
      this.build(state,seconds);
      const ctx=this.ctx;
      ctx.clearRect(0,0,this.width,this.height);
      const gradient=ctx.createLinearGradient(0,0,0,this.height);
      gradient.addColorStop(0,"#111f31");gradient.addColorStop(1,"#080e18");
      ctx.fillStyle=gradient;ctx.fillRect(0,0,this.width,this.height);
      // Painter's algorithm is intentionally simple. It approximates occlusion;
      // intersecting/transparent faces may show sorting artifacts, unlike a z-buffer.
      const projected=this.faces.map(face=>({...face,p:face.vertices.map(v=>this.project(v))}));
      projected.sort((a,b)=>b.p.reduce((s,p)=>s+p.depth,0)-a.p.reduce((s,p)=>s+p.depth,0));
      for(const face of projected) {
        ctx.beginPath();face.p.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();
        ctx.globalAlpha=face.alpha;ctx.fillStyle=face.color;ctx.fill();
        ctx.strokeStyle="rgba(10,20,32,0.14)";ctx.lineWidth=0.5;ctx.stroke();
      }
      ctx.globalAlpha=1;
      for(const arrow of this.arrows) {
        const points=arrow.points.map(p=>this.project(p));
        ctx.strokeStyle=arrow.color;ctx.fillStyle=arrow.color;ctx.lineWidth=3;
        ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.stroke();
        const end=points.at(-1),before=points.at(-2);
        const t=Math.atan2(end.y-before.y,end.x-before.x);
        ctx.beginPath();ctx.moveTo(end.x,end.y);ctx.lineTo(end.x-11*Math.cos(t-0.45),end.y-11*Math.sin(t-0.45));ctx.lineTo(end.x-11*Math.cos(t+0.45),end.y-11*Math.sin(t+0.45));ctx.closePath();ctx.fill();
        // A travelling dot reinforces direction without implying a flow speed.
        const segment=Math.min(points.length-2,Math.floor(arrow.progress*(points.length-1)));
        const f=arrow.progress*(points.length-1)-segment;
        const a=points[segment],b=points[segment+1];
        ctx.beginPath();ctx.arc(a.x+(b.x-a.x)*f,a.y+(b.y-a.y)*f,4,0,Math.PI*2);ctx.fill();
        if(arrow.label)this.drawLabel(points[0],arrow.label,arrow.color);
      }
      for(const label of this.labels)this.drawLabel(this.project(label.point),label.text,label.color);
      ctx.font="12px system-ui";ctx.fillStyle="#a6b9d0";
      ctx.fillText("3D cutaway · drag / arrow keys to orbit",14,this.height-16);
    }
    drawLabel(point,text,color) {
      const ctx=this.ctx;ctx.font="12px system-ui";
      const w=ctx.measureText(text).width+12;
      const x=Math.max(4,Math.min(this.width-w-4,point.x+10));
      const y=Math.max(18,Math.min(this.height-32,point.y-13));
      ctx.fillStyle="rgba(8,14,24,0.86)";ctx.fillRect(x-4,y-13,w,19);
      ctx.fillStyle=color;ctx.fillText(text,x+2,y);
    }
  }
  globalThis.EngineRenderer=EngineRenderer;
})();
