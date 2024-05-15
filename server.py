# --==BLOCK BLASTR BY OLIVER KILLANE==--
# GAME DESCRIPTION AND CODE EXPLANATION:
# SERVER PROTOCOLS
# all messages are in chunks, each with a + either side, to client has id between + and command.
# Types:
#   name            "+n12345678"        e.g. "+nOliver  "
#   colour          "+c123123123"       e.g. "+c000225000"
#   health          "+h123"             e.g. "+h012"
#   position        "+p12341234"        e.g. "+p01231445"
#   closing         "+x"                N/A
#   new frame       "+u"                N/A
#   new laser       "+lw12341234"       e.g. "+ls06000800"
#   laser update    "+v1231212341234"   e.g. "+v0010206000880"
#   laser gone      "+o123"             e.g. "+o002"
#   player gone     "+z"                e.g. "+z01"
#   player killed   "+k12"              e.g. "+k00"
#
# DATA HANDLING
#   Player Position:    Client --> Server (id added) --> Other Clients
#   Player Name:        Client --> Server (id added) --> Other Clients
#   Player Colour:      Client --> Server (processed for display only) (id added) --> Other Clients
#   Health:             Client --> Server (id added) --> Other Clients
#   Closing:            Client --> Server -->Other Clients or Server --> Client then Server --> Other Clients
#   New Laser:          Client --> Server (processed continuously) --> All Clients (continuously)
#   Laser Update:       Server (removes direction) --> All Clients
#   Laser Gone:         Client --> Server --> All Clients
#   Player Gone:        Client --> Server --> All Clients or Server --> All Clients
#
# PLAYER OBJECT
# An object containing all information on a player.
# Attributes:   Type:   Description:
#   properties      Dict    Holds all of the information other clients require in a dictionary:
#                           self.properties = {"c": string, "n": string, "p": string, "h": string, "k": int}
#
#   colour_format   Tuple   Holds a tuple with the information for the player's colour that pygame can display:
#                           (int, int, int)
#
#   identity        String  The identity of the player within the game, denoted by its key within the self.players dictionary
#                           Identity is a 2 character string of numbers (from 0 to 99).
#
#   connection      Socket  Holds the socket.socket object that is used to communicate with this client from.
#
#   update          Dict    Contains all the players that the client needs to be updated on and the attributes that need updating
#                           update = {...player_id : [attribute, e.g "p","n"], ...}
#
#   status          Boolean Determines if the player has the required information to play.
#
# Methods:      Parameters:     Description
#   update_data     data (string)   Takes new data as supplied by the client and updates the properties of the player based on it.
#                                   The data is in form (type char)(...data...) e.g "c255255255"
#
#   reset_player    N/A             Resets the player's attributes but keeps them connected - so they can easily re-enter the game if they die.
#
# LASER CLASS
# Attributes:   Type:       Description:
#   position        Tuple       Holds two integers representing the position of a laser in the game
#
#   data            String      The formatted string of information about the laser, laser_id, player_id, direction and current position

#
# SERVER CLASS
# Attributes:   Type:       Description:
#   server_state    String      Holds the state of the server, namely, offline, initialising or online.
#
#   server          Socket      Holds the socket object used by the server. Ip is taken from socket.getsockname() --> (ip, port)
#
#   players         Dict        Holds a dictionary where the keys are identities and values players.
#                               e.g {..."01" : <Player Object>,...}
#
# Methods:      Parameters:     Description:
#   start_server    N/A             Creates the socket server object, changes server_state to reflect this.
#
#   process_data    data(string)    Takes the message containing player data sent to the server and updates properties, update.
#                   client_id (Socket)
#
#   server_clients  N/A             Runs the main server loop, takes inputs, outputs relevant data.
#
#   remove_player   client_id (string)  Removes a client due to disconnection or being kicked.
#
#   stop_server     N/A             Shuts server down.
#
#   socket_to_id    Client (Socket) Gives the relevant player id of a socket connection.
#
#   add_player      Client (Socket) Adds a new player into the players list.
#
#   remove_dead     Removes dead Player objects

import socket
import select
import pygame
import _thread as thread

class Player:
    def __init__(self, identity, connection):
        self.properties = {"c": False, "n": False, "p": False, "h": 0, "k": 0}
        self.colour_formatted = False
        self.identity = identity
        self.connection = connection
        self.update = dict()
        self.status = False

    def update_data(self, data):
        self.properties[data[0]] = data[1:]
        if data[0] == "c":
            self.colour_formatted = (int(data[1:4]), int(data[4:7]), int(data[7:10]))
        self.status = all([self.properties[index] for index in self.properties if index != "k"])

    def reset_player(self):
        self.properties = {"c": False, "n": False, "p": False, "h": False, "k": 0}
        self.colour_formatted = False
        self.status = False

class Laser:
    def __init__(self, data, id, colour, player_id):
        self.data = str()
        self.colour = colour
        self.position = [int(data[1:5]), int(data[5:9])]
        self.laser_id = id
        self.player_id = player_id
        self.direction = data[0]
        self.update_laser()

    def update_laser(self):
        laser_speed = 5
        if self.direction == "w":
            self.position[1] -= laser_speed
        elif self.direction == "s":
            self.position[1] += laser_speed
        elif self.direction == "a":
            self.position[0] -= laser_speed
        elif self.direction == "d":
            self.position[0] += laser_speed
        self.data = self.laser_id + self.player_id + self.colour + str(self.position[0]).zfill(4) + str(self.position[1]).zfill(4)

class Server(Player, Laser):
    def __init__(self, hostname):
        self.hostname = hostname
        self.players = dict()
        self.lasers = dict()
        self.server_state = "OFFLINE"

    def start_server(self):
        self.server_state = "INITIALISING"
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(False)
        # self.server.bind((socket.gethostbyname(socket.gethostname()), 6000))
        self.server.bind((self.hostname, 6000))
        self.server_state = "CONNECTED"
        self.server.listen(10)

    def process_data(self, data, client):
        player_id = self.sock_to_id(client)
        if data[0] == "l":
            if self.players[player_id].status:
                self.lasers[str([index for index in range(0, 999) if str(index).zfill(3) not in self.lasers][0]).zfill(3)] = Laser(data[1:], str([index for index in range(0, 999) if str(index).zfill(3) not in self.lasers][0]).zfill(3), self.players[player_id].properties["c"], player_id)
        elif data[0] == "o":
            try:
                del self.lasers[data[1:]]
            except KeyError:
                pass
        if data[0] == "k":
            self.players[player_id].reset_player()
            self.players[data[1:]].properties["k"] = str(int(self.players[data[1:]].properties["k"]) + 1)
            for player in self.players.values():
                if data[1:] in player.update:
                    player.update[data[1:]].append("k")
                else:
                    player.update[data[1:]] = ["k"]
        else:
            self.players[player_id].update_data(data)
            for player in self.players.values():
                if player != self.players[player_id]:
                    if player_id in player.update:
                        player.update[player_id].append(data[0])
                    else:
                        player.update[player_id] = [data[0]]

    def sock_to_id(self, client):
        for player in self.players:
            if self.players[player].connection is client:
                return player

    def add_player(self, client):
        client_id = [str(pot_id).zfill(2) for pot_id in range(0, 99) if not str(pot_id).zfill(2) in self.players][0]
        self.players[client_id] = Player(client_id, client)
        for player in self.players.values():
            if player != self.players[client_id]:
                player.update[client_id] = ["c", "n", "p", "h"]
                self.players[client_id].update[player.identity] = ["c", "n", "p", "h"]

    def remove_dead(self):
        try:
            for player_id in self.players:
                try:
                    self.players[player_id].connection.sendall("+u".encode())
                except socket.error:
                    self.remove_player(player_id)
        except RuntimeError:
            pass

    def remove_player(self, client_id):
        try:
            self.players[client_id].connection.sendall("+x".encode())
            self.players[client_id].connection.close()
        except socket.error:
            pass
        for client in self.players.values():
            client.update[client_id] = ["z"]
        del self.players[client_id]

    def stop_server(self):
        try:
            [self.remove_player(player_id) for player_id in self.players]
            self.server.close()
            self.server_state = "OFFLINE"
        except RuntimeError:
            self.stop_server()

    def check_lasers(self):
        try:
            for laser_id in self.lasers:
                if not 0 <= self.lasers[laser_id].position[0] <= 999 or not 0 <= self.lasers[laser_id].position[1] <= 999:
                    del self.lasers[laser_id]
        except RuntimeError:
            pass

    def serve_clients(self):
        self.check_lasers()
        [laser.update_laser() for laser in self.lasers.values()]
        inputs, outputs, exceptions = select.select([player.connection for player in self.players.values()] + [self.server], [player.connection for player in self.players.values()], [])
        for event in inputs:
            if event is self.server:
                connection, ip = self.server.accept()
                self.add_player(connection)
            else:
                try:
                    data = event.recv(1024).decode()
                    for item in data.split("+"):
                        item = item.strip()
                        if item == "":
                            pass
                        elif item == "x":
                            self.remove_player(self.sock_to_id(event))
                        else:
                            self.process_data(item, event)
                except socket.error:
                    self.remove_dead()

        for event in outputs:
            try:
                event.sendall("+u".encode())
                for laser in self.lasers.values():
                    event.sendall(("+v" + laser.data).encode())
                player_obj = self.players[self.sock_to_id(event)]
                for player_id in player_obj.update:
                    try:
                        for request in player_obj.update[player_id]:
                            if request == "z":
                                event.sendall(("+" + player_id + "z").encode())
                            if self.players[player_id].properties[request]:
                                event.sendall(("+" + player_id + request + self.players[player_id].properties[request]).encode())
                                del player_obj.update[player_id][player_obj.update[player_id].index(request)]
                    except KeyError:
                        self.remove_dead()
            except socket.error:
                self.remove_dead()

class Mainloop(Server):
    def __init__(self, hostname):
        self.hostname = hostname
        Server.__init__(self, hostname=self.hostname)
        pygame.init()

        self.window_size = (1000, 600)
        self.window = pygame.display.set_mode(self.window_size)

        stage = self.start_screen
        while True:
            stage = stage()

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
            elif anchor == "topleft":
                text_rect.topleft = (position[0] * self.window_size[0], position[1] * self.window_size[1])
            elif anchor == "topright":
                text_rect.topright = (position[0] * self.window_size[0], position[1] * self.window_size[1])
        else:
            if anchor == "center":
                text_rect.center = position
            elif anchor == "midleft":
                text_rect.midleft = position
            elif anchor == "midright":
                text_rect.midright = position
            elif anchor == "midbottom":
                text_rect.midbottom = position
            elif anchor == "topleft":
                text_rect.topleft = position
            elif anchor == "topright":
                anchor.topright = position
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

    def start_screen(self):
        gui_stage = "start"
        back_button = None
        while True:
            if gui_stage == "start":
                self.window.fill((0, 0, 0))
                start_button = self.create_textrect((0.1, 0.1), (0.8, 0.6), (0, 225, 0), True, "START SERVER", 50, (225, 225, 225), "center")
                credits_button = self.create_textrect((0.1, 0.7), (0.4, 0.2), (0, 0, 225), True, "CREDITS", 30, (225, 225, 225), "center")
                quit_button = self.create_textrect((0.5, 0.7), (0.4, 0.2), (225, 0, 0), True, "QUIT", 30, (225, 225, 225), "center")
            elif gui_stage == "credits":
                self.window.fill((0, 0, 0))
                self.create_textrect((0.1, 0.1), (0.8, 0.7), (225, 225, 225), True, "THIS GAME WAS DEVELOPED BY OLIVER KILLANE.", 30, (0, 0, 0), "center")
                back_button = self.create_textrect((0.1, 0.7), (0.8, 0.2), (225, 225, 0), True, "BACK", 30, (0, 0, 0), "center")
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONUP:
                    if gui_stage == "start":
                        if start_button.collidepoint(event.pos):
                            return self.server_control
                        elif quit_button.collidepoint(event.pos):
                            pygame.display.quit()
                            quit()
                        elif credits_button.collidepoint(event.pos):
                            gui_stage = "credits"
                    elif gui_stage == "credits":
                        if back_button.collidepoint(event.pos):
                            gui_stage = "start"
                elif event.type == pygame.VIDEORESIZE:
                    self.window_size = event.size
                    self.window = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
                elif event.type == pygame.QUIT:
                    pygame.display.quit()
                    quit()
            pygame.display.update()

    def server_control(self):
        scroll = 0
        kick_buttons = dict()
        thread.start_new_thread(self.start_server, ())
        self.window.fill((255,255,255))
        while True:
            if self.server_state == "INITIALISING":
                # self.create_textrect((0.1, 0.1), (0.8, 0.7), (0, 225, 0), True, "INITIALSING SERVER AT:" + socket.gethostbyname(socket.gethostname()), 30, (0, 0, 0), "center")
                self.create_textrect((0.1, 0.1), (0.8, 0.7), (0, 225, 0), True, "INITIALSING SERVER AT:" + self.hostname, 30, (0, 0, 0), "center")
            elif self.server_state == "CONNECTED":
                self.serve_clients()
                self.window.fill((225, 225, 225))
                # self.create_textrect((0, 0), (0.5, 0.1), (225, 0, 0), True, "SERVER IP:  " + socket.gethostbyname(socket.gethostname()), 20, (225, 225, 225), "center")
                self.create_textrect((0, 0), (0.5, 0.1), (225, 0, 0), True, "SERVER IP:  " + self.hostname, 20, (225, 225, 225), "center")
                self.create_textrect((0.5, 0), (0.5, 0.1), (225, 0, 0), True, "SERVER STATE:  " + self.server_state, 20, (225, 225, 225), "center")
                self.display_text("ID", 15, (0, 0, 0), (0, 0.1), "topleft", True)
                self.display_text("NAME", 15, (0, 0, 0), (0.2, 0.1), "topleft", True)
                self.display_text("COLOUR", 15, (0, 0, 0), (0.4, 0.1), "topleft", True)
                self.display_text("HEALTH", 15, (0, 0, 0), (0.6, 0.1), "topleft", True)
                self.display_text("KILLS", 15, (0, 0, 0), (0.7, 0.1), "topleft", True)
                self.display_text("KICK PLAYER", 15, (0, 0, 0), (0.8, 0.1), "topleft", True)
                back_button = self.create_textrect((0, 0.9), (1, 0.1), (225, 0, 0), True, "STOP SERVER", 20, (225, 225, 225), "center")
                kick_buttons.clear()

                players = list(self.players.values())
                for index in range(0, min(8, len(self.players))):
                    player_obj = players[scroll + index]
                    self.display_text(player_obj.identity, 15, (0,0,0), (0, 0.2 + scroll * 0.1), "topleft", True)
                    if player_obj.status:
                        self.display_text(player_obj.properties["n"], 15, (0,0,0) ,(0.2, 0.2 + index * 0.1),"topleft", True)
                        self.display_rect((0.4, 0.2 + scroll * 0.1),(0.1,0.1), player_obj.colour_formatted, True)
                        self.display_text(player_obj.properties["h"], 15, (0,0,0) ,(0.6, 0.2 + index * 0.1), "topleft", True)
                        self.display_text(str(player_obj.properties["k"]), 15, (0,0,0) ,(0.7, 0.2 + index * 0.1), "topleft", True)
                        kick_buttons[player_obj.identity] = self.create_textrect((0.8, 0.2 + index * 0.1), (0.2,0.1), (255,0,0), True, "KICK", 15, (255,255,255), "center")

            for event in pygame.event.get():
                if event.type == pygame.VIDEORESIZE:
                    self.window_size = event.size
                    self.window = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
                elif event.type == pygame.QUIT:
                    self.stop_server()
                    pygame.display.quit()
                    quit()
                elif self.server_state == "CONNECTED":
                    if event.type == pygame.KEYDOWN:
                        if event.scancode == 72:
                            if len(self.players) - 8 > scroll:
                                scroll += 1
                        elif event.scancode == 80:
                            if scroll > 0:
                                scroll -= 1
                    if event.type == pygame.MOUSEBUTTONUP:
                        for player_id in kick_buttons:
                            if kick_buttons[player_id].collidepoint(event.pos):
                                self.remove_player(player_id)
                        if back_button.collidepoint(event.pos):
                            self.stop_server()
                            return self.start_screen

            pygame.display.update()

hostname = input('Enter server hostname or IP address: ')
Mainloop(hostname=hostname)

#bug the player seems to get an object of themselves back, but with the position messed up.