from pycsp.greenlets import *
from random import *
from numpy import *
import pygame, sys
from pygame.locals import *


EMPTY, FISH, SHARK = range(3)
TYPE, AGE, MOVED, STARVED = range(4)


@process
def barrier (nr, cIN, cOUT):
  while True:
    for i in range(nr):
       cIN()
       sleep(1)
       #print "%i workers in barrier" %(i+1)
    for i in range(nr):
       cOUT(1)


@process
def start(cOUT, nr_partsW):
  world_height = 10
  world_width = 32
  #worldsize = 32 #world is symmetric, value*value
  worldparts = 2 #change to dymamic later
  
  starting_fish = 40
  starting_sharks = 40

  nr_partsW(worldparts)
  for i in range(worldparts):
    cOUT((starting_fish, starting_sharks, world_height, world_width/worldparts,i)) # i is transmitted as a reference to the worldpart

@process
def worldpart (cIN, cOUT):
  fish, sharks, world_height, part_width, part_id = cIN()
  print "%i fish and %i sharks in the world" %(fish, sharks)
  #Array is fefined as x,y,type of fish, age, moved, starved 
  mypart = zeros((part_width,world_height,4))

  assert world_height*part_width > fish+sharks #make sure we have room for fish+sharks
 
  #FIXME for several worldparts!
  def getsurroundings(x,y,type):
    empty = []
    if mypart[x][(y-1)%world_height][TYPE] == type: empty.append((x,(y-1)%world_height)) #Above
    if mypart[x][(y+1)%world_height][TYPE] == type: empty.append((x,(y+1)%world_height)) #Below
    if mypart[(x-1)%part_width][y][TYPE] == type: empty.append(((x-1)%part_width,y)) #Left
    if mypart[(x+1)%part_width][y][TYPE] == type: empty.append(((x+1)%part_width,y)) #Right
    return empty

  

  #Populate fish
  i = 0
  while i < fish:
    x = randint(0,part_width-1)
    y = randint(0,world_height-1)
    if mypart[x][y][TYPE] == EMPTY:
      mypart[x][y][TYPE] = FISH
      mypart[x][y][AGE] = randint(1,3)
      mypart[x][y][MOVED] = 0
      i+=1

  #Populate sharks
  i = 0
  while i < sharks:
    x = randint(0,part_width-1)
    y = randint(0,world_height-1)
    if mypart[x][y][TYPE] == EMPTY:
      mypart[x][y][TYPE] = SHARK
      mypart[x][y][AGE] = randint(0,3)
      mypart[x][y][MOVED] = 0
      mypart[x][y][STARVED] = 0

      i+=1

  while True: 
    #reset MOVED before we begin the iteration
    for i in range(world_height):
      for j in range(part_width):
        f = mypart[j][i]
        f[MOVED] = 0

    for i in range(world_height):
      for j in range(part_width):
        f = mypart[j][i]
        emptyspaces = getsurroundings(j,i, EMPTY)
        fish = getsurroundings(j,i,FISH)
        #Fish has not moved or reproduced yet and has room to do so
        if f[TYPE] == FISH and f[MOVED] == 0 and len(emptyspaces) > 0:
          spawn = choice(emptyspaces)
          mypart[spawn[0]][spawn[1]][TYPE] = FISH
          mypart[spawn[0]][spawn[1]][AGE] = 0
          mypart[spawn[0]][spawn[1]][MOVED] = 1
          if f[AGE] < 3: #Delete old fish (so it becomes a move instead of spawn)
            mypart[spawn[0]][spawn[1]][AGE] = f[AGE]+1 #remember age and increment
            f[TYPE] = EMPTY
            f[AGE] = 0
            f[MOVED] = 0
          else:
            f[AGE] = 0 #Age is reset for both new and old fish when a spawn accurs
        
        #Sharks want to eat if possible, otherwise move. 
        if f[TYPE] == SHARK and f[MOVED] == 0: # and (len(emptyspaces) > 0 or (len(fish) > 0)):
          #Shark is starved and dies
          if f[STARVED] == 3:
            f[TYPE] = EMPTY
            f[AGE] = 0
            f[MOVED] = 0
            f[STARVED] = 0
            continue
          # Move to fish and eat it
          try:
            spawn = choice(fish)
            mypart[spawn[0]][spawn[1]][STARVED] = 0 #Reset starvation as we eat
          except IndexError:
            try:
              # Move
              spawn = choice(emptyspaces)
              mypart[spawn[0]][spawn[1]][STARVED] = f[STARVED]+1
            except IndexError:
              #no fish to eat, nowhere to move
              f[AGE] +=1
              f[STARVED] +=1
              continue
          mypart[spawn[0]][spawn[1]][TYPE] = SHARK
          mypart[spawn[0]][spawn[1]][AGE] = 0
          mypart[spawn[0]][spawn[1]][MOVED] = 1
          if f[AGE] < 10: #Delete old shark (so it becomes a move instead of spawn)
            mypart[spawn[0]][spawn[1]][AGE] = f[AGE]+1 #remember age and increment
            f[TYPE] = EMPTY
            f[AGE] = 0
            f[MOVED] = 0
            f[STARVED] = 0
          else:
            f[AGE] = 0
        
    #var = raw_input("continue?")
    cOUT((mypart, part_id))
    


@process
def aggregate(partR, nr_partsR, cW):
  nr_parts = nr_partsR()
  while True:
    for k in range(nr_parts):
      part, part_id = partR()
      if k == 0: 
        world = zeros((len(part)*nr_parts, len(part[0])))
      offset = part_id*len(part)
      for i in range(len(part[0])):
        for j in range(len(part)):
          world[j+offset][i] = part[j][i][TYPE]
    #print "Aggregated world:"
    #print world
    cW(world)

@process
def visualize(cIN):
  while True:
    part = cIN()
    print "World:"
    for i in range(len(part[0])): # y coordinate
      for j in range(len(part)): # x coordinate
        type = part[j][i]
        if type == EMPTY: print " ",
        if type == FISH: print "-",
        if type == SHARK: print "|",
      print ""




ch = Channel()
start2aggr = Channel()
part2aggr = Channel()
aggr2vis = Channel()

Parallel(
  start(ch.writer(), start2aggr.writer()), 
  2*worldpart(ch.reader(), part2aggr.writer()),
  aggregate(part2aggr.reader(), start2aggr.reader(), aggr2vis.writer()),
  visualize(aggr2vis.reader())
)
