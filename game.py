import pygame
import socket


# Use a players array based on id, based the players creation function from the server to add attributes.
class Player:
    def __init__(self, identity):
        self.identity = identity
        self.colour = False
        self.name = False
        self.health = 0
        self.position = False
        self.kills = 0
        self.status = False

    def update(self, data):
        if data[0] == "n":
            self.name = data[1:]
        elif data[0] == "c":
            self.colour = (int(data[1:4]), int(data[4:7]), int(data[7:10]))
        elif data[0] == "h":
            self.health = int(data[1:])
        elif data[0] == "p":
            self.position = (int(data[1:5]), int(data[5:9]))
        elif data[0] == "k":
            self.kills = int(data[1:])
        self.status = all([self.colour, self.name, self.health, self.position])


class Laser:
    def __init__(self, data):
        self.laser_id = data[0:3]
        self.player_id = data[3:5]
        self.colour = (int(data[5:8]), int(data[8:11]), int(data[11:14]))
        self.position = [int(data[14:18]), int(data[18:22])]


class Client(Player):
    def __init__(self):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.connection.setblocking(True)
        self.players = dict()
        self.lasers = dict()
        self.name = str()
        self.colour = tuple()
        self.health = int()
        self.position = tuple()
        self.kills = int()

    def connect(self, ip):
        try:
            self.connection.connect((ip, 6000))
            return True
        except ConnectionError:
            return False

    def senddata(self, data):
        self.connection.sendall(data.encode())

    def receivedata(self):
        return self.connection.recv(1024).decode()

    def sendplayerdata(self, item):
        if item == "p":
            self.senddata("+p" + str(self.position[0]).split(".")[0].zfill(4) + str(self.position[1]).split(".")[0].zfill(4))
        elif item == "c":
            self.senddata("+c" + "".join([str(colour).zfill(3) for colour in self.colour]))
        elif item == "h":
            self.senddata("+h" + str(self.health).zfill(3))
        elif item == "n":
            self.senddata("+n" + self.name + " " * (8 - len(self.name)))
        elif item[0] == "o":
            self.senddata("+o" + item[1:])
        elif item[0] == "k":
            self.senddata("+k" + item[1:])

        # for lasers:
        elif item in list("wasd"):
            self.senddata("+l" + item + str(self.position[0]).zfill(4) + str(self.position[1]).zfill(4))

    def update_game(self):
        self.lasers.clear()
        try:
            received = self.receivedata()
            for command in received.split("+"):
                if command == '':
                    pass
                elif command == "u":
                    pass
                elif command[0] == "v":
                    try:
                        self.lasers[command[1:4]] = Laser(command[1:])
                    except ValueError:
                        pass
                else:
                    identity = command[0:2]
                    data = command[2:]
                    if identity not in self.players:
                        self.players[identity] = Player(identity)
                    if data[0] == "z":
                        del self.players[identity]
                    elif data[0] == "x":
                        self.disconnect()
                    elif data[0] in list("nchpk"):
                        self.players[identity].update(data)

        except IndexError:
            pass

    def validip(self, ip):
        if all([character in list("0123456789.") for character in ip]):
            try:
                if all([int(section) <= 255 for section in ip.split(".")]):
                    if len(ip.split(".")) == 4:
                        return True
            except ValueError:
                return False
        return False

    def disconnect(self):
        self.players.clear()
        try:
            self.senddata("+x")
        except socket.error:
            pass
        self.connection.close()

    def reset_client(self):
        self.health = int()
        self.kills = 0
        self.position = [600, 600]


class Mainloop(Client):
    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(100, 50)
        self.window_size = (800, 400)
        self.window = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        pygame.display.set_caption("BLASTR")
        Client.__init__(self)

        self.stage = self.start_screen
        while True:
            self.stage = self.stage()

    def display_text(self, text, size, colour, position, anchor, rel):
        # text = string, size = integer, colour = (RRR, GGG, BBB), position = (float, float), anchor = centre, left, right, top, bottom.
        text_surface = pygame.font.Font("freesansbold.ttf", size).render(text, True, colour)
        text_rect = text_surface.get_rect()
        if rel:
            if anchor == "center":
                text_rect.center = (position[0] * self.window_size[0], position[1] * self.window_size[1])
            elif anchor == "midleft":
                text_rect.midleft = (position[0] * self.window_size[0], position[1] * self.window_size[1])
            elif anchor == "midright":
                text_rect.midright = (position[0] * self.window_size[0], position[1] * self.window_size[1])
            elif anchor == "midbottom":
                text_rect.midbottom = (position[0] * self.window_size[0], position[1] * self.window_size[1])
        else:
            if anchor == "center":
                text_rect.center = position
            elif anchor == "midleft":
                text_rect.midleft = position
            elif anchor == "midright":
                text_rect.midright = position
            elif anchor == "midbottom":
                text_rect.midbottom = position
        self.window.blit(text_surface, text_rect)

    def display_rect(self, pos, size, colour, rel):
        if rel:
            pos = (pos[0] * self.window_size[0], pos[1] * self.window_size[1])
            size = (size[0] * self.window_size[0], size[1] * self.window_size[1])
        rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
        pygame.draw.rect(self.window, colour, rect)
        return rect

    def create_textrect(self, pos, rect_size, rect_colour, rel, text, text_size, text_colour, anchor):
        rect = self.display_rect(pos, rect_size, rect_colour, rel)
        self.display_text(text, text_size, text_colour, rect.center, anchor, False)
        return rect

    def pos_to_coords(self, coords, rel_screen):
        coords = [coords[0], coords[1]]
        screen_size = [200, 200]
        screen_pos = [0, 0]
        for i in range(0, 2):
            if self.position[i] > 500:
                screen_pos[i] = min(self.position[i] - (screen_size[i] / 2), 1000 - screen_size[i])
            else:
                screen_pos[i] = max(self.position[i] - (screen_size[i] / 2), 0)

        for i in range(0, len(coords)):
            if rel_screen:
                coords[i] = (coords[i] - screen_pos[i % 2]) * (self.window_size[i % 2] / screen_size[i % 2])
            else:
                coords[i] = coords[i] * (self.window_size[i % 2] / screen_size[i % 2])
        return coords

    def start_screen(self):
        gui_stage = "start"

        while True:
            if gui_stage == "start":
                self.window.fill((0, 0, 0))
                start_button = self.create_textrect((0.1, 0.1), (0.8, 0.6), (0, 225, 0), True, "CONNECT TO SERVER", 50, (225, 225, 225), "center")
                credits_button = self.create_textrect((0.1, 0.7), (0.4, 0.2), (0, 0, 225), True, "CREDITS", 30, (225, 225, 225), "center")
                quit_button = self.create_textrect((0.5, 0.7), (0.4, 0.2), (225, 0, 0), True, "QUIT", 30, (225, 225, 225), "center")
                back_button = None
            elif gui_stage == "credits":
                self.window.fill((0, 0, 0))
                self.create_textrect((0.1, 0.1), (0.8, 0.7), (225, 225, 225), True, "THIS GAME WAS DEVELOPED BY OLIVER KILLANE.", 30, (0, 0, 0), "center")
                back_button = self.create_textrect((0.1, 0.7), (0.8, 0.2), (225, 225, 0), True, "BACK", 30, (0, 0, 0), "center")

            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONUP:
                    if gui_stage == "start":
                        if start_button.collidepoint(event.pos):
                            return self.enter_ip
                        elif quit_button.collidepoint(event.pos):
                            pygame.display.quit()
                            quit()
                        elif credits_button.collidepoint(event.pos):
                            gui_stage = "credits"
                    elif gui_stage == "credits":
                        if back_button.collidepoint(event.pos):
                            gui_stage = "start"
                            self.window.fill((0, 0, 0))
                elif event.type == pygame.VIDEORESIZE:
                    self.window_size = event.size
                    self.window = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
                elif event.type == pygame.QUIT:
                    pygame.display.quit()
                    quit()
            pygame.display.update()

    def enter_ip(self):
        gui_stage = "enter_ip"
        ip = str()
        while True:
            # Window Setup:
            if gui_stage == "enter_ip":
                self.window.fill((0, 0, 0))
                self.display_text("ENTER IP:", 50, (255, 255, 255), (0.5, 0.2), "center", True)
                back_button = self.create_textrect((0.3, 0.9), (0.4, 0.1), (255, 0, 0), True, "BACK", 50, (255, 255, 255), "center")
                self.display_text(ip, 30, (255, 255, 255), (0.5, 0.6), "center", True)
                if self.validip(ip):
                    connect_button = self.create_textrect((0.3, 0.8), (0.4, 0.1), (0, 255, 0), True, "CONNECT", 50, (255, 255, 255), "center")
            elif gui_stage == "connecting":
                self.window.fill((0, 225, 0))
                self.display_text("CONNECTING TO: " + ip, 50, (255, 255, 255), (0.5, 0.5), "center", True)
                if self.connect(ip):
                    return self.create_player
                else:
                    gui_stage = "failed"
            elif gui_stage == "failed":
                self.window.fill((255, 0, 0))
                self.display_text("CONNECTION FAILED", 50, (255, 255, 255), (0.5, 0.2), "center", True)
                back_button = self.create_textrect((0.3, 0.8), (0.4, 0.1), (255, 255, 255), True, "BACK", 50, (255, 0, 0), "center")

            # Events:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.display.quit()
                    quit()
                elif event.type == pygame.VIDEORESIZE:
                    self.window_size = event.size
                    self.window = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
                elif gui_stage == "enter_ip":
                    if event.type == pygame.KEYDOWN:
                        if event.unicode in list("0123456789.") and len(ip) < 15:
                            ip += event.unicode
                        elif event.unicode == "\x08":
                            ip = ip[:-1]
                        if self.validip(ip) and event.unicode == "\r":
                            gui_stage = "connecting"
                    if event.type == pygame.MOUSEBUTTONUP:
                        if self.validip(ip):
                            if connect_button.collidepoint(event.pos):
                                gui_stage = "connecting"
                        if back_button.collidepoint(event.pos):
                            return self.start_screen
                elif gui_stage == "failed":
                    if event.type == pygame.MOUSEBUTTONUP:
                        if back_button.collidepoint(event.pos):
                            return self.start_screen

            pygame.display.update()

    def create_player(self):
        # Allowed colours:
        player_colours = [(255, 51, 51), (255, 153, 51), (255, 255, 51), (153, 255, 51), (51, 255, 51), (51, 255, 153), (51, 255, 255), (51, 153, 255), (153, 51, 255), (255, 51, 255), (255, 51, 153)]
        colour_rects = dict()

        # Player information:
        player_colour = False
        player_name = str()

        # Button setup to prevent errors from conditional.
        start_game = False

        while True:
            self.update_game()
            self.window.fill((225, 0, 0))
            self.display_text("PLAYER SETUP", 50, (0, 0, 0), (0.5, 0.1), "center", True)

            # Player name input
            self.display_text(player_name, 30, (0, 0, 0), (0.5, 0.3), "center", True)
            if any([player_name == player.name for player in self.players.values()]):
                self.display_text("THIS NAME IS TAKEN", 30, (255, 255, 255), (0.5, 0.5), "center", True)

            # Colours:
            available_colours = [colour for colour in player_colours if not any([colour == player.colour for player in self.players.values()])]
            for index in range(0, len(available_colours)):
                colour_rects[available_colours[index]] = self.display_rect((index / len(available_colours), 0.7), (1 / len(available_colours), 0.1), available_colours[index], True)
            for colour in colour_rects:
                if colour == player_colour:
                    selector = pygame.Rect(0, 0, 0.02 * self.window_size[0], 0.02 * self.window_size[1])
                    selector.center = colour_rects[colour].center
                    pygame.draw.rect(self.window, (255, 255, 255), selector)

            # Enter Buttons
            if player_colour and not any([player_name == player.name for player in self.players.values()]) and len(player_name) <= 8 and len(player_name) > 0:
                start_game = self.create_textrect((0.3, 0.8), (0.4, 0.1), (0, 255, 0), True, "START GAME", 50, (255, 255, 255), "center")
            else:
                start_game = False
            back_button = self.create_textrect((0.3, 0.9), (0.4, 0.1), (255, 0, 0), True, "BACK", 50, (255, 255, 255), "center")

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if (event.unicode.isalpha() or event.unicode.isnumeric()) and len(player_name) < 8:
                        player_name += event.unicode
                    elif event.unicode == "\x08":
                        player_name = player_name[:-1]
                elif event.type == pygame.MOUSEBUTTONUP:
                    for colour in colour_rects:
                        if colour_rects[colour].collidepoint(event.pos):
                            player_colour = colour
                    if start_game:
                        if start_game.collidepoint(event.pos):
                            self.colour = player_colour
                            self.name = player_name
                            self.health = 10
                            self.kills = 0
                            return self.game_loop
                    if back_button.collidepoint(event.pos):
                        self.disconnect()
                        return self.start_screen
                elif event.type == pygame.VIDEORESIZE:
                    self.window_size = event.size
                    self.window = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
                elif event.type == pygame.QUIT:
                    self.disconnect()
                    pygame.display.quit()
                    quit()
            pygame.display.update()

    def game_loop(self):
        # Start position
        self.position = [600, 600]
        self.health = 10

        # Gui stage declaration
        gui_stage = "game"

        # send initial player data
        self.sendplayerdata("p")
        self.sendplayerdata("c")
        self.sendplayerdata("h")
        self.sendplayerdata("n")

        # The map in world coordinates
        game_map = [[(40, 40), (80, 440)], [(160, 40), (600, 40)], [(760, 40), (120, 320)], [(160, 120), (520, 80)], [(320, 200), (80, 240)], [(160, 240), (80, 80)], [(440, 240), (160, 120)],
                    [(640, 240), (80, 320)], [(40, 520), (80, 440)], [(160, 360), (80, 80)], [(160, 440), (40, 440)], [(920, 40), (40, 240)], [(240, 640), (80, 240)], [(320, 640), (80, 40)],
                    [(400, 640), (160, 240)], [(760, 400), (40, 320)], [(160, 920), (640, 40)], [(760, 800), (40, 120)], [(600, 800), (160, 80)], [(920, 320), (40, 240)], [(920, 600), (40, 240)],
                    [(840, 400), (40, 560)], [(880, 880), (80, 80)]]

        # The arrays to hold rects of objects in game (so that rect.colliderect(rect) can be used)
        map_rects = list()
        player_rects = list()
        laser_rects = dict()

        # Laser countdown variable:
        laser_cooldown = 0

        # Death screen requires the killing player's name:
        killed_by = str()

        # Buttons for :
        quit_button = None
        respawn_button = None

        while True:
            self.update_game()
            self.window.fill((255, 255, 255))
            last_position = self.position[:]
            laser_cooldown -= 1
            map_rects.clear()

            # get input
            if gui_stage == "game":
                input = pygame.key.get_pressed()
                if input[pygame.K_w]:
                    self.position[1] -= 1
                if input[pygame.K_s]:
                    self.position[1] += 1
                if input[pygame.K_a]:
                    self.position[0] -= 1
                if input[pygame.K_d]:
                    self.position[0] += 1
                if laser_cooldown <= 0:
                    if input[pygame.K_UP]:
                        self.sendplayerdata("w")
                        laser_cooldown = 25
                    elif input[pygame.K_DOWN]:
                        self.sendplayerdata("s")
                        laser_cooldown = 25
                    elif input[pygame.K_LEFT]:
                        self.sendplayerdata("a")
                        laser_cooldown = 25
                    elif input[pygame.K_RIGHT]:
                        self.sendplayerdata("d")
                        laser_cooldown = 25

                # Player position reset if it is invalid
                if not 5 <= self.position[0] <= 995 or not 5 <= self.position[1] <= 995:
                    self.position = last_position[:]
                client_rect = pygame.Rect(self.pos_to_coords([self.position[0] - 5, self.position[1] - 5], True), self.pos_to_coords([10, 10], False))
                for pos in game_map:
                    if client_rect.colliderect(pygame.Rect(self.pos_to_coords(pos[0], True), self.pos_to_coords(pos[1], False))):
                        self.position = last_position[:]
                        break

                # As the player's position should be valid:
                if last_position != self.position:
                    self.sendplayerdata("p")

                # Render Walls
                map_rects.clear()
                for pos in game_map:
                    map_rects.append(pygame.Rect(self.pos_to_coords(pos[0], True), self.pos_to_coords(pos[1], False)))
                [pygame.draw.rect(self.window, (50, 50, 50), rect) for rect in map_rects]

                # Render Other players
                player_rects.clear()
                for player in self.players.values():
                    if player.status and player.health:
                        player_rects.append(pygame.Rect(pygame.Rect(self.pos_to_coords([player.position[0] - 5, player.position[1] - 5], True), self.pos_to_coords([10, 10], False))))
                        pygame.draw.rect(self.window, player.colour, pygame.Rect(self.pos_to_coords([player.position[0] - 5, player.position[1] - 5], True), self.pos_to_coords([10, 10], False)))
                        self.display_text(player.name, 10, (0, 0, 0), self.pos_to_coords(player.position, True), "center", False)

                # Render Lasers and check laser
                laser_rects.clear()
                for laser in self.lasers.values():
                    laser_rect = pygame.Rect(self.pos_to_coords([laser.position[0] - 1.5, laser.position[1] - 1.5], True), self.pos_to_coords([3, 3], False))
                    if client_rect.colliderect(laser_rect) and laser.player_id in [player_obj.identity for player_obj in self.players.values()]:
                        self.sendplayerdata("o" + laser.laser_id)
                        self.health -= 1
                        self.sendplayerdata("h")
                        if self.health == 0:
                            print("killed")
                            self.sendplayerdata("k" + laser.player_id)
                            if not killed_by:
                                killed_by = self.players[laser.player_id].name
                                print(killed_by)
                            self.reset_client()
                            gui_stage = "killed"
                    if any([laser_rect.colliderect(map_rect) for map_rect in map_rects]):
                        self.sendplayerdata("o" + laser.laser_id)
                    laser_rects[laser.player_id] = laser_rect
                    pygame.draw.rect(self.window, laser.colour, pygame.Rect(self.pos_to_coords(laser.position, True), self.pos_to_coords([3, 3], False)))

                pygame.draw.rect(self.window, self.colour, pygame.Rect(self.pos_to_coords([self.position[0] - 5, self.position[1] - 5], True), self.pos_to_coords([10, 10], False)))

                if input[pygame.K_TAB]:
                    self.display_text("NAME:", 15, (0, 0, 0), (0.1, 0.1), "center", True)
                    self.display_text("HEALTH:", 15, (0, 0, 0), (0.2, 0.1), "center", True)
                    self.display_text("KILLS:", 15, (0, 0, 0), (0.3, 0.1), "center", True)
                    kill_list = sorted(list(self.players.values()), key=lambda player_obj: player_obj.kills)
                    for item in kill_list:
                        if not item.status:
                            kill_list.remove(item)

                    for index in range(0, len(kill_list)):
                        if kill_list[index].kills <= self.kills:
                            kill_list.insert(index, "CLIENT")
                            break
                    for index in range(0, min(7, len(kill_list))):
                        if kill_list[index] == "CLIENT":
                            self.display_text(self.name, 15, (255, 0, 0), (0.1, 0.2 + index * 0.1), "center", True)
                            self.display_text(str(self.health), 15, (255, 0, 0), (0.2, 0.2 + index * 0.1), "center", True)
                            self.display_text(str(self.kills), 15, (255, 0, 0), (0.3, 0.2 + index * 0.1), "center", True)
                        else:

                            self.display_text(kill_list[index].name, 15, (0, 0, 0), (0.1, 0.2 + index * 0.1), "center", True)
                            self.display_text(str(kill_list[index].health), 15, (0, 0, 0), (0.2, 0.2 + index * 0.1), "center", True)
                            self.display_text(str(kill_list[index].kills), 15, (0, 0, 0), (0.3, 0.2 + index * 0.1), "center", True)


            elif gui_stage == "killed":
                self.window.fill((0, 0, 0))
                self.display_text("YOU WERE KILLED BY: " + killed_by, 50, (255, 0, 0), (0.5, 0.3), "center", True)
                respawn_button = self.create_textrect((0.3, 0.5), (0.4, 0.1), (0, 255, 0), True, "RESPAWN", 50, (255, 255, 255), True)
                quit_button = self.create_textrect((0.3, 0.7), (0.4, 0.1), (0, 0, 255), True, "QUIT", 50, (255, 255, 255), True)

            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONUP:
                    if gui_stage == "killed":
                        if respawn_button.collidepoint(event.pos):
                            self.health = 10
                            self.sendplayerdata("h")
                            gui_stage = "game"
                        elif quit_button.collidepoint(event.pos):
                            self.disconnect()
                            return self.start_screen
                elif event.type == pygame.VIDEORESIZE:
                    self.window_size = event.size
                    self.window = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
                elif event.type == pygame.QUIT:
                    self.disconnect()
                    pygame.display.quit()
                    quit()
            pygame.display.update()


# TODO BUGS:
#   - Player camera view bug [FIXED]
#   - Colours not showing up for a second player entering the game [LINUX INCOMPATABILITY]
#   - When connected to a LAN but not the internet issue occurs [FIXED]
#   - Kick button does not work properly [FIXED]
#   - Server ceases up when a client is not connected - potential solution: have a client created by the server connect immediately
#   - Cannot see other players rects, self.players has 3 instead of 2 in test, ids seem wrong. [FIXED]

# TODO FEATURES:
#   - Add in collision detection for the map [DONE]
#   - Add in laser collision detection and send kill to correct player [DONE]
#   - Add in menu on escape key to show player kills, respawn and quit
#   - Add names to player blocks [DONE]
#   - Set controls to work not through event queue but by keypress [DONE]

# TODO BIG BUG: Not sending player data for some stupid fucking reason [FIXED]