import pygame
import random
import math

import neat
import pickle

pygame.init()
pygame.font.init()

# Defining Global Constants
c_white = (255, 255, 255)
c_black = (0  ,   0,   0)
c_red   = (255,   0,   0)

# Global Window vars
WIN_WIDTH  = 1280
WIN_HEIGHT = 720
WIN = pygame.display.set_mode((WIN_WIDTH,WIN_HEIGHT))
pygame.display.set_caption('Pong with NEAT')

# Global fonts
FNT_DEBUG = pygame.font.SysFont('Arial', 32)

gen = 0

class Ball():
    r = 10
    start_vel = 0.5

    def __init__(self, x, y, paddle, col):
        self.col = col
        self.x = x
        self.y = y

        self.start_x = x
        self.start_y = y

        self.paddle = paddle

        dx = (-1 if random.random() > 0.5 else 1) * 0.5 
        dy = (random.random() - 0.5) * 2 
        v = math.sqrt(dx ** 2 + dy ** 2)

        self.vel = (dx/v * self.start_vel, dy/v * self.start_vel)

    def reset(self):
        self.x = self.start_x
        self.y = self.start_y

        dx = (-1 if random.random() > 0.5 else 1) * 0.5 
        dy = (random.random() - 0.5) * 2 
        v = math.sqrt(dx ** 2 + dy ** 2)

        self.vel = (dx/v * self.start_vel, dy/v * self.start_vel)

    def update(self, dt):
        # Move
        outcome = 0
        self.y += self.vel[1] * dt
        self.x += self.vel[0] * dt

        #Add a logarithmic speed boost to the ball
        v = self.vel[0] ** 2 + self.vel[1] ** 2
        v = math.sqrt(v)

        angle = math.atan(self.vel[1]/ self.vel[0])
        if self.vel[0] < 0:
            angle += math.pi


        # Adjust position for collisions with ceiling and floor
        if self.y < 0:
            self.y *= -1 # Flip distance to top borders
            angle *= -1
        if self.y > WIN_HEIGHT:
            self.y -= 2*(self.y - WIN_HEIGHT)
            angle *= -1

        # Check for collisions with paddles
        
        if self.x >= self.paddle.x and self.x <= self.paddle.x + self.paddle.width and self.y >= self.paddle.y and self.y <= self.paddle.y + self.paddle.height:
            # Ball collided with paddle
            outcome = 1
            self.v = math.log(math.exp(v)+1) #Add a logarithmic speed boost to the ball
            ydelt = self.y - (self.paddle.y + self.paddle.height/2)
            angle = ydelt/self.paddle.height * math.pi / 2 #Value ranging from -pi/4 to pi/4 depending upon where the ball hit the paddle
            if self.vel[0] > 0:
                angle = math.pi - angle

        # Bounce the ball off the left wall
        # TODO Add in random angle shift here
        if self.x < 0:
            self.x *= -1
            angle  = math.pi - angle # flip the direction the ball is traveling over the y axis
            angle = random.uniform(math.pi/-4 , math.pi/4)

        
        elif self.x > WIN_WIDTH:
            # Paddle missed the ball #TODO return false
            outcome = -1

        self.vel = (v * math.cos(angle), v * math.sin(angle))
        return outcome

    def draw(self, surf):
        pygame.draw.circle(surf, self.col, (self.x, self.y), self.r)




class Paddle():
    width = 25
    height = 135 # Center at y + 67
    speed = 0.5
    player_controlled=False
    keybinds = {
        'up':pygame.K_w,
        'down':pygame.K_s
    }
    

    def __init__(self, x, y, keybinds=None):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        if keybinds is not None:
            self.keybinds = keybinds
        self.col = (random.randrange(125, 200), random.randrange(125, 200), random.randrange(125, 200))
        self.ball = Ball(WIN_WIDTH/2, WIN_HEIGHT/2, self, self.col)

    def reset(self):
        self.x = self.start_x
        self.y = self.start_y

        self.ball.reset()

    def update(self, dt):
        if self.player_controlled:
            if pygame.key.get_pressed()[self.keybinds['up']]:
                self.move_up(dt)
            if pygame.key.get_pressed()[self.keybinds['down']]:
                self.move_down(dt)

        return self.ball.update(dt)   
        
    def move_up(self, dt):
        self.y -= min(self.speed*dt, self.y)

    def move_down(self, dt):
        self.y += self.speed*dt
        if self.y + self.height > WIN_HEIGHT:
            self.y = WIN_HEIGHT - self.height

    def draw(self, surf):
        surf.fill(self.col, (self.x, self.y, self.width, self.height))
        self.ball.draw(surf)


def eval_genomes(genomes, config):
    paddles = []
    nets = []
    ge = []
    
    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        ge.append(genome)
        nets.append(net)
        paddles.append(Paddle(WIN_WIDTH-30, WIN_HEIGHT/2))


    # Create engine
    clock = pygame.time.Clock()
        
    # Run the game until manual exit, all paddles have died, or a paddle has reflected at least 25 balls
    while len(paddles) > 0:
        dt = clock.tick(60)

        # Check if there is a manual exit
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                quit()
                

        rem = []
        for x, p in enumerate(paddles):
            n = nets[x]
            g = ge[x]

            inputs = (#p.ball.x,         # Ball pos
                        p.ball.y, 
                        #p.ball.vel[0],  # Ball Vel
                        #p.ball.vel[1], 
                        p.y)            # Paddle pos (1D)
            output = n.activate(inputs)

            if output[0] > 0.3:
                p.move_up(dt)
                ydelt = abs(p.y + p.height/2 - p.ball.y) / WIN_HEIGHT
                if ydelt < 0.10:
                    g.fitness += 1
            if output[1] > 0.3:
                p.move_down(dt)
                ydelt = abs(p.y + p.height/2 - p.ball.y) / WIN_HEIGHT
                if ydelt < 0.10:
                    g.fitness += 1

            outcome = p.update(dt)
            if outcome == 1:
                # Ball was successfully reflected, reward genome
                #g.fitness += 50
                pass
            
            if outcome == -1:
                # Paddle missed ball, remove it from the game
                rem.append(x)

        # Remove all the dropped paddles
        for x in rem[::-1]:
            ge.pop(x)
            paddles.pop(x)
            nets.pop(x)

        # === DRAW ===
        WIN.fill(c_black)


        # Draw lines in the middle
        num_lines = math.ceil(WIN_HEIGHT / 25 / 2)
        for i in range(num_lines):
            start_pos = (WIN_WIDTH / 2, 25 * 2 * i)
            end_pos =   (WIN_WIDTH / 2, 25 * 2 * i + 25)
            pygame.draw.line(WIN, c_white, start_pos, end_pos, 3)

        for p in paddles:
            p.draw(WIN)

        pygame.display.flip()

        
        



def run(config_path):
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))

    winner = p.run(eval_genomes, 300)
    winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
    pickle.dump(winner_net, open('./best_net.pkl', 'wb'))

   
    


if __name__ == '__main__':
    run('./06_lab_final_project/config.txt')


# TODO
    # Add in current highest fintess within and out of generation