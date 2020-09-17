import pygame as p, sys, os
from pathlib import Path
from random import randint
from pygame.sprite import Sprite as spt, Group
from pygame.rect import *
from pygame.surface import *
from pygame.colordict import THECOLORS as colors

# Global variables
script_dir = os.path.dirname(__file__)
media_folder = Path(script_dir + "/Media/")

screenSize = width, height = 800, 600
sectors = 4
baseSize = 128, 512
soldierSizeW = 32 #wide
bulletSize = 24, 12

# Spliiting the screen for routes accorfing to the sectors variable
# Defining the unit sizes according to the screen routes sizes
sect = height // sectors
sections = [ sect // 2 + i * sect for i in range(sectors) ]
sizes = [ sect // 2 + (sect // 2 - 5 * i) for i in range(5, 0, -1) ]

# Create sprite groups, for units and bullets for each side
# Allow easy managing of sprites
# Streamlines the game loop
group_left_side = Group()
group_right_side = Group()
group_bullet_left = Group()
group_bullet_right = Group()

# Create a tupel containing all groups
groups = (
        group_left_side,
        group_right_side,
        group_bullet_left,
        group_bullet_right,
    )

# Custom raise error class
class Sprite_Sub_Error(Exception):
    def __init__(self, typeName):
        self.expression = "Error"
        self.message = '"{}" not subclass of sprite'.format(typeName)
        super().__init__(self.message)

# Dynamically change / set attribute
def set_rect(selfRect, attribute, rect):
    setattr(selfRect, attribute, rect)

# Wraper functions to dynamically create unit not depended on class or args, split by side
# Add sprites to groups depends on sides
def left_side(scr, spriteType, imagePathStr, *args, **kwargs):
    if spriteType not in spriteSubsNameStr:
        raise Sprite_Sub_Error(spriteType)
    sp = eval(spriteType)(imagePathStr, scr, 'l', *args, **kwargs)
    set_rect(sp.getRect(), 'left', scr.get_rect().left)
    group_left_side.add(sp)
    return sp

def right_side(scr, spriteType, imagePathStr, *args, **kwargs):
    if spriteType not in spriteSubsNameStr:
        raise Sprite_Sub_Error(spriteType)
    sp = eval(spriteType)(imagePathStr, scr, 'r', *args, **kwargs)
    set_rect(sp.getRect(), 'right', scr.get_rect().right)
    group_right_side.add(sp)
    return sp

# unit types
units = [
        # (class, image_path, life, size, dmg = none)
        ['Soldier', str(media_folder / "soldier.jpg"), 5, (soldierSizeW, sizes[0]), {'dmg': 2}],
        ['Ranger', str(media_folder / "archer.jpg"), 7, (soldierSizeW, sizes[1])],
        ['Soldier', str(media_folder / "poll.jpg"), 9, (soldierSizeW, sizes[2]), {'dmg': 3}],
        ['Soldier', str(media_folder / "knight.jpg"), 11, (soldierSizeW, sizes[3]), {'dmg': 4}],
    ]

# unit prices
price = {
        # Unit : Price
        0: 3,
        1: 4,
        2: 5,
        3: 7
    }

# Crate unit wrapper using the units list and prices dict, packing and unpacking using *args and **kwargs
def create(side, unit, section, **kwargs):
    unit = units[unit]
    if type(unit[-1]) == dict:
        unit = unit[:]
        kwargs = unit.pop()

    if side == 'l':
        left_side(screen, *unit, section, **kwargs)
    elif side == 'r':
        right_side(screen, *unit, section, **kwargs)

# Base sprite class inheriting for pygame sprite class
class Sprite(spt):
    def __init__(self, imagePathStr, side, life, dmg = None):
        super().__init__()
        if imagePathStr:
            self.__image__ = p.image.load(imagePathStr).convert_alpha()
        self.__life__ = self.__maxlife__ = life
        self.__dmg__ = dmg
        self.__side__ = side
        if side == 'l':
            self.__opposite__ = group_right_side
        else:
            self.__opposite__ = group_left_side

    def lifebar(self):
        bar = Surface((self.rect.width, self.rect.height * 0.02)).convert()
        bar.fill(colors['red'])
        screen.blit(bar, (self.rect.left, self.rect.top - 5))
        bar.fill(colors['green'])
        screen.blit(bar, (self.rect.left, self.rect.top - 5), (0, 0, self.rect.width / self.__maxlife__ * self.__life__, self.rect.height * 0.02))

    # Update method is a methods the group.update method use from each instance in a group
    def update(self):
        if self.__life__ < 1:
            spt.kill(self)

    def getImage(self):
        return self.__image__

    # def getDmg(self):
    #     return self.dmg

    def getLife(self):
        return self.__life__

    def setLife(self, life):
        self.__life__ = life

    def getSide(self):
        return self.__side__

    def getRect(self):
        return self.rect

# Not base class, but class for army bases, used once on each side
# Inherits from Sprite class
# The base class life is the ending condition
class Base(Sprite):
    def __init__(self, imagePathStr, scr, sde, life):
        super().__init__(imagePathStr, sde, life)
        self.image = p.transform.scale(self.__image__, baseSize)
        self.rect = self.image.get_rect(center = scr.get_rect().center)

# Melee class, soldier, inherits from Sprite class
class Soldier(Sprite):
    #  Attacking speed
    __fireRate__ = __rate__ = 30
    def __init__(self, imagePathStr, scr, side, life, size, section, dmg = None):
        super().__init__(imagePathStr, side, life, dmg)
        self.image = p.transform.scale(self.__image__, size)
        self.rect = self.image.get_rect()
        self.rect.center = scr.get_rect().center[0], sections[section]

    def update(self):
        super().update()
        # Create a list of opposite group sprites collided with self
        enemies = p.sprite.spritecollide(self, self.__opposite__, False)
        if enemies:
            # checks fire rate before attack
            if self.__fireRate__ == 0:
                for enemy in enemies:
                    # inflict dmg on enemy unit
                    enemy.setLife(enemy.getLife() - self.__dmg__)
                # Restart the fire rate counter
                self.__fireRate__ = self.__rate__ + 1
        # Moves the sprite if it hasent encountered an enemy
        else:
            switcher = {
                'l': 2,
                'r': -2
            }
            self.rect.move_ip(switcher.get(self.__side__), 0)
        # decrement the fire rate
        if self.__fireRate__ != 0:
            self.__fireRate__ -= 1

# Ranged unit which shoot and stay at distance
# Inherit from Sprite class
class Ranger(Sprite):
    #  Attacking speed
    __rate__ = __fireRate__ = 50
    def __init__(self, imagePathStr, scr, side, life, size, section):
        super().__init__(imagePathStr, side, life)
        self.image = p.transform.scale(self.__image__, size)
        self.rect = self.image.get_rect()
        self.rect.center = scr.get_rect().center[0], sections[section]
        # Costume class used to define distance
        self.dist = Distance(self.rect)

    def update(self):
        super().update()
        # Create a list of opposite group sprites collided with self or with distance / range rect
        enemies = p.sprite.spritecollide(self, self.__opposite__, False)
        inRange = p.sprite.spritecollideany(self.dist, self.__opposite__)
        # Update the 'keep distance' rect according to unit movement and side
        if self.__side__ == 'l':
            self.dist.get_rect().left = self.rect.right
        else:
            self.dist.get_rect().right = self.rect.left
        # Once the fire rate allow it, create a new bullet class and adds to same side bullet group to manage it
        if self.__fireRate__ == 0:
            bullet = Bullet(str(media_folder / "bullet.jpg"), self.__side__, rect_center=self.rect.center)
            if self.__side__ == 'l':
                group_bullet_left.add(bullet)
            else:
                group_bullet_right.add(bullet)
            del bullet
            self.__fireRate__ = self.__rate__
        else:
            self.__fireRate__ -= 1
        # Moves unit if no enemies in range
        if not enemies and not inRange:
            switcher = {
                'l': 2,
                'r': -2
            }
            self.rect.move_ip(switcher.get(self.__side__), 0)

# Costume class to define distance for the ranged class
# Not inheriting from the Sprite class but from Pygame Sprite class
class Distance(spt):
    __distance__ = 120
    def __init__(self, ranger_rect):
        super().__init__()
        # Create rect object
        self.rect = Rect(ranger_rect)
        self.rect.width = self.__distance__

    def get_rect(self):
        return self.rect

# Bullet class
# Inherit from Sprite class
# Only able to hit one unit and then kill itself
class Bullet(Sprite):
    __dmg__ = 1
    def __init__(self, imagePathStr, side, rect_center):
        super().__init__(imagePathStr, side, None, self.__dmg__)
        self.image = p.transform.scale(self.__image__, bulletSize)
        self.rect = self.image.get_rect(center = rect_center)

    def update(self):
        enemies = p.sprite.spritecollide(self, self.__opposite__, False)
        if not enemies or all (type(enemy) == Bullet for enemy in enemies):
            switcher = {
                'l': 4,
                'r': -4
            }
            self.rect.move_ip(switcher.get(self.getSide()), 0)
        else:
            enemy = p.sprite.spritecollideany(self, self.__opposite__)
            enemy.setLife(enemy.getLife() - self.__dmg__)
            spt.kill(self)

# Create Sprite class subclasses list
spriteSubsNameStr = [cls.__name__ for cls in Sprite.__subclasses__()]

# Create a welcome screen
def start_screen():
    screen.fill(black)
    screen.blit(nlabel, nlabel_rect)
    p.display.flip()
    while True:
        for event in p.event.get():
            if event.type == p.MOUSEBUTTONDOWN:
                return

# The main game
def main():
    p.mixer.music.play(-1)

    # Create the basses
    baseLeft = left_side(screen, 'Base', str(media_folder / "watchtower.jpg"), 30)
    baseRight = right_side(screen, 'Base', str(media_folder / "watchtower.jpg"), 30)

    # Create coin variables, and unit variables
    player = computer = p_unit = p_sect = temp = 0
    # Create User event which add coin every x time
    ADD_COIN, t = p.USEREVENT+1, 1000
    p.time.set_timer(ADD_COIN, t)
    # Call the welcome screen function
    start_screen()

    # Starts the game loop
    while True:
        # text surfaces to render on screen, the player and computer money
        p_money = font.render('Player money = {}'.format(player), True, colors['gold'])
        c_money = font.render('Computer money = {}'.format(computer), True, colors['gold'])
        c_text_rect = c_money.get_rect(right = screen.get_rect().right - 10, top = 10)

        # Draw on screen
        screen.fill(black)
        # Quick group methods to draw all sprite in a group on surface
        for gp in groups:
            gp.draw(screen)
        # Blit the money variables / text objects on screen
        screen.blit(p_money, (10,10))
        screen.blit(c_money, c_text_rect)
        # Draw the life bar of each unit
        for entity in group_left_side:
            entity.lifebar()
        for entity in group_right_side:
            entity.lifebar()
        p.display.flip()

        # Check win / lose conditions
        if not (baseLeft.alive() and baseRight.alive()):
            # Stop music
            p.mixer.music.stop()
            if not baseLeft.alive():
                title_text = title.render('GAME OVER !', True, colors['red'])
            else:
                title_text = title.render('YOU WIN !', True, colors['red'])
            t_text_rect = title_text.get_rect(center = screen.get_rect().center)
            screen.blit(title_text, t_text_rect)
            p.display.update(t_text_rect)
            while True:
                for event in p.event.get():
                    if event.type == p.MOUSEBUTTONDOWN:
                        # Restart game and quit current proccess
                        baseLeft = baseRight = None
                        for gp in groups:
                            gp.empty()
                        main()
                        #os.system("python shlomo.py")
                        #quit()

        # Userevents, timer, quit, keys, and spwaning user units
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            if event.type == p.KEYDOWN:
                if event.key == p.K_1: temp = 1
                elif event.key == p.K_2: temp = 2
                elif event.key == p.K_3: temp = 3
                elif event.key == p.K_4: temp = 4
                if temp:
                    if not p_unit:
                        p_unit = temp
                    elif 0 < p_unit < 5:
                        p_sect = temp
                    temp = 0
                if 0 < p_unit < 5 and 0 < p_sect < 5:
                    if player >= price[p_unit - 1]:
                        # create(side, index-unit, index-screen)
                        create('l', p_unit - 1, p_sect - 1)
                        player -= price[p_unit - 1]
                    p_unit = p_sect = 0
            # add coin to each side every x seconds
            if event.type == ADD_COIN:
                player += 1
                computer += 1

        # Computer turn generates random numbers
        c_unit = randint(0, 3)
        c_sect = randint(0, 3)
        if computer >= price[c_unit]:
            # create(side, index-unit, index-screen)
            create('r', c_unit, c_sect)
            computer -= price[c_unit]

        # Update - groups method that call instance update method
        for gp in groups:
            gp.update()

        FPS.tick(60)

# Game init
p.init()
black = 0, 0, 0
FPS = p.time.Clock()
p.display.set_caption("Shlomo game")
screen = p.display.set_mode(screenSize)

# font objects
font = p.font.SysFont(None, 24, italic=True)
title = p.font.SysFont(None, 96, True)
myfont = p.font.SysFont("Britannic Bold", 75)
nlabel = myfont.render("Welcome", 1, colors['yellowgreen'])
nlabel_rect = nlabel.get_rect(center=screen.get_rect().center)

# Load and play music
p.mixer.music.load(str(media_folder / "Bog-Creatures-On-the-Move.mp3"))

# Run the game
main()