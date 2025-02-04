
from pyglet.window import key
from cocos.sprite import Sprite
from cocos.scene import Scene
from cocos.layer import ScrollableLayer, ScrollingManager
from cocos.tiles import load_tmx
from cocos.mapcolliders_plus import TmxObjectMapCollider, make_collision_handler
from cocos.collision_model import AARectShape, CollisionManagerBruteForce
from cocos.particle_systems import Explosion, Smoke, Sun
from cocos.particle import Color
from cocos.actions import Action, Delay, CallFunc, MoveBy, Repeat
from cocos.director import director
from cocos.euclid import Vector2
from random import randint

class MiGuerrero(Sprite):
    en_suelo = True
    VEL_MOV = 200
    VEL_SALTO = 500
    GRAVEDAD = -800

    def __init__(self, image):
        super().__init__(image)
        self.velocidad = (0,0)
        self.direccion = 'derecha'
        self.hay_disparo = False

    def update(self, dt):
        vx, vy = self.velocidad
        vx = (man_tec[key.RIGHT] - man_tec[key.LEFT]) * self.VEL_MOV
        vy += self.GRAVEDAD * dt
        if self.en_suelo and man_tec[key.SPACE]:
            vy = self.VEL_SALTO
        if man_tec[key.LEFT]:
            self.direccion = 'izquierda'
        if man_tec[key.RIGHT]:
            self.direccion = 'derecha'
        if man_tec[key.ENTER] and not self.hay_disparo:
            self.hay_disparo = True
            if self.direccion == 'derecha':
                self.disparo = MiCuchillo('mi_cuchillo_1.png', 'd',
                                          self.position[0], self.position[1])
                self.parent.add(self.disparo)
            elif self.direccion == 'izquierda':
                self.disparo = MiCuchillo('mi_cuchillo_2.png', 'i',
                                          self.position[0], self.position[1])
                self.parent.add(self.disparo)
            self.do(Delay(0.2)+ CallFunc(self.nuevo_disparo))

        dx = vx * dt
        dy = vy * dt

        antes = self.get_rect()
        despues = antes.copy()
        despues.x += dx
        despues.y += dy

        self.velocidad = self.man_col(antes, despues, vx, vy)
        self.en_suelo = (despues.y == antes.y)
        self.position = despues.center

        manejador_scroll.set_focus(despues.x, 384)

    def nuevo_disparo(self):
        self.hay_disparo = False


class MiCuchillo(Sprite):
    def __init__(self, image, dir, x, y):
        super().__init__(image)
        self.position = (x,y)
        self.direccion = dir
        self.cshape = AARectShape(self.position, self.width/5, self.height/5)

    def update(self, dt):
        coor_cuchillo = manejador_scroll.world_to_screen(self.x, self.y)[0]
        if coor_cuchillo> 1280 or coor_cuchillo < 0:
            self.kill()
        if self.direccion == 'd':
            self.position += Vector2(20,0)
        elif self.direccion == 'i':
            self.position -= Vector2(20,0)
        self.cshape.center = Vector2(self.position[0], self.position[1])


class MiObjeto(Sprite):
    def __init__(self, image):
        super().__init__(image)


class MiEnemigo(Sprite):
    def __init__(self, image):
        super().__init__(image)
        self.cshape = AARectShape(self.position, self.width/2, self.height/2)

    def update(self, dt):
        self.cshape.center = Vector2(self.position[0], self.position[1])


class MiDragon(MiEnemigo):
    def __init__(self, image):
        super().__init__(image)

    def update(self, dt):
        if randint(1,1000) > 980:
            llama = MiFuegoDragon('mi_fuego_dragon.png', self.x - 50, self.y + 40)
            self.parent.add(llama)
        self.cshape.center = Vector2(self.position[0], self.position[1])


class MiFuegoDragon(Sprite):
    def __init__(self, image, x, y):
        super().__init__(image)
        self.position = (x,y)
        self.cshape = AARectShape(self.position, self.width/5, self.height/5)

    def update(self, dt):
        self.position += Vector2(-10,0)
        if self.x < 0:
            self.kill()
        self.cshape.center = Vector2(self.position[0], self.position[1])


class MiExplosion1(Explosion):
    def __init__(self, pos):
        super().__init__()
        self.position = pos
        self.auto_remove_on_finish = True
        self.total_particles = 700
        self.emission_rate = 700
        self.size = 2
        self.life = 1
        self.scale = 2
        self.start_color = Color(255,255,0,255)

    def update(self, dt):
        pass


class MiExplosion2(Explosion):
    def __init__(self, pos):
        super().__init__()
        self.position = pos
        self.auto_remove_on_finish = True
        self.total_particles = 700
        self.emission_rate = 1200
        self.size = 10
        self.life = 3
        self.start_color = Color(0,255,100,255)

    def update(self, dt):
        pass


class Control(Action):
    def start(self):
        self.mc = CollisionManagerBruteForce()

    def step(self, dt):
        self.mc.clear()
        for objeto in self.target.parent.children:
            if isinstance(objeto[1], (MiCuchillo, MiFuegoDragon, MiDragon)):
                self.mc.add(objeto[1])

        for elemento in list(self.mc.iter_all_collisions()):
            a = set([type(elemento[0]), type(elemento[1])])
            b = set([MiCuchillo, MiFuegoDragon])
            c = set([MiCuchillo, MiDragon])
            if  a == b:
                self.target.parent.add(MiExplosion1(elemento[0].position))
                if (0, elemento[0]) in self.target.parent.children:
                    elemento[0].kill()
                if (0, elemento[1]) in self.target.parent.children:
                    elemento[1].kill()
            if a == c:
                self.target.parent.add(MiExplosion2(elemento[0].position))
                if (0, elemento[0]) in self.target.parent.children:
                    elemento[0].kill()
                if (0, elemento[1]) in self.target.parent.children:
                    elemento[1].kill()

        for objeto in self.target.parent.children:
            if not isinstance(objeto[1], (MiObjeto, Smoke, Sun)):
                objeto[1].update(dt)


class Escena(Scene):
    def __init__(self):
        global  manejador_scroll
        super().__init__()
        mi_mapa1 = load_tmx('mapa_plataformas_2.tmx')['objetos']
        mi_mapa1_1 = load_tmx('mapa_plataformas_2.tmx')['capa0']

        dragon = MiDragon('mi_dragon.png')
        ref_dra = mi_mapa1.find_cells(p_dragon=True)[0]
        dragon.position = (ref_dra.x, ref_dra.y)
        mi_mapa1.objects.remove(ref_dra)
        dragon.do(Repeat(MoveBy((0, 300), 1) + MoveBy((0, -300), 1)))

        araña1 = MiEnemigo('mi_araña_2.png')
        ref_ara = mi_mapa1.find_cells(p_arana=True)[0]
        araña1.position = (ref_ara.x, ref_ara.y +10)
        mi_mapa1.objects.remove(ref_ara)
        araña1.do(Repeat(MoveBy((450, 0), 3) + MoveBy((-450, 0), 3)))

        araña2 = MiEnemigo('mi_araña_2.png')
        ref_ara = mi_mapa1.find_cells(p_arana_2=True)[0]
        araña2.position = (ref_ara.x, ref_ara.y +10)
        mi_mapa1.objects.remove(ref_ara)
        araña2.do(Repeat(MoveBy((-450, 0), 3) + MoveBy((450, 0), 3)))

        pila = MiObjeto('mi_pila.png')
        ref_pila = mi_mapa1.find_cells(p_pila=True)[0]
        pila.position = ref_pila.center

        humo_pila = Smoke()
        humo_pila.position = pila.position + Vector2(0, 40)

        sol = Sun()
        ref_sol = mi_mapa1.find_cells(p_sol=True)[0]
        sol.position = Vector2(ref_sol.x, ref_sol.y)
        mi_mapa1.objects.remove(ref_sol)

        personaje = MiGuerrero('mi_guerrero_2.png')
        ref_per = mi_mapa1.find_cells(p_personaje=True)[0]
        personaje.position = (ref_per.x, ref_per.y)
        mi_mapa1.objects.remove(ref_per)
        personaje.do(Control())

        capa_fondo = ScrollableLayer()
        for i in range(4):
            a = Sprite('mi_fondo.png')
            a.position = (640 + 1280*i, 440)
            capa_fondo.add(a)

        capa_personaje = ScrollableLayer()
        capa_personaje.add(dragon)
        capa_personaje.add(araña1)
        capa_personaje.add(araña2)
        capa_personaje.add(pila)
        capa_personaje.add(humo_pila)
        capa_personaje.add(sol)
        capa_personaje.add(personaje)

        manejador_scroll = ScrollingManager()
        manejador_scroll.add(mi_mapa1, z=0)
        manejador_scroll.add(capa_fondo, z=1)
        manejador_scroll.add(mi_mapa1_1, z=2)
        manejador_scroll.add(capa_personaje, z=3)

        mapa_colision = TmxObjectMapCollider()
        mapa_colision.on_bump_handler = mapa_colision.on_bump_slide
        personaje.man_col = make_collision_handler(mapa_colision, mi_mapa1)

        self.add(manejador_scroll)
        director.run(self)


if __name__ == '__main__':
    ventana = director.init(width=1280, height=768, caption='Guerrero vs Dragón')
    ventana.set_location(300,200)
    man_tec = key.KeyStateHandler()
    director.window.push_handlers(man_tec)
    Escena()
