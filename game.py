import pygame
import math
from network import Network

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.lerp_speed = 0.1  # Adjust this value to change the speed of the camera movement

    def apply(self, entity):
        return pygame.Rect(entity.rect.x - self.camera.x, entity.rect.y - self.camera.y, entity.rect.width, entity.rect.height)

    def update(self, target):
        target_center_x = target.rect.centerx
        target_center_y = target.rect.centery

        # Linear interpolation (lerp) for smooth camera movement
        self.camera.x += (target_center_x - self.camera.x - self.width // 2) * self.lerp_speed
        self.camera.y += (target_center_y - self.camera.y - self.height // 2) * self.lerp_speed

        # Limit scrolling to map size
        self.camera.x = max(-(self.width // 2), min(self.camera.x, target.rect.width - self.width // 2))
        self.camera.y = max(-(self.height // 2), min(self.camera.y, target.rect.height - self.height // 2))

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
        self.glide_x = 0
        self.glide_y = 0
    
    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, g, camera):
        g.blit(self.surf, camera.apply(self))
        
    def move(self, direction):
        if direction == 0:  # Rotate right
            self.angle += self.rotation_speed
        elif direction == 1:  # Rotate left
            self.angle -= self.rotation_speed
        elif direction == 2:  # Move forward
            self.speed = min(self.speed + self.acceleration, self.max_speed)
            self.glide_x = math.cos(math.radians(self.angle))
            self.glide_y = math.sin(math.radians(self.angle))
    
        # Update position based on speed and angle
        self.x += self.glide_x * self.speed
        self.y -= self.glide_y * self.speed  # Subtract to make the movement relative to the player's direction
    
        # Deceleration
        self.speed *= 0.99


class Game:

    def __init__(self, w, h, debug=False):
        self.debug = debug
        if not self.debug:
            self.net = Network()
            self.players = [self.net.getPlayer()]
        else:
            self.players = [Player(100,100)]
            
        self.camera = Camera(500,500)
        self.width = w
        self.height = h
        # self.player = Player(50, 50)
        # self.player2 = Player(100,100)
        cell_size = 50
        self.canvas = Canvas(self.width, self.height, cell_size, "Testing...")

    def run(self):
        clock = pygame.time.Clock()
        run = True
        while run:
            
            clock.tick(60)
            
            self.camera.update(self.players[0])
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

            # for entity in [self.player, self.player2]:
            #     entity.draw(self.canvas.get_canvas(), self.camera)

            keys = pygame.key.get_pressed()

            if keys[pygame.K_RIGHT]:
                self.players[0].move(0)

            if keys[pygame.K_LEFT]:
                self.players[0].move(1)

            if keys[pygame.K_UP]:
                self.players[0].move(2)

            # Send Network Stuff
            
            if not self.debug:
                player_data = self.send_data()
                other_players = self.parse_data(player_data)
                self.players = [self.players[0]] + other_players
            # self.player2.x, self.player2.y = self.parse_data(self.send_data())

            # Update Canvas
            
            self.canvas.draw_background()
            for player in self.players:
                player.draw(self.canvas.get_canvas(), self.camera)
            self.canvas.update()
            # self.canvas.draw_background()
            # self.player.draw(self.canvas.get_canvas(), self.camera)
            # self.player2.draw(self.canvas.get_canvas(), self.camera)
            # self.canvas.update()

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
    
    def __init__(self, w, h, cell_size, name="None"):
        self.width = w
        self.height = h
        self.cell_size = cell_size
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
        self.screen.fill((0, 0, 0))
        
        for x in range(0, self.width, self.cell_size):
            pygame.draw.line(self.screen, (255,255,255), (x,0), (x,self.height))
        for y in range(0, self.height, self.cell_size):
            pygame.draw.line(self.screen, (255,255,255), (0,y), (self.width,y))