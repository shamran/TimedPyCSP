from pycsp.simulation import *
import random
from random import choice as randomchoice 
from numpy import *
import pygame, sys, os
from pygame.locals import *

EMPTY, FISH, SHARK = range(3)
TYPE, AGE, MOVED, STARVED  = range(4)

type =  {
      0 : "EMPTY",
      1 : "FISH",
      2 : "SHARK"
      }

color  = {
    "blue": (0,0,205),
    "red" : (255,0,0)
    }

def _element(element):
  return "%s:age:%i moved:%i starved:%i"%(type[element[TYPE]],element[AGE],element[MOVED],element[STARVED])

class Point:
  def __init__(self,_x,_y):
    self.x = _x
    self.y = _y
  def __repr__(self):
    return "(%i,%i)"%(x,y)
  def getX(self):
    return self.x
  def getY(self):
    return self.y
  def to_gui(self):
    return (self.x*multiplier,self.y*multiplier)


@process
def worldpart (part_id):

  #indices for working in a shared matrix:
  part_width = (world_width/world_parts)-2
  start_col = part_id*(part_width+2)
  right_shadow_col = (start_col+part_width)%world_width
  print part_width,start_col, right_shadow_col
  @io
  def main_iteration():
      for i in range(world_height):
        for j in range(start_col,start_col+part_width+2):
          f = world[j][i]
          f[MOVED] = 0

      for i in range(world_height):
        for j in range(start_col,start_col+part_width):
          element_iteration(Point(j,i))

  def element_iteration(p):
    f = world[p.getX()][p.getY()]
    if f[TYPE] == EMPTY or f[MOVED] == 1:
      return
    fish = None
    if f[TYPE] == SHARK :
      #print "%d: iteration shark"%Now()
      if f[STARVED] >= 3:
        viz_die(p)
        for i in range(4):
          f[i] = 0
        return
      fish = getsurroundings(p,FISH)
    spawn = None
    if fish:
      spawn = randomchoice(fish)
    else:
      emptyspaces = getsurroundings(p, EMPTY)
      if emptyspaces:
        spawn = randomchoice(emptyspaces)
    if spawn:        
      move(p,spawn)
    else:
        f[AGE] += 1
        if f[TYPE] == SHARK:
          f[STARVED] += 1

  def getsurroundings(p,_type):
    empty = []
    x = p.getX()
    y = p.getY()
    if world[x][(y-1)%world_height][TYPE] == _type: empty.append(Point(x,(y-1)%world_height)) #Above
    if world[x][(y+1)%world_height][TYPE] == _type: empty.append(Point(x,(y+1)%world_height)) #Below
    if world[(x-1)%world_width][y][TYPE] == _type: empty.append(Point((x-1)%world_width,y)) #Left
    if world[(x+1)%world_width][y][TYPE] == _type: empty.append(Point((x+1)%world_width,y)) #Right
    if empty == []: 
      return None
    return empty

  def move(f,t):
      _from = world[f.getX()][f.getY()]
      _to = world[t.getX()][t.getY()]
      if _from[TYPE] == SHARK:
        if _to[TYPE] == FISH:
          _to[STARVED] = 0
          viz_die(t)
        else:
          _to[STARVED] = _from[STARVED] + 1

      _to[AGE] = _from[AGE]+1
      _to[MOVED] = 1
      _to[TYPE] = _from[TYPE]
      viz_move(_to,f,t)

      if (_to[TYPE] == FISH and _to[AGE]<3) or _to[AGE]<10 :
        for i in range(4):
          _from[i] = 0
      else:
        #if _from[TYPE] == SHARK :print "shark multipliing"
        _to[AGE] = 0
        _from[AGE] = 0
        _from[MOVED] = 1
        create_gui(_from[TYPE],f)
      return _to

  def viz_move(element,_from, _to):
    viz_die(_from)
    create_gui(element[TYPE],_to)

  def viz_die(_to):
      screen.fill(color["blue"],(_to.to_gui(),(multiplier,multiplier)))
           
  Wait(1)
  for i in xrange(iterations):
    #Calc your world part:
    print "%d: main part b4 iteration"%Now()
    main_iteration()
    print "%d: main part after iteration"%Now()
    Wait(1)
    #Calc the two shadowrows
    print "%d: shadow row "%Now()
    for i in range(world_height):
      for j in range(2):
        element_iteration(Point(right_shadow_col+j,i))
    Wait(2)
  
@process
def visualize():
  for i in xrange(iterations):
    Wait(3)
    pygame.display.flip()
    print "%d: vizualized"%Now()
    #print "%s"%Simulation() 
    #t = raw_input()
    
def create_gui(type,point):
  if type == SHARK : screen.blit(shark_img,(point.getX()*multiplier,point.getY()*multiplier))
  if type == FISH : screen.blit(fish_img,(point.getX()*multiplier,point.getY()*multiplier))

def create(type):
  x = random.randint(0,world_width)
  y = random.randint(0,world_height)
  while not world[x][y][TYPE] == EMPTY:
    x = random.randint(0,world_width)
    y = random.randint(0,world_height)
  age = random.randint(0,9)
  if type == FISH:
    age = random.randint(0,3)
    
  world[x][y][AGE] = age 
  world[x][y][MOVED] = 0
  world[x][y][STARVED] = 0
  world[x][y][TYPE] = type
  create_gui(type,Point(x,y))


if __name__ == "__main__":
#Constants
  world_parts = 4
  iterations = 40
  pct_fish = 0.76
  pct_shark = 0.01
  multiplier = 10
  window_size = 3
  img_size = (multiplier,multiplier)

#Set GUI
  pygame.init()
  shark_img = pygame.image.load(os.path.join("images","shark2_ms.jpg"))
  fish_img = pygame.image.load(os.path.join("images","fish2_s.jpg"))
  shark_img = pygame.transform.smoothscale(shark_img,img_size)
  fish_img = pygame.transform.smoothscale(fish_img,img_size)

  assert shark_img.get_height() == shark_img.get_width()
  assert fish_img.get_height() == fish_img.get_width()
  assert shark_img.get_bounding_rect() == fish_img.get_bounding_rect()

  display = pygame.display.list_modes()[window_size]
  world_width = (display[0]/(multiplier*world_parts))*world_parts
  world_height = display[1]/multiplier
  if window_size == 0 :
      screen = pygame.display.set_mode((world_width*multiplier,world_height*multiplier),FULLSCREEN)
  else :
      screen = pygame.display.set_mode((world_width*multiplier,world_height*multiplier))
  screen.fill(color["blue"])

#Create shared data structure
  assert 0 == world_width%world_parts
  starting_fish = int(world_width*world_height*pct_fish) 
  starting_sharks = int(world_width*world_height*pct_shark)
  assert world_height*world_width >= starting_fish+starting_sharks #make sure we have room for fish+sharks
  world = zeros((world_width,world_height,4),object)

#Populate fish
  for i in xrange(starting_fish): create(FISH)

#Populate sharks
  for i in xrange(starting_sharks): create(SHARK)
  
  Parallel(
    [worldpart(i) for i in range(world_parts)],
    visualize()
  )
  print "main done"
