from pycsp.greenlets import *
from random import *
from numpy import *
import pygame, sys
from pygame.locals import *


EMPTY, FISH, SHARK = range(3)
TYPE, AGE, MOVED, STARVED = range(4)

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

pygame.init()

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
def start(cOUT):
  worldsize = 32 #world is symmetric, value*value
  worldparts = 1 #change to dymamic later
  
  starting_fish = 40
  starting_sharks = 40

  cOUT((starting_fish, starting_sharks, worldsize))


@process
def worldpart (cIN):
  fish, sharks, worldsize = cIN()
  print "%i fish and %i sharks in the world" %(fish, sharks)
  windowsurface = pygame.display.set_mode((worldsize, worldsize), 0, 32) 
  #Array is fefined as x,y,type of fish, age, moved 
  #Array is defines as x,y,(FISH or SHARK), (MOVED or NOTMOVED) with a age value at the location
  mypart = zeros((worldsize,worldsize,4))
  #Distribute fish and sharks randomly in the world

  assert worldsize**2 > fish+sharks #make sure we have room for fish+sharks
 
  #FIXME for several worldparts!
  def getsurroundings(x,y,type):
    empty = []
    if mypart[x][(y-1)%worldsize][TYPE] == type: empty.append((x,(y-1)%worldsize)) #Above
    if mypart[x][(y+1)%worldsize][TYPE] == type: empty.append((x,(y+1)%worldsize)) #Below
    if mypart[(x-1)%worldsize][y][TYPE] == type: empty.append(((x-1)%worldsize,y)) #Left
    if mypart[(x+1)%worldsize][y][TYPE] == type: empty.append(((x+1)%worldsize,y)) #Right
    return empty

  

  #Populate fish
  i = 0
  while i < fish:
    x = randint(0,worldsize-1)
    y = randint(0,worldsize-1)
    if mypart[x][y][TYPE] == EMPTY:
      mypart[x][y][TYPE] = FISH
      mypart[x][y][AGE] = randint(1,3)
      mypart[x][y][MOVED] = 0
      i+=1

  #Populate sharks
  i = 0
  while i < sharks:
    x = randint(0,worldsize-1)
    y = randint(0,worldsize-1)
    if mypart[x][y][TYPE] == EMPTY:
      mypart[x][y][TYPE] = SHARK
      mypart[x][y][AGE] = randint(0,3)
      mypart[x][y][MOVED] = 0
      mypart[x][y][STARVED] = 0

      i+=1

  printworld(mypart)
  while True: 
    for i in range(worldsize):
      for j in range(worldsize):
        f = mypart[j][i]
        f[MOVED] = 0

    for i in range(worldsize):
      for j in range(worldsize):
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
        
    var = raw_input("continue?")
    printworld(mypart)
    
def printworld(part):
  print "World:"
  for i in range(len(part)): # y coordinate
    for j in range(len(part[0])): # x coordinate
      f = part[j][i]
      if f[TYPE] == EMPTY: print " ",
      if f[TYPE] == FISH: print "F",
      if f[TYPE] == SHARK: print "S",
    print ""

ch = Channel()

Parallel(
  start(ch.writer()), worldpart(ch.reader())
)
