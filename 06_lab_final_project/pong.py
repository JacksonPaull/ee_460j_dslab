import pygame
import random
import math

import neat
import pickle

# Defining Global Constants
c_white = (255, 255, 255)
c_black = (0  ,   0,   0)
c_red   = (255,   0,   0)

class GameObject:
    def update(self, dt):
        pass
    def draw(self, surf):
        pass

class Ball(GameObject):
    r = 10
    start_vel = 0.5

    def __init__(self, x, y, paddle):
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
        if self.y > self.paddle.engine.scr_height:
            self.y -= 2*(self.y - self.paddle.engine.scr_height)
            angle *= -1

        # Check for collisions with paddles
        
        if self.x >= self.paddle.x and self.x <= self.paddle.x + self.paddle.width and self.y >= self.paddle.y and self.y <= self.paddle.y + self.paddle.height:
            # Ball collided with paddle
            self.v = math.log(math.exp(v)+1) #Add a logarithmic speed boost to the ball
            ydelt = self.y - (self.paddle.y + self.paddle.height/2)
            angle = ydelt/self.paddle.height * math.pi / 2 #Value ranging from -pi/4 to pi/4 depending upon where the ball hit the paddle
            if self.vel[0] > 0:
                angle = math.pi - angle


        # Check for round over (Paddle missed a ball)
        if self.x < 0:
            self.x *= -1
            angle  = math.pi - angle # flip the direction the ball is traveling over the y axis

        
        elif self.x > self.paddle.engine.scr_width:
            # Paddle missed the ball #TODO return false
            return False

        self.vel = (v * math.cos(angle), v * math.sin(angle))
        return True

    def draw(self, surf):
        pygame.draw.circle(surf, c_white, (self.x, self.y), self.r)




class Paddle(GameObject):
    width = 25
    height = 135 # Center at y + 67
    speed = 0.5
    player_controlled=True
    keybinds = {
        'up':pygame.K_w,
        'down':pygame.K_s
    }

    def __init__(self, x, y, engine, keybinds=None):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.engine = engine
        if keybinds is not None:
            self.keybinds = keybinds

        self.ball = Ball(self.engine.scr_width/2, self.engine.scr_height/2, self)

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

        if not self.ball.update(dt):
            # missed ball
            self.engine.reset()
        
    def move_up(self, dt):
        self.y -= min(self.speed*dt, self.y)

    def move_down(self, dt):
        self.y += self.speed*dt
        if self.y + self.height > self.engine.scr_height:
            self.y = self.engine.scr_height - self.height

    def draw(self, surf):
        surf.fill(c_white, (self.x, self.y, self.width, self.height))
        self.ball.draw(surf)


class Scoreboard(GameObject):
    #TODO Refactor this if we want it to display like the maximum current score?
    dashed_line_height = 25

    def __init__(self, font, engine):
        # Create scoreboard object
        self.p1Score = 0
        self.p2Score = 0
        
        self.font = font
        self.engine = engine
        self.num_lines = math.ceil(self.engine.scr_height / self.dashed_line_height / 2)


    def draw(self, surf):
        # Draw the current scores of the players in the proper position onto surf
        t = self.font.render(f'Player 1 Score: {self.p1Score}', False, c_white)
        t_rect = t.get_rect()
        t_rect.center = (self.engine.scr_width/4, 50)
        surf.blit(t, t_rect)

        t = self.font.render(f'{self.p2Score}: Player 2 Score', False, c_white)
        t_rect = t.get_rect()
        t_rect.center = (3 * self.engine.scr_width/4, 50)
        surf.blit(t, t_rect)

        for i in range(self.num_lines):
            start_pos = (self.engine.scr_width / 2, self.dashed_line_height * 2 * i)
            end_pos =   (self.engine.scr_width / 2, self.dashed_line_height * 2 * i + self.dashed_line_height)
            pygame.draw.line(surf, c_white, start_pos, end_pos, 3)



class Pong_Game_Engine:
    pygame.init()
    pygame.font.init()
    _framerate = 60
    clock = pygame.time.Clock()
    scr_width, scr_height = 1280, 720
    fnt_debug = pygame.font.SysFont('Arial', 32)

    dashed_line_height = 25
    num_lines = math.ceil(scr_height / dashed_line_height / 2)

    def __init__(self, screensize=None):
        self.objects = {}
        self.should_quit = False
        self.paused = True

        if screensize is not None:
            self.scr_width, self.scr_height = screensize

        self.screen = pygame.display.set_mode((self.scr_width, self.scr_height))

        #p = Paddle(30, self.scr_height/2, self)
        #p.y -= math.floor(p.height/2)
        #self.objects['paddle1'] = p

        p = Paddle(self.scr_width - 30, self.scr_height/2, self, keybinds={'up':pygame.K_o, 'down':pygame.K_l})
        p.x -= p.width
        p.y -= math.floor(p.height/2)
        self.objects['paddle2'] = p

        # Draw initial screen
        self.screen.fill(c_black)
        for o in self.objects.values():
            o.draw(self.screen)

        for i in range(self.num_lines):
            start_pos = (self.scr_width / 2, self.dashed_line_height * 2 * i)
            end_pos =   (self.scr_width / 2, self.dashed_line_height * 2 * i + self.dashed_line_height)
            pygame.draw.line(self.screen, c_white, start_pos, end_pos, 3)

        pygame.display.flip()

    def update(self):
        dt = self.clock.tick(self._framerate)
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                self.should_quit = True
                return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                self.paused ^= 1
            if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                self.reset()

        if self.paused:
            return

        self.screen.fill(c_black)

        for o in self.objects.values():
            o.update(dt)

        for o in self.objects.values():
            o.draw(self.screen)
        
        for i in range(self.num_lines):
            start_pos = (self.scr_width / 2, self.dashed_line_height * 2 * i)
            end_pos =   (self.scr_width / 2, self.dashed_line_height * 2 * i + self.dashed_line_height)
            pygame.draw.line(self.screen, c_white, start_pos, end_pos, 3)

        pygame.display.flip()

    def reset(self):
        self.paused = True

        self.screen.fill(c_black)

        for o in self.objects.values():
            o.reset()
            o.draw(self.screen)

        pygame.display.flip()


def eval_genomes(genomes, config):
    paddles = []
    nets = []
    genomes = []
    
    for genome_id, genome in genomes:
        genome.fitness = 4.0
        net = neat.nn.FeedForwardNetwork.create(genome, config)

    # Create engine
        
    # while loop
        # update all paddles
            # If a paddle fails to reflect a ball, 
        # update engine

        #draw all paddles

        



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

    #open config

    #call run

    pge = Pong_Game_Engine()
    while not pge.should_quit:
        pge.update()



# TODO
    # Create run() function
        # Wrapper function for eval_genomes, includes neat setup

    # Create eval_genomes function
        # parameters: genomes, config

        # Create a paddle for each genome

        # Create one ball for each genome
            # Refactor ball to be a child class of the paddle

        # One iteration of the game,
            # score increases for every ball reflection
            # 

    # Ideas:
        # Ball speed increases logarithmically throughout the game
            # any other sublinear way?
            # Linearly

        # After model is trained play it vs all of us, see what scores we can get, how far the ai gets

        # Inputs
        # ball x
        # ball y
        # ball xspeed
        # ball yspeed
        # paddle y