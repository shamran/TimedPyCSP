from pycsp.greenlets import *
import random
from random import choice as randomchoice 
from numpy import *
import pygame, sys, os
from pygame.locals import *
#import psyco
#psyco.full()
EMPTY, FISH, SHARK = range(3)
TYPE, AGE, MOVED, STARVED, GUI = range(5)

type =  {
      0 : "EMPTY",
      1 : "FISH",
      2 : "SHARK"
      }

color  = {
    "blue": (0,0,205)
    }
def _element(element):
  return "%s:age:%i moved:%i starved:%i"%(type[element[TYPE]],element[AGE],element[MOVED],element[STARVED])

def gcd(num1, num2):
    if num1 > num2:
        for i in range(1,num2+1):
            if num2 % i == 0:
                if num1 % i == 0:
                    result = i
        return result

    elif num2 > num1:
        for i in range(1,num1+1):
            if num1 % i == 0:
                if num2 % i == 0:
                    result = i
        return result

    else:
        result = num1*num2/num1
        return result

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
  part_width = (world_width/world_parts)-2
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
      viz_move(_to,f,t)

      if (_to[TYPE] == FISH and _to[AGE]<3) or _to[AGE]<10 :
        for i in range(5):
          _from[i] = 0
      else:
        #if _to[TYPE] == SHARK : print " MULTIPLYING ->",
        _to[AGE] = 0
        _from[AGE] = 0
        _from[MOVED] = 1
        create_gui(_from[TYPE],f)
        #print _element(_to),_element(_from)

  def viz_move(element,_from, _to):
    viz_die(_from)
    create_gui(element[TYPE],_to)
  def viz_die(_to):
      screen.fill(color["blue"],(_to.to_gui(),(multiplier,multiplier)))

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
    #print i
    barW(1)
    barR()
    barW(1)
    barR()
    pygame.display.flip()
    #t = raw_input()
    barW(1)
    barR()
  poison(barW,barR)   

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
  #world[x][y][GUI].draw(win)

world_parts = 5

#Set GUI
pygame.init()

shark_img = pygame.image.load(os.path.join("images","shark2_ms.jpg"))
fish_img = pygame.image.load(os.path.join("images","fish2_s.jpg"))
assert shark_img.get_height() == shark_img.get_width()
assert fish_img.get_height() == fish_img.get_width()
assert shark_img.get_bounding_rect() == fish_img.get_bounding_rect()
multiplier = shark_img.get_height() 
display = pygame.display.list_modes()[0]
world_width = (display[0]/(multiplier*world_parts))*world_parts
world_height = display[1]/multiplier
screen = pygame.display.set_mode((world_width*multiplier,world_height*multiplier),FULLSCREEN)
screen.fill(color["blue"])

assert 0 == world_width%world_parts
starting_fish = 900
starting_sharks = 61
iterations = 50
assert world_height*world_width >= starting_fish+starting_sharks #make sure we have room for fish+sharks
world = zeros((world_width,world_height,5),object)


print world_height,world_width
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
  [worldpart(i, +ch,+barrier_channel,-barrier_channel) for i in range(world_parts)],
  visualize(+barrier_channel,-barrier_channel),
  barrier(world_parts+1, +barrier_channel, -barrier_channel)
)
