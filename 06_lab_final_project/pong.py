import pygame
from pygame.locals import *
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

class Game:
    SCORE_FONT = pygame.font.SysFont("comicsans", 50)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)

    def __init__(self, window):
        self.FNT_DEBUG = None
        self.left_score = 0
        self.right_score = 0
        self.left_hits = 0
        self.right_hits = 0
        self.window = window

    def _draw_score(self):
        left_score_text = self.SCORE_FONT.render(
            f"{self.left_score}", 1, self.WHITE)
        right_score_text = self.SCORE_FONT.render(
            f"{self.right_score}", 1, self.WHITE)
        self.window.blit(left_score_text, (1280 //
                                           4 - left_score_text.get_width()//2, 20))
        self.window.blit(right_score_text, (1280 * (3/4) -
                                            right_score_text.get_width()//2, 20))

    def reset(self):
        """Resets the entire game."""
        self.left_score = 0
        self.right_score = 0



class Paddle_Play:
    width = 25
    height = 135  # Center at y + 67
    speed = 0.5
    player_controlled = False
    keybinds = {
        'up': pygame.K_w,
        'down': pygame.K_s
    }

    def __init__(self, x, y, keybinds=None):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        if keybinds is not None:
            self.keybinds = keybinds
        self.col = (random.randrange(125, 200), random.randrange(125, 200), random.randrange(125, 200))


    def reset(self):
        self.x = self.start_x
        self.y = self.start_y


    def update(self, dt):
        if self.player_controlled:
            if pygame.key.get_pressed()[self.keybinds['up']]:
                self.move_up(dt)
            if pygame.key.get_pressed()[self.keybinds['down']]:
                self.move_down(dt)


    def move_up(self, dt):
        if self.y == 0:
            return False
        self.y -= min(self.speed * dt, self.y)
        return True

    def move_down(self, dt):
        if self.y + self.height == WIN_HEIGHT:
            return False
        self.y += self.speed * dt
        if self.y + self.height > WIN_HEIGHT:
            self.y = WIN_HEIGHT - self.height
        return True

    def draw(self, surf):
        surf.fill(self.col, (self.x, self.y, self.width, self.height))


class Ball_Play:
    r = 10
    start_vel = 0.5

    def __init__(self, x, y, col):
        self.col = col
        self.x = x
        self.y = y

        self.start_x = x
        self.start_y = y


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

    def update(self, dt, LPaddle, RPaddle):
        # Move
        outcome = 0
        left_score = 0;
        right_score = 0;
        self.y += self.vel[1] * dt
        self.x += self.vel[0] * dt

        v = math.sqrt(self.vel[0] ** 2 + self.vel[1] ** 2)


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


        if self.x >= RPaddle.x and self.x <= RPaddle.x + RPaddle.width and self.y >= RPaddle.y and self.y <= RPaddle.y + RPaddle.height:
            # Ball collided with paddle
            outcome = 1
            v = math.log(math.exp(v) + 0.1)  # Add a logarithmic speed boost to the ball
            ydelt = self.y - (RPaddle.y + RPaddle.height / 2)
            angle = ydelt / RPaddle.height * math.pi / 2  # Value ranging from -pi/4 to pi/4 depending upon where the ball hit the paddle
            if self.vel[0] > 0:
                angle = math.pi - angle

        if self.x >= LPaddle.x and self.x <= LPaddle.x + LPaddle.width and self.y >= LPaddle.y and self.y <= LPaddle.y + LPaddle.height:
            # Ball collided with paddle
            outcome = 1
            v = math.log(math.exp(v) + 0.1)  # Add a logarithmic speed boost to the ball
            ydelt = self.y - (LPaddle.y + LPaddle.height / 2)
            angle = ydelt / LPaddle.height * math.pi / 2  # Value ranging from -pi/4 to pi/4 depending upon where the ball hit the paddle
            if self.vel[0] > 0:
                angle = math.pi - angle

        # Bounce the ball off the left wall
        if self.x < 0:
            outcome = 10
            right_score = right_score + 1;


        elif self.x > WIN_WIDTH:
            outcome = 11
            left_score = left_score + 1;

        self.vel = (v * math.cos(angle), v * math.sin(angle))


        return right_score, left_score, outcome

    def draw(self, surf):
        pygame.draw.circle(surf, self.col, (self.x, self.y), self.r)



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

        v = math.sqrt(self.vel[0] ** 2 + self.vel[1] ** 2)


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
            v = math.log(math.exp(v) + 0.1) #Add a logarithmic speed boost to the ball
            ydelt = self.y - (self.paddle.y + self.paddle.height/2)
            angle = ydelt/self.paddle.height * math.pi / 2 #Value ranging from -pi/4 to pi/4 depending upon where the ball hit the paddle
            if self.vel[0] > 0:
                angle = math.pi - angle

        # Bounce the ball off the left wall
        if self.x < 0:
            self.x *= -1
            angle  = math.pi - angle # flip the direction the ball is traveling over the y axis
            angle = random.uniform(math.pi/-4 , math.pi/4)
            #outcome = -1

        
        elif self.x > WIN_WIDTH:
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
        if self.y == 0:
            return False
        self.y -= min(self.speed*dt, self.y)
        return True

    def move_down(self, dt):
        if self.y + self.height == WIN_HEIGHT:
            return False
        self.y += self.speed*dt
        if self.y + self.height > WIN_HEIGHT:
            self.y = WIN_HEIGHT - self.height
        return True

    def draw(self, surf):
        surf.fill(self.col, (self.x, self.y, self.width, self.height))
        self.ball.draw(surf)

def gaus(z):
    return 1/math.sqrt(2*math.pi) * math.exp(-(z**2)/2)

def eval_genomes(genomes, config):
    paddles = []
    nets = []
    ge = []
    
    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        ge.append(genome)
        nets.append(net)
        paddles.append(Paddle(WIN_WIDTH-30, WIN_HEIGHT/2 - 67))


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

            inputs = (  p.ball.x,       # Ball pos
                        p.ball.y, 
                        #p.ball.vel[0], # Ball Vel
                        #p.ball.vel[1], 
                        p.y)            # Paddle pos (1D)
            output = n.activate(inputs)

            if (output[0] > 0.5) ^ (output[1] > 0.5):
                moved = False
                if output[0] > 0.5:
                    moved = p.move_up(dt)
                if output[1] > 0.5:
                    moved = p.move_down(dt)
                
                if moved:
                    ydelt = abs(p.y + p.height/2 - p.ball.y) / p.height
                    g.fitness += 5*gaus(ydelt)
                else:
                    g.fitness -= 1
            else:
                g.fitness -= 0.05
            
 
            

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

def test_ai(net):
    User = Paddle_Play(30, WIN_HEIGHT/2, keybinds=True)
    AI = Paddle_Play(WIN_WIDTH-30, WIN_HEIGHT/2)
    #test_P = Paddle_Play(WIN_WIDTH-30, WIN_HEIGHT/2, keybinds=True)
    Ball_In = Ball_Play(WIN_WIDTH/2, WIN_HEIGHT/2, c_white)
    Game_play = Game(window=WIN)
    clock = pygame.time.Clock()


    run = True
    while run:
        dt = clock.tick(60)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                run = False
                break

        inputs = (Ball_In.x,  # Ball pos
                  Ball_In.y,
                  #AI.ball.vel[0], # Ball Vel
                  #AI.ball.vel[1],
                  AI.y)  # Paddle pos (1D)
        output = net.activate(inputs)
        if output[0] > 0.5:
            AI.move_up(dt)
        if output[1] > 0.5:
            AI.move_down(dt)

        outcome = AI.update(dt)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            User.move_up(dt)
            #test_P.move_up(dt)
        if keys[pygame.K_s]:
            User.move_down(dt)
            #test_P.move_down(dt)

        WIN.fill(c_black)

        # Draw lines in the middle
        num_lines = math.ceil(WIN_HEIGHT / 25 / 2)
        for i in range(num_lines):
            start_pos = (WIN_WIDTH / 2, 25 * 2 * i)
            end_pos = (WIN_WIDTH / 2, 25 * 2 * i + 25)
            pygame.draw.line(WIN, c_white, start_pos, end_pos, 3)


        AI.draw(WIN)
        #test_P.draw(WIN)
        User.draw(WIN)
        Ball_In.draw(WIN)
        RScore, LScore, Check_Score = Ball_In.update(dt=dt, LPaddle=User, RPaddle=AI)

        if Check_Score == 10 or Check_Score == 11:
            Game_play.right_score = Game_play.right_score + RScore
            Game_play.left_score = Game_play.left_score + LScore
            #test_P.reset()
            #AI.reset()
            #User.reset()
            Ball_In.reset()

        # if Game_play.right_score == 5 or Game_play.left_score == 5:
        #     if Game_play.right_score == 5:
        #         text = FNT_DEBUG.render("AI Wins", True, c_white)
        #         textRect = text.get_rect()
        #         textRect.center = (1280 // 2, 720 // 2)
        #         WIN.blit(text, textRect)
        #         # for g in pygame.event.get():
        #         #     if g.type == pygame.K_w:
        #         #         break
        #         event = pygame.event.wait()
        #         if event.type == QUIT:
        #             pygame.quit()
        #         elif event.type == KEYDOWN:
        #             pass



            # else:
            #     text = FNT_DEBUG.render("You Win", True, c_white)
            #     textRect = text.get_rect()
            #     textRect.center = (1280 // 2, 720 // 2)
            #     WIN.blit(text, textRect)


        Game_play._draw_score()

        pygame.display.flip()

def play_ai(config):
    with open("best_net.pkl", "rb") as f:
        winner = pickle.load(f)
    #winner_net = neat.nn.FeedForwardNetwork.create(winner,config)
    test_ai(winner)



def run(config_path):
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    #Added -Josh
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(1))

    winner = p.run(eval_genomes, 300)
    winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
    pickle.dump(winner_net, open('./best_net.pkl', 'wb'))

   
    


if __name__ == '__main__':
    #Train AI
    #run('C:/Pycharm/Pong NEAT/config.txt')

    #Play Against AI
    play_ai('C:/Pycharm/Pong NEAT/config.txt')


# TODO
    # Add in current highest fintess within and out of generation