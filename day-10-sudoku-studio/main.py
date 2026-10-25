"""Sudoku Studio: a Pygame view/controller around a pure Python model.

Generation and solving run in a single background worker so a difficult search
never stops the window responding. Only the MAIN thread draws or edits a game.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor

import pygame
from sudoku import Puzzle, Session, candidates, conflicts, generate_puzzle, solve

WIDTH, HEIGHT = 1040, 790
GRID = pygame.Rect(32, 110, 630, 630)
CELL = 70
BG = (238, 242, 248)
INK = (32, 46, 66)
BLUE = (25, 90, 168)
WHITE = (255, 255, 255)
RED = (176, 42, 54)


class App:
    """UI state is separate from Session's board/notes/undo state."""
    def __init__(self, seed=None):
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.font = pygame.font.Font(None, 30)
        self.small = pygame.font.Font(None, 23)
        self.digits = pygame.font.Font(None, 51)
        self.tiny = pygame.font.Font(None, 22)
        self.title = pygame.font.Font(None, 45)
        self.worker = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.operation = None
        self.session = None
        self.seed = seed
        self.generation = 0
        self.level = 'easy'
        self.show_candidates = False
        self.paused = False
        self.seconds = 0.0
        self.message = 'Choose a difficulty, then New puzzle.'
        self.buttons = {}
        self.new_puzzle()

    @property
    def busy(self):
        return self.future is not None

    def new_puzzle(self):
        if self.busy:
            return
        # A base seed gives a reproducible SERIES, not the same puzzle forever.
        seed = None if self.seed is None else self.seed + self.generation
        self.generation += 1
        self.operation = 'generate'
        self.future = self.worker.submit(generate_puzzle, self.level, seed)
        self.message = f'Generating {self.level} / checking uniqueness...'

    def poll(self):
        """Called each frame. A worker result crosses back to the main thread."""
        if self.future is None or not self.future.done():
            return
        future, operation = self.future, self.operation
        self.future = None
        try:
            result = future.result()
            if operation == 'generate':
                self.session = Session(result)
                self.level = result.difficulty
                self.seconds = 0
                self.paused = False
                self.message = 'Unique puzzle ready. Select a cell and enter 1-9.'
            elif result is None:
                self.message = 'No solution with these entries. Undo or Reset, then try again.'
            else:
                # The worker solves a COPY. No Pygame calls or shared board edits
                # occur there, and editing is locked while the job is running.
                self.session.apply_solution(result)
                self.message = 'One solution revealed; custom boards may have others. Undo restores entries.' if self.session.puzzle.difficulty == 'custom' else 'Solution revealed. Undo restores your previous board.'
        except Exception as problem:
            self.message = f'Could not finish: {problem}'

    def action(self, name):
        if self.busy:
            return
        if name == 'custom':
            blank = [[0]*9 for _ in range(9)]
            self.session = Session(Puzzle(blank, [row[:] for row in blank], 'custom', 0))
            self.seconds = 0
            self.paused = False
            self.message = 'Custom board: enter clues as editable values, then Solve. Uniqueness is not guaranteed.'
            return
        if name in ('easy','medium','hard'):
            self.level = name
            self.new_puzzle()
            return
        if name == 'new':
            self.new_puzzle()
            return
        if self.session is None:
            return
        if name == 'pause':
            self.paused = not self.paused
            return
        if self.paused:
            return
        session = self.session
        if name == 'notes':
            session.note_mode_toggle()
            self.message = 'Pencil marks on.' if session.note_mode else 'Number entry on.'
        elif name == 'candidates':
            self.show_candidates = not self.show_candidates
        elif name == 'undo':
            self.message = 'Undone.' if session.undo() else 'Nothing to undo.'
        elif name == 'reset':
            session.reset()
            self.seconds = 0
            self.message = 'Original clues restored. Notes and undo history cleared.'
        elif name == 'hint':
            if session.puzzle.difficulty == 'custom':
                self.message = 'Hints use a generated unique solution. Custom boards: use Solve instead.'
                return
            self.message = 'One value revealed (not a logical deduction).' if session.hint() else 'Already complete.'
        elif name == 'solve':
            self.operation = 'solve'
            self.future = self.worker.submit(solve, [row[:] for row in session.board])
            self.message = 'Searching for a solution using your current entries...'
        elif name == 'erase':
            session.enter(0)
        elif name.isdigit():
            self.enter(int(name))

    def enter(self, value):
        if self.busy or self.paused or self.session is None:
            return
        if self.session.enter(value):
            self.message = 'Pencil mark changed.' if self.session.note_mode else 'Value entered. Red marks show duplicates, not every mistake.'
        else:
            self.message = 'Clues are fixed; select an editable cell.' if self.session.is_given(*self.session.selected) else 'No change.'

    def key(self, event):
        if event.key in (pygame.K_p, pygame.K_SPACE):
            self.action('pause')
            return
        shortcuts = {pygame.K_e:'custom', pygame.K_n:'new', pygame.K_m:'notes', pygame.K_c:'candidates',
                     pygame.K_h:'hint', pygame.K_s:'solve', pygame.K_z:'undo',
                     pygame.K_r:'reset', pygame.K_BACKSPACE:'erase', pygame.K_DELETE:'erase', pygame.K_0:'erase'}
        if event.key in shortcuts:
            self.action(shortcuts[event.key])
            return
        # event.unicode handles both number row and keypad in normal NumLock use.
        text = getattr(event, 'unicode', '')
        keypad = {getattr(pygame, f'K_KP{i}'):i for i in range(1,10)}
        if text in '123456789' and len(text) == 1:
            self.enter(int(text))
        elif event.key in keypad:
            self.enter(keypad[event.key])
        elif not self.busy and not self.paused and self.session:
            r,c = self.session.selected
            moves = {pygame.K_UP:(-1,0),pygame.K_DOWN:(1,0),pygame.K_LEFT:(0,-1),pygame.K_RIGHT:(0,1),pygame.K_TAB:(0,-1 if event.mod & pygame.KMOD_SHIFT else 1)}
            if event.key in moves:
                dr,dc = moves[event.key]
                self.session.select((r+dr)%9,(c+dc)%9)

    def click(self, pos):
        for name, rect in self.buttons.items():
            if rect.collidepoint(pos):
                self.action(name)
                return
        if not self.busy and not self.paused and self.session and GRID.collidepoint(pos):
            self.session.select(int((pos[1]-GRID.y)//CELL),int((pos[0]-GRID.x)//CELL))

    def text(self, value, pos, color=INK, font=None, center=False):
        image = (font or self.font).render(str(value),True,color)
        self.canvas.blit(image,image.get_rect(center=pos) if center else pos)

    def button(self, name, label, rect, active=False):
        self.buttons[name] = pygame.Rect(rect)
        pygame.draw.rect(self.canvas, BLUE if active else WHITE, rect, border_radius=8)
        pygame.draw.rect(self.canvas, BLUE, rect, 1, border_radius=8)
        self.text(label,pygame.Rect(rect).center,WHITE if active else INK,self.small,True)

    def wrap(self, text, x, y, width, color=INK):
        """Word-wrap status/help text; no silent clipping on long messages."""
        line = ''
        for word in text.split():
            trial = (line+' '+word).strip()
            if self.small.size(trial)[0] > width and line:
                self.text(line,(x,y),color,self.small)
                y += 23
                line = word
            else:
                line = trial
        self.text(line,(x,y),color,self.small)
        return y+23

    def draw(self):
        self.canvas.fill(BG)
        self.buttons = {}
        self.text('SUDOKU STUDIO',(32,25),font=self.title)
        self.text('DAY 10 / GENERATE • PLAY • SOLVE',(34,70),font=self.small)
        for i,level in enumerate(('easy','medium','hard')):
            self.button(level,level.title(),(697+i*106,30,98,40),self.level==level)
        self.button('custom','Custom board [E]',(484,30,178,40))
        session = self.session
        if session:
            puzzle = session.puzzle  # Copy the protected original once per frame.
            bad = conflicts(session.board)
            sr,sc = session.selected
            selected_value = session.board[sr][sc]
            for r in range(9):
                for c in range(9):
                    rect = pygame.Rect(GRID.x+c*CELL,GRID.y+r*CELL,CELL,CELL)
                    color = WHITE
                    if r==sr or c==sc or (r//3,c//3)==(sr//3,sc//3): color=(228,236,248)
                    if selected_value and session.board[r][c]==selected_value: color=(204,226,250)
                    if (r,c)==(sr,sc): color=(172,208,246)
                    if (r,c) in bad: color=(255,218,220)
                    pygame.draw.rect(self.canvas,color,rect)
                    if self.paused: continue  # Hide puzzle to make pause honest.
                    value = session.board[r][c]
                    if value:
                        ink = RED if (r,c) in bad else INK if session.is_given(r,c) else BLUE
                        self.text(value,rect.center,ink,self.digits,True)
                    else:
                        marks = session.notes.get((r,c),set())
                        automatic = self.show_candidates and not marks
                        if automatic: marks=candidates(session.board,r,c)
                        for value in sorted(marks):
                            px = rect.x+((value-1)%3)*23+12
                            py = rect.y+((value-1)//3)*23+12
                            self.text(value,(px,py),(91,116,111) if automatic else BLUE,self.tiny,True)
            self.text(f'{puzzle.difficulty.title()} • {puzzle.clues} clues',(698,92),font=self.small)
            self.text(f'{int(self.seconds)//60:02d}:{int(self.seconds)%60:02d}',(947,92),font=self.small)
        else:
            pygame.draw.rect(self.canvas,WHITE,GRID)
        for i in range(10):
            thick=3 if i%3==0 else 1
            pygame.draw.line(self.canvas,INK,(GRID.x+i*CELL,GRID.y),(GRID.x+i*CELL,GRID.bottom),thick)
            pygame.draw.line(self.canvas,INK,(GRID.x,GRID.y+i*CELL),(GRID.right,GRID.y+i*CELL),thick)
        labels=[('new','New [N]'),('undo','Undo [Z]'),('notes','Pencil [M]'),('candidates','Candidates [C]'),('hint','Hint [H]'),('solve','Solve [S]'),('reset','Reset [R]'),('pause','Resume [P]' if self.paused else 'Pause [P]')]
        for i,(name,label) in enumerate(labels):
            active=(name=='notes' and session and session.note_mode) or (name=='candidates' and self.show_candidates)
            self.button(name,label,(697+(i%2)*165,133+(i//2)*50,155,40),active)
        self.text('Select a digit',(698,349),font=self.small)
        for i in range(9):
            self.button(str(i+1),str(i+1),(697+(i%3)*108,379+(i//3)*43,98,36))
        self.button('erase','Erase [Delete / 0]',(697,518,314,40))
        y=self.wrap(self.message,697,578,310,BLUE)
        if session and session.complete and not self.busy:
            y=self.wrap('Complete — assisted.' if session.assisted else 'Complete — well done!',697,y+9,310,BLUE)
        self.wrap('Difficulty uses clue-count bands, not a guaranteed human solving grade.',697,max(y+10,677),310)
        self.text('Click a cell • 1–9 enter • arrows move • Esc quit',(32,759),font=self.small)
        if self.paused or (self.busy and self.session is None):
            cover=pygame.Surface(GRID.size,pygame.SRCALPHA)
            cover.fill((238,242,248,235))
            self.canvas.blit(cover,GRID.topleft)
            self.text('PAUSED' if self.paused else 'GENERATING...',GRID.center,BLUE,self.title,True)
        return self.canvas

    def close(self):
        # Jobs are bounded. Waiting avoids leaving background generation running
        # after the window closes; no new jobs are accepted after this call.
        self.worker.shutdown(wait=True)


def main(argv=None):
    parser=argparse.ArgumentParser(description='Sudoku generator, player and solver')
    parser.add_argument('--seed',type=int,help='reproducible puzzle series')
    parser.add_argument('--frames',type=int,help='exit after N frames (headless testing)')
    args=parser.parse_args(argv)
    if args.frames is not None and args.frames<=0: parser.error('--frames must be positive')
    pygame.display.init(); pygame.font.init()
    window=pygame.display.set_mode((WIDTH,HEIGHT),pygame.RESIZABLE)
    pygame.display.set_caption('Day 10 · Sudoku Studio')
    clock=pygame.time.Clock()
    app=App(args.seed)
    running=True
    frame_count=0
    try:
        while running:
            dt=min(clock.tick(60)/1000,.1)
            w,h=window.get_size()
            scale=min(w/WIDTH,h/HEIGHT)
            size=(max(1,round(WIDTH*scale)),max(1,round(HEIGHT*scale)))
            ox,oy=(w-size[0])//2,(h-size[1])//2
            for event in pygame.event.get():
                if event.type==pygame.QUIT: running=False
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE: running=False
                    else: app.key(event)
                elif event.type==pygame.WINDOWFOCUSLOST: app.paused=True
                elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                    app.click(((event.pos[0]-ox)/scale,(event.pos[1]-oy)/scale))
            app.poll()
            if app.session and not app.busy and not app.paused and not app.session.complete:
                app.seconds+=dt
            image=app.draw()
            window.fill(BG)
            window.blit(pygame.transform.smoothscale(image,size),(ox,oy))
            pygame.display.flip()
            frame_count+=1
            if args.frames and frame_count>=args.frames: running=False
    finally:
        app.close()
        pygame.quit()
    return 0


if __name__=='__main__':
    raise SystemExit(main())
