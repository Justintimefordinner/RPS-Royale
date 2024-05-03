import pygame
import math
from network import Network

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + int(self.width / 2)
        y = -target.rect.centery + int(self.height / 2)

        self.camera = pygame.Rect(x, y, self.width, self.height)

class Player():
    width = height = 50

    def __init__(self, startx, starty, color=(255,0,0)):
        self.x = startx
        self.y = starty
        self.velocity = 2
        self.color = color
        self.surf = pygame.Surface((self.width, self.height))
        self.surf.fill(self.color)
        self.angle = 0
        self.rotation_speed = 5
        self.speed = 0
        self.acceleration = 1
        self.max_speed = 10
    
    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, g, camera):
        self.surf = pygame.Surface((self.width, self.height))
        self.surf.fill(self.color)
        g.blit(self.surf, camera.apply(self))
        
    def move(self, direction):
        if direction == 0:  # Rotate right
            self.angle += self.rotation_speed
        elif direction == 1:  # Rotate left
            self.angle -= self.rotation_speed
        elif direction == 2:  # Move forward
            self.speed = min(self.speed + self.acceleration, self.max_speed)

        # Update position based on speed and angle
        self.x += math.cos(math.radians(self.angle)) * self.speed
        self.y += math.sin(math.radians(self.angle)) * self.speed

        # Deceleration
        self.speed *= 0.99


class Game:

    def __init__(self, w, h):
        self.net = Network()
        self.width = w
        self.height = h
        self.player = Player(50, 50)
        self.player2 = Player(100,100)
        self.canvas = Canvas(self.width, self.height, "Testing...")
        self.camera = Camera(w, h)

    def run(self):
        clock = pygame.time.Clock()
        run = True
        while run:
            clock.tick(60)
            self.camera.update(self.player)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

            for entity in [self.player, self.player2]:
                entity.draw(self.canvas.get_canvas(), self.camera)

            keys = pygame.key.get_pressed()

            if keys[pygame.K_RIGHT]:
                self.player.move(0)

            if keys[pygame.K_LEFT]:
                self.player.move(1)

            if keys[pygame.K_UP]:
                self.player.move(2)

            # Send Network Stuff
            self.player2.x, self.player2.y = self.parse_data(self.send_data())

            # Update Canvas
            self.canvas.draw_background()
            self.player.draw(self.canvas.get_canvas())
            self.player2.draw(self.canvas.get_canvas())
            self.canvas.update()

        pygame.quit()

    def send_data(self):
        """
        Send position to server
        :return: None
        """
        data = str(self.net.id) + ":" + str(self.player.x) + "," + str(self.player.y)
        reply = self.net.send(data)
        return reply

    @staticmethod
    def parse_data(data):
        try:
            d = data.split(":")[1].split(",")
            return int(d[0]), int(d[1])
        except:
            return 0,0


class Canvas:

    def __init__(self, w, h, name="None"):
        self.width = w
        self.height = h
        self.screen = pygame.display.set_mode((w,h))
        pygame.display.set_caption(name)

    @staticmethod
    def update():
        pygame.display.update()

    def draw_text(self, text, size, x, y):
        pygame.font.init()
        font = pygame.font.SysFont("comicsans", size)
        render = font.render(text, 1, (0,0,0))

        self.screen.draw(render, (x,y))

    def get_canvas(self):
        return self.screen

    def draw_background(self):
        self.screen.fill((255,255,255))
