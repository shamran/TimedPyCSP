from pycsp.greenlets import *
import random
from random import choice as randomchoice 
from numpy import *
import pygame, sys
from pygame.locals import *


EMPTY, FISH, SHARK = range(3)
TYPE, AGE, MOVED, STARVED = range(4)

type =  {
      0 : "EMPTY",
      1 : "FISH",
      2 : "SHARK"
      }
@process
def barrier (nr, cR, cW):
  while True:
    for i in range(nr):
       cR()
       #sleep(1)
       #print "%i workers in barrier" %(i+1)
    for i in range(nr):
       cW(1)



@process
def worldpart (part_id,cIN, barR, barW):

  #indices for working in a shared matrix:
  part_width = (world_width/worldparts)-2

  start_col = part_id*(part_width+2)
  right_shadow_col = (start_col+part_width)%world_width
  #print "shadow col ",right_shadow_col,part_id, worldparts

  def element_iteration(j,i):
    #print  "\n%i: (%i,%i)"%(part_id,j,i,),
    f = world[j][i]
    #print f[TYPE]
    if f[TYPE] == EMPTY:
      return
    #print " trying to move a %s"%type[f[TYPE]],
    #print "trying to move fish: %s"%_element(f)
    emptyspaces = getsurroundings(j,i, EMPTY)
    #if emptyspaces:
    #  print "number of free spaces:",len(emptyspaces)
    #else:
    #  print "no emptyspaces"

    #Fish has not moved or reproduced yet and has room to do so
    if f[TYPE] == FISH and f[MOVED] == 0 and emptyspaces:
      spawn = randomchoice(emptyspaces)
      #print"move from (%i,%i) to (%i,%i) : "%(j,i,spawn[0],spawn[1]),
      move(_from=f,_to=world[spawn[0]][spawn[1]])
    if f[TYPE] == SHARK and f[MOVED] == 0:
      if f[STARVED] == 3:
        #print "SHARK DYING ->",
        for i in range(4):
          f[i] = 0
        #print _element(f)
        return
      # Move to fish and eat it
      fish = getsurroundings(j,i,FISH)
      #if fish:
      #  print len(fish)
      #else:
      #  print "no fishs"
      spawn = None
      if fish:
        spawn = randomchoice(fish)
      elif emptyspaces:
        spawn = randomchoice(emptyspaces)
      if spawn:        
        #print"move from (%i,%i) to (%i,%i) : "%(j,i,spawn[0],spawn[1]),
        move(_from=f,_to=world[spawn[0]][spawn[1]])
      else:
        f[AGE] += 1
        f[STARVED] += 1

  def _element(element):
    return "%s:age:%i moved:%i starved:%i"%(type[element[TYPE]],element[AGE],element[MOVED],element[STARVED])

  def getsurroundings(x,y,_type):
    empty = []
    if world[x][(y-1)%world_height][TYPE] == _type: empty.append((x,(y-1)%world_height)) #Above
    if world[x][(y+1)%world_height][TYPE] == _type: empty.append((x,(y+1)%world_height)) #Below
    if world[(x-1)%world_width][y][TYPE] == _type: empty.append(((x-1)%world_width,y)) #Left
    if world[(x+1)%world_width][y][TYPE] == _type: empty.append(((x+1)%world_width,y)) #Right
    if empty == []: 
      #print " finding no %s nearby"%type[_type],
      #print x,y-1,(y-1)%world_height,world[x][(y-1)%world_height][TYPE],_type
      #print world[x][(y-1)%world_height][TYPE] == _type
      return None
    return empty

  def move(_from, _to):
      #print _element(_from)," -> ",
      if _from[TYPE] == SHARK:
        if _to[TYPE] == FISH:
          _to[STARVED] = 0
          #print " EATING ->",
        else:
          _to[STARVED] = _from[STARVED] + 1

      _to[AGE] = _from[AGE]+1
      _to[MOVED] = 1
      _to[TYPE] = _from[TYPE]

         
      if (_to[TYPE] == FISH and _to[AGE]<3) or _to[AGE]<10 :
        for i in range(4):
          _from[i] = 0
      else:
        #print " MULTIPLYING ->",
        _to[AGE] = 0
        _from[AGE] = 0
        _from[MOVED] = 1
        #print _element(_to),_element(_from)

  while True:
    #print "\n\n\nworker %i: moving parts"%part_id
    #reset MOVED before we begin the iteration
    for i in range(world_height):
      for j in range(start_col,start_col+part_width+2):
        f = world[j][i]
        f[MOVED] = 0

    for i in range(world_height):
      for j in range(start_col,start_col+part_width):
        element_iteration(j,i)
          
    barW(1)
    barR()
    #Shadow rows have access
    #print "\n\n\nworker %i: moving shadowrows"%part_id
    for i in range(world_height):
      for j in range(2):
        element_iteration(right_shadow_col+j,i)
    barW(1)
    barR()
    #visualizing have single access
    barW(1)
    barR()

  
@process
def visualize(barR,barW):
  while True:
    barW(1)
    barR()
    part_width = (world_width/worldparts)-2  #part = cIN()

    print "World:"
    for i in range(worldparts):
      for o in range(part_width):print "-",
      print "%","%",
    print ""
    for i in range(world_height): # y coordinate
      for j in range(world_width): # x coordinate
        type = world[j][i][0]
        #print type
        #       print world
        if type == EMPTY: print ".",
        if type == FISH: print "|",
        if type == SHARK: print "*",
      print ""
    for i in range(worldparts):
      for o in range(part_width):print "-",
      print "%","%",
    print ""
    #t = raw_input()
    barW(1)
    barR()
   


world_height = 40
world_width = 80 
worldparts = 5 
starting_fish = 430
starting_sharks = 20

assert world_height*world_width >= starting_fish+starting_sharks #make sure we have room for fish+sharks
world = zeros((world_width,world_height,4))

#Populate fish
i = 0
while i < starting_fish:
  x = random.randint(0,world_width)
  y = random.randint(0,world_height)
  if world[x][y][TYPE] == EMPTY:
    world[x][y][TYPE] = FISH
    world[x][y][AGE] = random.randint(0,3)
    world[x][y][MOVED] = 0
    i+=1

#Populate sharks
i = 0
while i < starting_sharks:
  x = random.randint(0,world_width)
  y = random.randint(0,world_height)
  if world[x][y][TYPE] == EMPTY:
    world[x][y][TYPE] = SHARK
    world[x][y][AGE] = random.randint(0,9)
    world[x][y][MOVED] = 0
    world[x][y][STARVED] = 0
    i+=1


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
