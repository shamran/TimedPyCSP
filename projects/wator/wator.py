from pycsp.greenlets import *
import random
from random import choice as randomchoice 
from numpy import *
import pygame, sys
#from pygame.locals import *
from graphics import *
#import psyco
#psyco.full()
EMPTY, FISH, SHARK = range(3)
TYPE, AGE, MOVED, STARVED, GUI = range(5)

type =  {
      0 : "EMPTY",
      1 : "FISH",
      2 : "SHARK"
      }
color = {
    0 : "blue",
    1 : "green", 
    2 : "red"
    }

def _element(element):
  return "%s:age:%i moved:%i starved:%i"%(type[element[TYPE]],element[AGE],element[MOVED],element[STARVED])

@process
def barrier (nr, cR, cW):
  try:
    while True:
      for i in range(nr):
         cR()
      for i in range(nr):
         cW(1)
  except ChannelPoisonException:
    return

@process
def worldpart (part_id,cIN, barR, barW):

  #indices for working in a shared matrix:
  part_width = (world_width/worldparts)-2
  start_col = part_id*(part_width+2)
  right_shadow_col = (start_col+part_width)%world_width

  def element_iteration(j,i):
    f = world[j][i]
    if f[TYPE] == EMPTY or f[MOVED] == 1:
      return
    if f[TYPE] == FISH and not getsurroundings(j,i, EMPTY):
      return
    p = Point(j,i)
    fish = None
    if f[TYPE] == SHARK :
      if f[STARVED] >= 3:
        #print "SHARK DIE ->",
        viz_die(p)
        for i in range(5):
          f[i] = 0
        return
      # Move to fish and eat it
      fish = getsurroundings(j,i,FISH)
      #print "BEFORE MOVE",
      #print _element(f)," at:",j,i,
      #win.update()
      #t = raw_input()
    spawn = None
    if fish:
      spawn = randomchoice(fish)
      #print " fishes nearby ",fish, "choosing ",spawn
    else:
      #Move to empty space
      emptyspaces = getsurroundings(j,i, EMPTY)
      if emptyspaces:
        spawn = randomchoice(emptyspaces)
    if spawn:        
      #if f[TYPE] == SHARK: print "from",f,
      to = world[spawn.getX()][spawn.getY()]
      move(_from=f,f=p,_to=to,t=spawn)
      f = to
      #if to[TYPE] == SHARK: print " to ",to
        
    else:
        f[AGE] += 1
        if f[TYPE] == SHARK:
          f[STARVED] += 1
    #      print "cannont move, starving now ",f[STARVED]
    #if f[TYPE] == SHARK:
    #  print "AFTER MOVE"
    #  win.update()
    #  t = raw_input()

  def getsurroundings(x,y,_type):
    empty = []
    if world[x][(y-1)%world_height][TYPE] == _type: empty.append(Point(x,(y-1)%world_height)) #Above
    if world[x][(y+1)%world_height][TYPE] == _type: empty.append(Point(x,(y+1)%world_height)) #Below
    if world[(x-1)%world_width][y][TYPE] == _type: empty.append(Point((x-1)%world_width,y)) #Left
    if world[(x+1)%world_width][y][TYPE] == _type: empty.append(Point((x+1)%world_width,y)) #Right
    if empty == []: 
      return None
    return empty

  def move(_from,f, _to,t):
      #print _element(_from)," -> ",
      if _from[TYPE] == SHARK:
        if _to[TYPE] == FISH:
          _to[STARVED] = 0
          viz_die(t)
          #print " EATING ->",
        else:
          _to[STARVED] = _from[STARVED] + 1
          #print "in move, starving ",_to[STARVED]

      _to[AGE] = _from[AGE]+1
      _to[MOVED] = 1
      _to[TYPE] = _from[TYPE]
      _to[GUI] = _from[GUI]
      viz_move(f,t)

      if (_to[TYPE] == FISH and _to[AGE]<3) or _to[AGE]<10 :
        for i in range(5):
          _from[i] = 0
      else:
        #if _to[TYPE] == SHARK : print " MULTIPLYING ->",
        _to[AGE] = 0
        _from[AGE] = 0
        _from[MOVED] = 1
        _from[GUI] = create_gui(_from[TYPE],f.getX(),f.getY())
        _from[GUI].draw(win) 
        #print _element(_to),_element(_from)

  def viz_move(_from, _to):
      dx =  _to.getX() - _from.getX() 
      dy =  _to.getY() - _from.getY() 
      #print "move",_from, _to, dx,dy 
      world[_to.getX()][_to.getY()][GUI].move(dx*multiplier,dy*multiplier)

  def viz_die(_to):
      world[_to.getX()][_to.getY()][GUI].undraw()

  @io
  def main_iteration():
      for i in range(world_height):
        for j in range(start_col,start_col+part_width+2):
          f = world[j][i]
          f[MOVED] = 0

      for i in range(world_height):
        for j in range(start_col,start_col+part_width):
          element_iteration(j,i)
            
  try:
    while True:
      main_iteration()
      barW(1)
      barR()
      for i in range(world_height):
        for j in range(2):
          element_iteration(right_shadow_col+j,i)
      barW(1)
      barR()
      #visualizing have single access
      barW(1)
      barR()

  except ChannelPoisonException:
      poison(cIN)
  
@process
def visualize(barR,barW):
  for i in xrange(iterations):
    print i
    barW(1)
    barR()
    barW(1)
    barR()
    win.update()
    #t = raw_input()
    barW(1)
    barR()
  poison(barW,barR)   

def create_gui(type,x,y):
  point1 = Point(x*multiplier,y*multiplier)
  point2 = Point(x*multiplier+multiplier,y*multiplier+multiplier)
  rec = Rectangle(point1,point2)
  rec.setFill(color[type])
  return rec

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
  world[x][y][GUI] = create_gui(type,x,y)
  world[x][y][GUI].draw(win)

world_height = 80
world_width = 100 
worldparts = 1 
starting_fish = 900
starting_sharks = 61
multiplier = 10
iterations = 500
assert world_height*world_width >= starting_fish+starting_sharks #make sure we have room for fish+sharks
world = zeros((world_width,world_height,5),object)

#Set GUI
win = GraphWin("WATOR",world_width*multiplier,world_height*multiplier,False)
win.setBackground("blue1")


#Populate fish
for i in range(starting_fish):  
    create(FISH)

#Populate sharks
for i in range(starting_sharks):
  create(SHARK)

ch = Channel()
start2aggr = Channel()
part2aggr = Channel()
aggr2vis = Channel()
barrier_channel = Channel()



#def worldpart (cIN, cOUT, barR, barW, leftR, leftW, rightR, rightW):
Parallel(
  # start(ch.writer(), workers), 
  [worldpart(i, +ch,+barrier_channel,-barrier_channel) for i in range(worldparts)],
  visualize(+barrier_channel,-barrier_channel),
  barrier(worldparts+1, +barrier_channel, -barrier_channel)
)
