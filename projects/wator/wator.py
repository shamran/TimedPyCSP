from pycsp.greenlets import *
import random
from random import choice as randomchoice 
from numpy import *
import pygame, sys
#from pygame.locals import *
from graphics import *

EMPTY, FISH, SHARK = range(3)
TYPE, AGE, MOVED, STARVED = range(4)

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
def start(cOUT, nr_partsW):
  world_height = 60
  world_width = 60
  #worldsize = 32 #world is symmetric, value*value
  worldparts = 2 #change to dymamic later
  
  starting_fish = 80 
  starting_sharks = 60

  nr_partsW(worldparts)
  for i in range(worldparts):
    cOUT((starting_fish, starting_sharks, world_height, world_width/worldparts,i)) # i is transmitted as a reference to the worldpart

@process
def worldpart (cIN, cOUT, barR, barW, leftR, leftW, rightR, rightW):
  fish, sharks, world_height, part_width, part_id = cIN()
  print "%i fish and %i sharks in the world" %(fish, sharks)
  #Array is defined as x,y,type of fish, age, moved, starved 
  mypart = zeros((part_width+2,world_height,4))

  assert world_height*part_width > fish+sharks #make sure we have room for fish+sharks
 
  def getsurroundings(x,y,type):
    empty = []
    if mypart[x][(y-1)%world_height][TYPE] == type: empty.append((x,(y-1)%world_height)) #Above
    if mypart[x][(y+1)%world_height][TYPE] == type: empty.append((x,(y+1)%world_height)) #Below
    if mypart[x-1][y][TYPE] == type: empty.append((x-1,y)) #Left
    if mypart[x+1][y][TYPE] == type: empty.append((x+1,y)) #Right
    return empty

  
  #def merge_columns(col, pos):
  #  for i in range len(col):
  #    if col[i][MOVED] == 1:
  #      assert mypart
  
  def synchronize(merge=False):
    my_left_col = mypart[1] 
    my_right_col = mypart[len(mypart)-2] 
    
    shadow_left_col = mypart[0]
    shadow_right_col = mypart[len(mypart)-1] 
 

    @choice
    def read_left(__channel_input=None):
      if merge:
        print ""
      else:
        mypart[0] = __channel_input
        rightW(my_right_col)

    @choice
    def write_right():
      if merge:
        print ""
      else:
        mypart[0] = leftR()
    
    Alternation([
      (leftR,read_left()), 
      (rightW,my_right_col,write_right())]
      ).execute()

    @choice 
    def read_right(__channel_input=None):
      if merge:
        print "" 
      else:
        mypart[len(mypart)-1] = __channel_input
        leftW(my_left_col)

    @choice
    def write_left():
      if merge:
        print ""
      else:
        mypart[len(mypart)-1] = rightR()

    Alternation([
      (rightR,read_right()), 
      (leftW,my_left_col,write_left())]
      ).execute()


  #Populate fish
  i = 0
  while i < fish:
    x = random.randint(1,part_width+1)
    y = random.randint(0,world_height)
    if mypart[x][y][TYPE] == EMPTY:
      mypart[x][y][TYPE] = FISH
      mypart[x][y][AGE] = random.randint(0,3)
      mypart[x][y][MOVED] = 0
      i+=1

  #Populate sharks
  i = 0
  while i < sharks:
    x = random.randint(1,part_width+1)
    y = random.randint(0,world_height)
    if mypart[x][y][TYPE] == EMPTY:
      mypart[x][y][TYPE] = SHARK
      mypart[x][y][AGE] = random.randint(0,3)
      mypart[x][y][MOVED] = 0
      mypart[x][y][STARVED] = 0
      i+=1

  # Temp printing  
  '''
  print "before exchange %i" %(part_id)
  for i in range(len(mypart[0])):
    for j in range(len(mypart)):
      f = mypart[j][i]
      if f[TYPE] == EMPTY: print ".",
      if f[TYPE] == FISH: print "/",
      if f[TYPE] == SHARK: print "|",
    print""
  '''
  
  while True: 
    #reset MOVED before we begin the iteration
    for i in range(world_height):
      for j in range(1,part_width+1):
        f = mypart[j][i]
        f[MOVED] = 0

    synchronize() 
    cOUT((mypart, part_id))
    barW(1)
    barR()

    for i in range(world_height):
      for j in range(1,part_width+1):
        f = mypart[j][i]
        emptyspaces = getsurroundings(j,i, EMPTY)
        fish = getsurroundings(j,i,FISH)
        #Fish has not moved or reproduced yet and has room to do so
        if f[TYPE] == FISH and f[MOVED] == 0 and len(emptyspaces) > 0:
          spawn = randomchoice(emptyspaces)
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
            spawn = randomchoice(fish)
            mypart[spawn[0]][spawn[1]][STARVED] = 0 #Reset starvation as we eat
          except IndexError:
            try:
              # Move
              spawn = randomchoice(emptyspaces)
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
    
    #Send fish and sharks that have moved to another world part
    


    #var = raw_input("continue?")
    cOUT((mypart, part_id))
    barW(1)
    barR()
  

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

#@process
#def visualize(cIN):
#  while True:
#    part = cIN()
#    print "World:"
#    for i in range(len(part[0])): # y coordinate
#      for j in range(len(part)): # x coordinate
#        type = part[j][i]
#        if type == EMPTY: print ".",
#        if type == FISH: print "|",
#        if type == SHARK: print "*",
#      print ""

@process
def visualize(cIN):
  win = GraphWin("WATOR",500,500,False)
  win.setBackground("blue1")
  prev_part = []
  while True:
    part = cIN()
    for i in range(len(part[0])): # y coordinate
      for j in range(len(part)): # x coordinate
        type = part[j][i]
        if len(prev_part) and (type != prev_part[j][i]):
          #print "prev: %i, part: %i" %(prev_part[j][i],type)
          if type == EMPTY: win.plot(j,i,"black")
          if type == FISH: win.plot(j,i,"green")
          if type == SHARK: win.plot(j,i,"red")
    win.update()
    prev_part = part

    #t = raw_input()

ch = Channel()
start2aggr = Channel()
part2aggr = Channel()
aggr2vis = Channel()
part2bar = Channel()
bar2part = Channel()

#change to dymanic channel assignment:
zero2oneL = Channel()
one2zeroL = Channel()
zero2oneR = Channel()
one2zeroR = Channel()



#def worldpart (cIN, cOUT, barR, barW, leftR, leftW, rightR, rightW):
Parallel(
  start(ch.writer(), start2aggr.writer()), 
  worldpart(ch.reader(), part2aggr.writer(), bar2part.reader(), part2bar.writer(),one2zeroL.reader(),zero2oneL.writer(),one2zeroR.reader(),zero2oneR.writer()),
  worldpart(ch.reader(), part2aggr.writer(), bar2part.reader(), part2bar.writer(),zero2oneR.reader(),one2zeroR.writer(),zero2oneL.reader(),one2zeroL.writer()),
  aggregate(part2aggr.reader(), start2aggr.reader(), aggr2vis.writer()),
  visualize(aggr2vis.reader()),
  barrier(2, part2bar.reader(), bar2part.writer())
)
