import pygame
from pygame.locals import *
import random

## 继承pygame.sprite.Sprite类的update()函数、image和rect属性
## 鸟对象
class Bird(pygame.sprite.Sprite):
    
    def __init__(self, x, y):
        super().__init__()
        self.images = []
        self.index = 0 #images初始索引
        self.counter = 0 #计数器，用于更新动画效果
        self.cap = 10 #每次的加速度
        self.vel = 0 #速度
        self.flying = False
        self.failed = False
        self.clicked = False
        for num in range(1,4): #将小鸟图片循环导入images列表
            img = pygame.image.load(f"resources/bird{num}.png")
            self.images.append(img)
        self.image = self.images[self.index]
        self.rect = self.image.get_rect() #利用图片确定边框
        self.rect.center = [x,y] #x,y确定坐标
        self.wing = pygame.mixer.Sound("resources/wing.wav") #煽动翅膀音乐

    ## 手动飞
    def handle_input(self):
        if pygame.mouse.get_pressed()[0] == 1 and not self.clicked: #防止一直持续按住左键
            self.wing.play() 
            self.clicked = True #修改点击bool值
            self.vel = -1 * self.cap #小鸟向上飞
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

    ## 图像变化
    def animation(self):
        flap_cooldown = 5 #图片冷却时间
        self.counter += 1
        if self.counter > flap_cooldown: #超过5帧后图片进行变化
            self.index = (self.index + 1) % 3
            self.image = self.images[self.index]
            self.counter = 0
        self.image = pygame.transform.rotate(self.images[self.index], self.vel * -2) #逆时针旋转self.vel*-2的角度

    ## 判断小鸟是否着地
    def touch_ground(self):
        return self.rect.bottom >= Game.ground_y
    
    ## 每帧更新小鸟位置 
    def update(self): 
        if self.flying :
            self.vel += 0.5 #重力作用
            if self.vel > 8:
                self.vel = 8
            if not self.touch_ground(): #如果还没着地
                self.rect.y += int(self.vel) #更新纵坐标
        if not self.failed : #正常操作
            self.handle_input()
            self.animation()
        else:
            self.image = pygame.transform.rotate(self.images[self.index], -90) #失败动画
    
## 钢管对象
class Pipe(pygame.sprite.Sprite):
    scroll_speed = 4 #钢管本身速度
    pipe_gap = 180 #上下钢管缺口大小
    
    def __init__(self, x, y, is_top):
        super().__init__()
        self.passed = False
        self.is_top = is_top #上钢管or下钢管
        self.image = pygame.image.load("resources/pipe.png")
        self.rect = self.image.get_rect() 

        if is_top : # 翻转图片并确定钢管位置
            self.image = pygame.transform.flip(self.image,False,True)
            self.rect.bottomleft = [x, y - Pipe.pipe_gap // 2]
        else :
            self.rect.topleft = [x, y + Pipe.pipe_gap // 2] 
    
    def update(self):
        self.rect.x -= Pipe.scroll_speed
        if self.rect.right < 0:
            self.kill()

## 重置按钮对象
class Button:

    def __init__(self, x, y):
        self.image = pygame.image.load("resources/restart.png")
        self.rect = self.image.get_rect(centerx=x, centery=y)

    ## 判断是否按到按钮
    def pressed(self,event):
        pressed = False
        if event.type == MOUSEBUTTONDOWN: # 如果事件是鼠标点击
            pos = pygame.mouse.get_pos() # 获取鼠标位置
            if self.rect.collidepoint(pos): #判断是否在按钮边框内
                pressed = True # 按到了
        return pressed
    
    ## draw函数把按钮按照边框位置画在屏幕上
    def draw(self,surface):
        surface.blit(self.image, self.rect)

## 游戏主体对象
class Game():
    ground_y = 650

    ##
    def __init__(self,Width = 600, Height = 800):
        pygame.init() # pygame初始化
        self.Win_width, self.Win_height = (Width,Height) # 定义游戏窗口大小
        self.surface = pygame.display.set_mode((self.Win_width, self.Win_height)) # 定义窗口
        self.ground_x = 0
        self.score = 0
        self.pipe_counter = 0 # 钢管计数器
        self.observed = dict()
        self.Clock = pygame.time.Clock() # 初始化pygame内置时钟
        self.fps = 60
        self.font = pygame.font.SysFont('Bauhaus 93', 60)
        self.images = self.loadImages()
        self.sounds = self.loadSounds()
        self.pipe_group = pygame.sprite.Group()
        self.bird_group = pygame.sprite.Group()
        self.flappy = Bird(100, self.ground_y // 2)
        self.bird_group.add(self.flappy)
        self.new_pipes(time=0)
        self.button = Button(self.Win_width//2,self.Win_height//2)
        pygame.display.set_caption("Flappy Bird") # 游戏标题
        pygame.mixer.music.load("resources/BGMUSIC.mp3")
        pygame.mixer.music.play(-1)

    ## 加载游戏图片
    def loadImages(self):
        background = pygame.image.load("resources/bg.png")
        ground = pygame.image.load("resources/ground.png")
        return {'bg':background, 'ground':ground}

    ## 加载游戏声音 
    def loadSounds(self):
        hit = pygame.mixer.Sound("resources/hit.wav")
        point = pygame.mixer.Sound("resources/point.wav")
        return {'hit':hit, 'point':point} 

    ## 游戏重置        
    def reset_game(self):
        self.pipe_group.empty()
        self.new_pipes(time=0)
        self.flappy.rect.x = 100
        self.flappy.rect.y = self.ground_y // 2
        self.score = 0
        self.observed = dict()
        pygame.mixer.music.play(-1)

    ## 开始起飞条件
    def start_flying(self,event):
        if (event.type == pygame.MOUSEBUTTONDOWN
            and not self.flappy.flying
            and not self.flappy.failed):
            self.flappy.flying = True

    ## 游戏重置条件
    def game_restart(self,event):
        if (self.flappy.failed and
            self.button.pressed(event)):
                self.flappy.failed = False
                self.reset_game()

    ## 碰撞检测
    def handle_collision(self):
        if (pygame.sprite.groupcollide(self.bird_group, self.pipe_group, False, False) # 碰撞检测函数
            or self.flappy.rect.top < 0
            or self.flappy.rect.bottom >= Game.ground_y):
            self.flappy.failed = True
            self.sounds['hit'].play()
            pygame.mixer.music.stop()

    ## 移动地面
    def ground_update(self):
        self.ground_x -=Pipe.scroll_speed
        if abs(self.ground_x) > 35:
            self.ground_x = 0
    
    ## 产生新的钢管
    def new_pipes(self,time = 90):
        self.pipe_counter += 1
        if self.pipe_counter > time:
            pipe_height = random.randint(-150, 150)
            top_pipe = Pipe(self.Win_width, self.ground_y // 2 + pipe_height, True)
            btm_pipe = Pipe(self.Win_width, self.ground_y // 2 + pipe_height, False)
            self.pipe_group.add(top_pipe)
            self.pipe_group.add(btm_pipe)
            self.pipe_counter = 0

    ## 观测钢管在小鸟的相对位置
    def get_pipe_dist(self):
        pipe_2 = [pipe for pipe in self.pipe_group.sprites() if pipe.passed == False][:2]
        for pipe in pipe_2:
            if pipe.is_top:
                self.observed['pipe_dist_right'] = pipe.rect.right
                self.observed['pipe_dist_top'] = pipe.rect.bottom
            else:
                self.observed['pipe_dist_bottom'] = pipe.rect.top

    ## 判断小鸟成功穿越钢管
    def check_pipe_pass(self):
        if self.flappy.rect.left >= self.observed['pipe_dist_right']:
            self.score += 1
            self.pipe_group.sprites()[0].passed = True
            self.pipe_group.sprites()[1].passed = True
            self.sounds['point'].play()
    
    ## 封装所有钢管函数
    def pipe_update(self):
        self.new_pipes()
        self.pipe_group.update()
        if len(self.pipe_group) > 0:
            self.get_pipe_dist()
            self.check_pipe_pass()

    ## 显示“score”文字
    def draw_text(self,text,color,x,y):
        img = self.font.render(text, True, color)
        self.surface.blit(img,(x,y))

    ## 封装所有绘制函数
    def draw(self):
        self.surface.blit(self.images['bg'],(0,0))
        self.pipe_group.draw(self.surface)
        self.bird_group.draw(self.surface)
        self.surface.blit(self.images['ground'],(self.ground_x,self.ground_y))
        self.draw_text(f'score:{self.score}',(255,255,255),20,20)
    
    # 检测失败
    def check_failed(self):
        if self.flappy.failed:
            pygame.mixer.music.stop()
            if self.flappy.touch_ground():
                self.button.draw(self.surface)
                self.flappy.flying = False

    ## 游戏时每一帧的流程（所有操作的集合）
    def play_step(self):
        game_over = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            self.start_flying(event)
            self.game_restart(event)
        self.bird_group.update()
        if not self.flappy.failed and self.flappy.flying:
            self.handle_collision()
            self.pipe_update()
            self.ground_update()
        self.draw()
        self.check_failed()
        pygame.display.update()
        self.Clock.tick(self.fps)
        return game_over, self.score
    
if __name__ == '__main__':
    game = Game()
    while True:
        game_over, score = game.play_step()
        if game_over == True:
            break

    print('Final Score :', score)
    pygame.quit()