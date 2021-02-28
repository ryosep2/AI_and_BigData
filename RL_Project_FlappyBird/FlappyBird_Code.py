################################################################ ENSEA FAME SPRING 2020: Intelligence Artificielle et Big Data (Option S8) Projet_Reinforcement_Learning ################################################################
#
# CODE DONE BY EMMA S. KANTOLA AND RYAN E. YOSEPH
#
# 

# Import necessary packages

import pygame
import neat
import time 
import os
import random

# Package needed if you would like to save the winner after multiple trainings
import pickle
pygame.font.init()

# Initialize gen

GEN = 0

# Initialize sprites 

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird1.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird2.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bg.png")))

# Initialize game window 

WIN_WIDTH = BG_IMG.get_width()
WIN_HEIGHT = 800


STAT_FONT = pygame.font.SysFont("comicsans",50)

class Bird:
	IMGS = BIRD_IMGS
	MAX_ROTATION = 25 # degree of tilt when the bird jumps and falls
	ROT_VEL = 20 # how much we rotate each frame
	ANIMATION_TIME = 5 #duration of time we show bird flapping animation

	def __init__(self,x,y):
		self.x = x
		self.y = y 
		self.tilt = 0 
		self.tick_count = 0
		self.vel = 0
		self.height = self.y
		self.img_count = 0
		self.img = self.IMGS[0]

	def jump(self):
		self.vel = -10.5 # negative velocity goes upward; based on leftmost origin in PyGame
		self.tick_count = 0 # keeps track of when we last jumped
		self.height = self.y # keeps track of where the bird jumped/originated from

	def move(self):
		self.tick_count += 1

		displacement = self.vel*self.tick_count + 1.5*self.tick_count**2 # physics equation to map out displacement of bird

		if displacement >= 16: # If we are moving down more than 16 pixels, set limit at 16
			displacement = 16

		if displacement < 0:
			displacement -= 2 # If we are moving upwards, object moves up a little bit more to finetune the movement

		self.y = self.y + displacement

		if displacement < 0 or self.y < self.height + 50:
			if self.tilt < self.MAX_ROTATION:
				self.tilt = self.MAX_ROTATION
		else:
			if self.tilt > -90:
				self.tilt -= self.ROT_VEL

	def draw(self,win):
		self.img_count += 1 

		if self.img_count < self.ANIMATION_TIME:
			self.img = self.IMGS[0]
		elif self.img_count < self.ANIMATION_TIME*2:
			self.img = self.IMGS[1]
		elif self.img_count < self.ANIMATION_TIME*3:
			self.img = self.IMGS[2]
		elif self.img_count < self.ANIMATION_TIME*4:
			self.img = self.IMGS[1]
		elif self.img_count == self.ANIMATION_TIME*4 + 1:
			self.img = self.IMGS[0]
			self.img_count = 0

		if self.tilt <= -80:
			self.img = self.IMGS[1]
			self.img_count = self.ANIMATION_TIME*2

		# Properly rotate the bird around it's center axis 
		rotated_image = pygame.transform.rotate(self.img,self.tilt)
		new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft= (self.x,self.y)).center)
		win.blit(rotated_image,new_rect.topleft)


	def get_mask(self): # Function for detecting collisions 
		return pygame.mask.from_surface(self.img)


class Pipe:
	GAP = 200
	VEL = 6 # Pipes are moving, not the bird

	def __init__(self, x):
		self.x = x
		self.height = 0

		self.top = 0
		self.bottom = 0
		self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True) # creates the top pipe image by flipping our pipe iamge
		self.PIPE_BOTTOM = PIPE_IMG

		self.passed = False # collision purposes and to check if bird has passed this pipe

		self.set_height() # manipulate the pipe gap

	def set_height(self):
		self.height = random.randrange(50,450)
		self.top = self.height - self.PIPE_TOP.get_height()
		self.bottom = self.height + self.GAP

	def move(self): #function to move the pipes in the window
		self.x -= self.VEL

	def draw(self,win):
		win.blit(self.PIPE_TOP, (self.x,self.top))
		win.blit(self.PIPE_BOTTOM, (self.x,self.bottom))

	def collide(self,bird):
		# These next 3 lines create and initialize the pixel detection system which is coined as "masking". 
		bird_mask = bird.get_mask()
		top_mask = pygame.mask.from_surface(self.PIPE_TOP)
		bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

		top_offset = (self.x - bird.x, self.top - round(bird.y))
		bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

		b_point = bird_mask.overlap(bottom_mask, bottom_offset) # Find point of overlap between the bird mask and bottom pipe
		t_point = bird_mask.overlap(top_mask, top_offset) # Find point of overlap between the bird mask and top pipe

		if t_point or b_point: # if values are !None, then we are colliding with object
			return True

		return False

class Base:
	VEL = 6
	WIDTH = BASE_IMG.get_width()
	IMG = BASE_IMG

	def __init__(self, y):
		self.y = y
		self.x1 = 0
		self.x2 = self.WIDTH

	def move(self):
		self.x1 -= self.VEL
		self.x2 -= self.VEL

		# If statements check if image is outside the window. If so, cycle old image to the back of new image coming into the window

		if self.x1 + self.WIDTH < 0:
			self.x1 = self.x2 + self.WIDTH

		if self.x2 + self.WIDTH < 0:
			self.x2 = self.x1 + self.WIDTH

	def draw(self,win):
		win.blit(self.IMG, (self.x1, self.y))
		win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score, gen):
	win.blit(BG_IMG,(0,0))

	for pipe in pipes:
		pipe.draw(win)

	text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255))
	win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

	text = STAT_FONT.render("Gen: " + str(gen), 1, (255,255,255))
	win.blit(text, (10,10))

	base.draw(win)
	for bird in birds:
		bird.draw(win)

	pygame.display.update()


def main(genomes, config):
	global GEN
	GEN += 1
	nets = []
	ge = []
	birds =	[]

	for _,g in genomes:                                    # Genomes is a tuple that contains the genome ID and the genome object. Because we only want the object, we reject the genome ID by doing _, g
		net = neat.nn.FeedForwardNetwork.create(g,config) # Set up a Feed Forward neural network for our genome 
		nets.append(net)
		birds.append(Bird(230,350)) # Append bird object to the genome 
		g.fitness = 0 # Initialize fitness to 0 of all starting birds
		ge.append(g) # append the new population genomes to the list 


	base = Base(730)
	pipes = [Pipe(600)]
	win = pygame.display.set_mode((WIN_WIDTH,WIN_HEIGHT))
	clock = pygame.time.Clock()

	score = 0

	run = True
	while run: ########################################### Game loop starts here ###########################################
		clock.tick(30) # sets standard clock. For example, every second the following for loops will run 30 times a second
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
				pygame.quit()
				quit() # quit the game



		## Important Nuance: Because the input to our neural network is the y position of the bird and the distance from the bird to the top and bottom pipe,
		## we need to account for the fact that there might be two pipes on the screen at a time. Therefore, we created this pipe index and following if statements.


		pipe_ind = 0
		if len(birds) > 0:
			if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width(): # If we have passed the (n-1)th pipe, iterate pipe index so agent can focus on next incoming pipe and determine jump or !jump
				pipe_ind = 1

		else: # If no birds are left, quit the game
			run = False
			break


		for x, bird in enumerate(birds): # For all of our birds, we want to move them. we want to pass some values to the neural network associated with the bird object, check the output value, if value > 0.5, make bird jump. 
			bird.move()
			ge[x].fitness += 0.03 # every second our bird stays alive, we give the bird ~1 fitness point. ####################################### FITNESS ADJUSTER HERE FITNESS ADJUSTER HERE ###############################################

			output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom))) # activate the neural network with our inputs. Input: (y-position of bird object, distance between top pipe and bird, distance between bottom pipe and bird)

			if output[0] > 0.5: # Since we only have one output neuron, we pass the first index in the output list.
				bird.jump() # if the hyperbolic tangent function returns greater than 0.5, tell the bird object to jump. (Default is tanh; we tested the sigmoid activation function as well to compare performances)


		
		add_pipe = False # At the beginning of the game, no pipes are passed
		rem = []
		for pipe in pipes:
			for x, bird in enumerate(birds):
				if pipe.collide(bird):
					ge[x].fitness -= 1 # every time a bird hits a pipe, we remove 1 from its fitness score. ####################################### FITNESS ADJUSTER HERE FITNESS ADJUSTER HERE ###############################################
					birds.pop(x) # gets rid of bird object because it is unfavorable 
					nets.pop(x) # gets rid of the neural network associated with the bird 
					ge.pop(x) # gets rid of the genome associated with the bird 

				if not pipe.passed and pipe.x < bird.x: # as soon as we pass a pipe, generate a new pipe
					pipe.passed = True
					add_pipe = True

			if pipe.x + pipe.PIPE_TOP.get_width() < 0: # as soon as the pipe leaves the screen, remove the pipe
				rem.append(pipe)

			pipe.move()

		if add_pipe: # add 1 to our score if we pass a pipe, and create a new pipe
			score += 1
			for g in ge:
				g.fitness += 5 # increase fitness score for birds that have passed through a pipe ####################################### FITNESS ADJUSTER HERE FITNESS ADJUSTER HERE ###############################################
			pipes.append(Pipe(600)) # creates new pipe object

		for r in rem:   # remove pipes that went off the screen
			pipes.remove(r)

		for x, bird in enumerate(birds):
			if bird.y + bird.img.get_height() >= 730 or bird.y < 0: # Check to see if birds have hit the ground. also check to see if bird is at the top of the screen.
				birds.pop(x)
				nets.pop(x)
				ge.pop(x)


		if score > 100:
			run = False
			break


		base.move()		
		draw_window(win, birds, pipes, base, score, GEN)


def run(config_path):
	config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path) # Load in configuration file 

	p = neat.Population(config) # Create a population based on the NEAT configuration specified in our .rtf file 

	p.add_reporter(neat.StdOutReporter(True))
	stats = neat.StatisticsReporter()
	p.add_reporter(stats) # Returns the output 

	winner = p.run(main,50)



if __name__ == '__main__':
	local_dir = os.path.dirname(__file__)
	config_path = os.path.join(local_dir, "NEAT_Algorithm.rtf")
	run(config_path)







