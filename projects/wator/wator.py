from pycsp.greenlets import *
from random import *
from numpy import *


EMPTY, FISH, SHARK = range(3)
TYPE, AGE, MOVED = range(3)
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
  worldsize = 16 #world is symmetric, value*value
  worldparts = 1 #change to dymamic later
  
  starting_fish = 40
  starting_sharks = 20

  cOUT((starting_fish, starting_sharks, worldsize))


@process
def worldpart (cIN):
  fish, sharks, worldsize = cIN()
  print "%i fish and %i sharks in the world" %(fish, sharks)
 
  #Array is fefined as x,y,type of fish, age, moved 
  #Array is defines as x,y,(FISH or SHARK), (MOVED or NOTMOVED) with a age value at the location
  mypart = zeros((worldsize,worldsize,3))
  #Distribute fish and sharks randomly in the world

  assert worldsize**2 > fish+sharks #make sure we have room for fish+sharks
 
  def getempty(x,y):
    empty = []
    if mypart[x][(y-1)%worldsize][TYPE] == EMPTY: empty.append((x,(y-1)%worldsize)) #Above
    if mypart[x][(y+1)%worldsize][TYPE] == EMPTY: empty.append((x,(y+1)%worldsize)) #Below
    if mypart[(x-1)%worldsize][y][TYPE] == EMPTY: empty.append(((x-1)%worldsize,y)) #Left
    if mypart[(x+1)%worldsize][y][TYPE] == EMPTY: empty.append(((x+1)%worldsize,y)) #Right
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
      mypart[x][y][AGE] = randint(1,3)
      mypart[x][y][MOVED] = 0
      i+=1

  printworld(mypart)
  
  for i in range(worldsize):
    for j in range(worldsize):
      f = mypart[j][i]
      emptyspaces = getempty(j,i)
      if f[TYPE] == FISH and len(emptyspaces) > 0:
        spawn = choice(emptyspaces)
        mypart[spawn[0]][spawn[1]][TYPE] = FISH
        mypart[spawn[0]][spawn[1]][AGE] = 1
        mypart[spawn[0]][spawn[1]][MOVED] = 1
        if f[AGE] < 3: #Delete old fish (so it becomes a move instead of spawn)
          mypart[spawn[0]][spawn[1]][AGE] = f[AGE] #remember age
          f[TYPE] = EMPTY
          f[AGE] = 0
          f[MOVED] = 0

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
