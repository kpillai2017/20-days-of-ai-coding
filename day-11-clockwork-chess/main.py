"""Pygame controller: human events, cancellable AI, animation and sound.

Rules live in engine.py. Animations preview a legal move on a saved board, then
commit it once, so visual timing never changes what moves are legal.
"""
import argparse
from array import array
from concurrent.futures import ThreadPoolExecutor
import math
import random
import threading

import pygame
from engine import Position, search, other, sq_to_notation
from graphics import Renderer, BG, square_at
from animation import STYLES, IMPACT

LEVELS={'easy':(2,.35),'medium':(3,1.1),'hard':(5,2.5)}


class Sounds:
    """Short original PCM effects. No external recordings or copyrighted assets."""
    def __init__(self,mute=False):
        self.enabled=False;self.available=False;self.effects={}
        if mute:return
        try:
            pygame.mixer.init(frequency=22050,size=-16,channels=1,buffer=512)
            rate=pygame.mixer.get_init()[0];rng=random.Random(11)
            for name,freq,duration in [('move',260,.13),('capture',95,.40),('check',620,.26),('end',170,.65)]:
                samples=array('h')
                for i in range(int(rate*duration)):
                    t=i/rate;envelope=(1-t/duration)**2
                    tone=math.sin(math.tau*freq*t)+.3*math.sin(math.tau*freq*1.5*t)
                    noise=rng.uniform(-1,1)*(.8 if name=='capture' else .03)
                    samples.append(int((tone+noise)*envelope*6000))
                self.effects[name]=pygame.mixer.Sound(buffer=samples)
            # Every moving/attacking type has an original timbre and envelope.
            # No prerecorded Battle Chess sound is loaded or approximated from
            # a sample: frequency sweeps/noise below are generated from scratch.
            recipes={'bash':(115,.35),'charge':(190,.45),'spell':(550,.48),
                     'rumble':(60,.50),'lightning':(820,.42),'sword':(1050,.30)}
            recipes.update({'move_'+kind:(170+i*47,.16) for i,kind in enumerate('pnbrqk')})
            for name,(freq,duration) in recipes.items():
                samples=array('h')
                for i in range(int(rate*duration)):
                    t=i/rate;phase=t/duration
                    fade=(1-phase)**2
                    pitch=freq*(1+phase*(1.8 if name in ('spell','lightning') else -.5))
                    tone=math.sin(math.tau*pitch*t)
                    metallic=math.sin(math.tau*pitch*2.73*t)*.35
                    noise=rng.uniform(-1,1)*(.85 if name in ('bash','rumble','lightning') else .13)
                    pulse=(.6+.4*math.sin(math.tau*18*t)) if name=='charge' else 1
                    samples.append(int((tone*.6+metallic+noise)*fade*pulse*6500))
                self.effects[name]=pygame.mixer.Sound(buffer=samples)
            self.enabled=self.available=True
        except pygame.error:
            pygame.mixer.quit()

    def play(self,name):
        if self.enabled:self.effects[name].play()

    def toggle(self):
        if self.available:self.enabled=not self.enabled


class App:
    def __init__(self,mute=False,ai=True):
        self.renderer=Renderer();self.sounds=Sounds(mute)
        self.worker=ThreadPoolExecutor(max_workers=1)
        self.future=None;self.stop=None;self.generation=0
        self.search_kind=None;self.hint_move=None
        self.ai_enabled=ai;self.human_side='w';self.level='medium'
        self.yaw=0.;self.zoom=1.;self.tilt=.5
        self.pointer_start=None;self.pointer_last=None;self.pointer_dragging=False
        self.view='3d';self.flipped=True;self.animation=None;self.promotion=None
        self.position=Position();self.selected=None;self.legal=[]
        self.last_move=None;self.moves=[];self.status=''
        self.refresh()

    def refresh(self):
        self.hint_move=None
        self.legal=self.position.legal_moves()
        self.result=self.position.outcome(self.legal)
        self.status=self.result or ('Check — protect your king.' if self.position.in_check() else 'Select a piece, then a green destination.')

    def cancel_search(self):
        if self.stop:self.stop.set()
        if self.future:self.future.cancel()
        self.future=None;self.stop=None;self.search_kind=None;self.hint_move=None;self.generation+=1

    def new(self):
        self.cancel_search()
        self.position=Position();self.animation=None;self.promotion=None
        self.selected=None;self.last_move=None;self.moves=[]
        self.refresh()

    def is_human_turn(self):
        return not self.ai_enabled or self.position.side==self.human_side

    def action(self,name):
        # Safe destructive actions invalidate a pending worker result. Only one
        # worker exists; its stop Event is checked at every recursive node.
        if name in ('rotate_left','rotate_right','zoom_out','zoom_in','camera_reset'):
            if self.view!='3d':return
            if name=='camera_reset':self.yaw,self.zoom,self.tilt=0.,1.,.5
            elif name.startswith('rotate'):self.yaw=(self.yaw+(-.18 if name=='rotate_left' else .18))%math.tau
            else:self.zoom=max(.65,min(1.5,self.zoom*(1.12 if name=='zoom_in' else 1/1.12)))
        elif name=='hint':
            if self.animation or self.future or self.promotion:
                return  # Do not overwrite another search or interrupt a move.
            if self.result:
                self.status=self.result
                return
            if not self.is_human_turn():
                self.status='Wait for the computer move before requesting a hint.'
                return
            self.hint_move=None
            self.stop=threading.Event()
            self.search_kind='hint'
            depth,seconds=LEVELS[self.level]
            self.future=self.worker.submit(search,self.position.clone(),depth,seconds,self.stop)
            self.status='Finding a suggested move...'
        elif name=='new':self.new()
        elif name=='mode':self.ai_enabled=not self.ai_enabled;self.new()
        elif name=='side':
            self.human_side=other(self.human_side);self.flipped=self.human_side=='w';self.new()
        elif name=='level':
            names=list(LEVELS);self.level=names[(names.index(self.level)+1)%len(names)]
            self.cancel_search();self.refresh()
        elif name=='view':self.view='2d' if self.view=='3d' else '3d'
        elif name=='flip':self.flipped=not self.flipped
        elif name=='sound':
            self.sounds.toggle()
            if not self.sounds.available:self.status='Audio unavailable or disabled with --mute; restart without --mute to enable.'
        elif name=='undo':
            self.cancel_search()
            if self.animation:
                # Preview has not changed the board, so cancelling IS the undo.
                ai_preview = self.ai_enabled and self.position.side != self.human_side
                self.animation=None
                if ai_preview and self.position.history:
                    self.position.pop()
                    if self.moves:self.moves.pop()
            elif self.position.history:
                self.position.pop()
                if self.moves:self.moves.pop()
                # In AI mode rewind the pair (or pending human move) so the
                # human can choose again, instead of the AI instantly replaying.
                if self.ai_enabled and self.position.side!=self.human_side and self.position.history:
                    self.position.pop()
                    if self.moves:self.moves.pop()
            self.promotion=None;self.selected=None;self.last_move=None;self.refresh()
        elif name.startswith('promote_') and self.promotion:
            choice=name[-1]
            move=next((m for m in self.promotion if m.promotion==choice),None)
            if move:self.promotion=None;self.animate(move)

    def click(self,pos):
        for name,rect in self.renderer.buttons.items():
            if rect.collidepoint(pos):self.action(name);return
        if self.animation or self.future or self.result or self.promotion or not self.is_human_turn():return
        square=square_at(pos,self.flipped,self.view,self.yaw,self.zoom,self.tilt)
        if square is None:self.selected=None;return
        if self.selected is not None:
            options=[m for m in self.legal if m.from_sq==self.selected and m.to_sq==square]
            if options:
                if len(options)>1:self.promotion=options;self.status='Choose Q, R, B or N for promotion.'
                else:self.animate(options[0])
                return
        piece=self.position.board[square]
        self.selected=square if piece!='.' and (piece.isupper()==(self.position.side=='w')) else None

    def pointer_down(self,pos):
        """Delay a board click until release so dragging cannot make a move.

        Buttons act immediately. Only a press on a 3D board square can start an
        orbit gesture; the sidebar and letterbox margins never rotate the view.
        """
        if any(rect.collidepoint(pos) for rect in self.renderer.buttons.values()):
            self.click(pos)
            return
        if self.view=='3d' and pygame.Rect(0,115,870,628).collidepoint(pos) and square_at(pos,self.flipped,self.view,self.yaw,self.zoom,self.tilt) is not None:
            self.pointer_start=pos
            self.pointer_last=pos
            self.pointer_dragging=False
        else:
            self.click(pos)

    def pointer_motion(self,pos):
        if self.pointer_start is None:return
        if not self.pointer_dragging:
            dx,dy=pos[0]-self.pointer_start[0],pos[1]-self.pointer_start[1]
            if math.hypot(dx,dy)<5:return  # Small hand jitter is still a click.
            self.pointer_dragging=True
        else:
            dx,dy=pos[0]-self.pointer_last[0],pos[1]-self.pointer_last[1]
        self.orbit(dx,dy)
        self.pointer_last=pos

    def pointer_up(self,pos):
        if self.pointer_start is None:return
        # Include the final displacement, even if SDL coalesced motion events.
        self.pointer_motion(pos)
        click=not self.pointer_dragging
        origin=self.pointer_start
        self.pointer_cancel()
        if click:self.click(origin)

    def pointer_cancel(self):
        self.pointer_start=None;self.pointer_last=None;self.pointer_dragging=False

    def orbit(self,dx,dy):
        """Logical-pixel drag deltas; tilt stays invertible, never edge-on."""
        if self.view=='3d':
            self.yaw=(self.yaw+dx*.008)%math.tau
            self.tilt=max(.28,min(.85,self.tilt+dy*.003))

    def key(self,key):
        camera={pygame.K_LEFT:'rotate_left',pygame.K_RIGHT:'rotate_right',pygame.K_MINUS:'zoom_out',pygame.K_EQUALS:'zoom_in',pygame.K_PLUS:'zoom_in',pygame.K_KP_PLUS:'zoom_in',pygame.K_KP_MINUS:'zoom_out',pygame.K_HOME:'camera_reset'}
        if key in camera:self.action(camera[key]);return
        if key in (pygame.K_UP,pygame.K_DOWN):
            self.orbit(0,-12 if key==pygame.K_UP else 12)
            return
        if self.promotion and key in (pygame.K_q,pygame.K_r,pygame.K_b,pygame.K_n):
            self.action('promote_'+pygame.key.name(key));return
        actions={pygame.K_h:'hint',pygame.K_v:'view',pygame.K_r:'new',pygame.K_u:'undo',pygame.K_f:'flip',pygame.K_m:'sound',pygame.K_TAB:'mode'}
        if key in actions:self.action(actions[key])

    def animate(self,move):
        if move not in self.legal:raise ValueError('Only legal moves can animate')
        self.hint_move=None
        board=self.position.board[:];piece=board[move.from_sq]
        capture_sq=move.to_sq+(-8 if piece.isupper() else 8) if move.en_passant else move.to_sq
        captured=board[capture_sq]
        rook_from=move.from_sq+(3 if move.to_sq>move.from_sq else -4)
        self.animation={'move':move,'board':board,'piece':piece,'captured':captured,
            'capture_sq':capture_sq,'rook_from':rook_from,'rook_to':(move.from_sq+move.to_sq)//2,
            'time':0.,'duration':STYLES[piece.lower()][1] if captured!='.' else (.8 if piece.lower()=='n' else .65),'impact':False}
        self.selected=None
        self.status=STYLES[piece.lower()][0]+'...' if captured!='.' else 'Moving...'
        if captured=='.':self.sounds.play('move_'+piece.lower())

    def update(self,dt):
        if self.animation:
            animation=self.animation;animation['time']+=max(0,min(dt,.1))
            if animation['captured']!='.' and not animation['impact'] and animation['time']>=animation['duration']*IMPACT:
                animation['impact']=True;self.sounds.play(STYLES[animation['piece'].lower()][2])
            if animation['time']>=animation['duration']:
                move=animation['move'];self.position.push(move)
                self.moves.append(move.uci());self.last_move=move;self.animation=None
                self.refresh()
                if self.result:self.sounds.play('end')
                elif self.position.in_check():self.sounds.play('check')
            return
        if self.future and self.future.done():
            future=self.future;kind=self.search_kind
            self.future=None;self.search_kind=None
            try:
                result=future.result()
                if result.move is not None and result.move in self.legal:
                    if kind=='hint':
                        self.hint_move=result.move
                        self.selected=result.move.from_sq
                        promotion=('; promote to '+result.move.promotion.upper()) if result.move.promotion else ''
                        self.status=f'Hint: {sq_to_notation(result.move.from_sq)} to {sq_to_notation(result.move.to_sq)}{promotion}. Highlighted only; you choose whether to play it.'
                    else:
                        self.animate(result.move)
            except Exception as problem:
                # Expose failures rather than silently making an arbitrary move.
                self.status=f'{"Hint" if kind=="hint" else "AI"} search failed: {problem}.'
                if kind!='hint':self.ai_enabled=False
        if not self.animation and not self.future and not self.result and not self.promotion and not self.is_human_turn():
            depth,seconds=LEVELS[self.level]
            self.stop=threading.Event()
            self.search_kind='ai'
            self.future=self.worker.submit(search,self.position.clone(),depth,seconds,self.stop)
            self.status=f'Computer thinking ({self.level})...'

    def close(self):
        self.cancel_search();self.worker.shutdown(wait=True)


def main(argv=None):
    parser=argparse.ArgumentParser(description='Original animated chess with a VICE-inspired engine')
    parser.add_argument('--mute',action='store_true')
    parser.add_argument('--two-player',action='store_true')
    parser.add_argument('--frames',type=int,help='quit after N frames (testing)')
    args=parser.parse_args(argv)
    if args.frames is not None and args.frames<=0:parser.error('--frames must be positive')
    pygame.display.init();pygame.font.init()
    window=pygame.display.set_mode((1240,800),pygame.RESIZABLE)
    pygame.display.set_caption('Day 11 · Clockwork Chess')
    clock=pygame.time.Clock();app=App(args.mute,not args.two_player)
    running=True;frames=0
    try:
        while running:
            dt=clock.tick(60)/1000
            width,height=window.get_size();scale=min(width/1240,height/800)
            size=(max(1,round(1240*scale)),max(1,round(800*scale)))
            ox,oy=(width-size[0])//2,(height-size[1])//2
            for event in pygame.event.get():
                if event.type==pygame.QUIT:running=False
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE:running=False
                    else:app.key(event.key)
                elif event.type==pygame.MOUSEWHEEL:
                    mx,my=pygame.mouse.get_pos()
                    if 0<=(mx-ox)/scale<870 and 115<=(my-oy)/scale<743:
                        for _ in range(min(8,abs(event.y))):app.action('zoom_in' if event.y>0 else 'zoom_out')
                elif event.type==pygame.WINDOWFOCUSLOST:
                    app.pointer_cancel()
                elif event.type==pygame.MOUSEMOTION:
                    app.pointer_motion(((event.pos[0]-ox)/scale,(event.pos[1]-oy)/scale))
                elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                    app.pointer_down(((event.pos[0]-ox)/scale,(event.pos[1]-oy)/scale))
                elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
                    app.pointer_up(((event.pos[0]-ox)/scale,(event.pos[1]-oy)/scale))
            app.update(dt)
            image=app.renderer.draw(app)
            window.fill(BG);window.blit(pygame.transform.smoothscale(image,size),(ox,oy))
            pygame.display.flip();frames+=1
            if args.frames and frames>=args.frames:running=False
    finally:app.close();pygame.quit()
    return 0


if __name__=='__main__':raise SystemExit(main())
