import pygame
import os
import random
import neat
import neat.config
import time

aiJogando = True
geracao = 0
max_pontos = 0

TELA_LARGURA = 500
TELA_ALTURA = 800

# Imagens — substitua pelos seus arquivos em ./imgs/
IMAGEM_BACKGROUND = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bg.png')))
IMAGEM_CHAO = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'base.png')))
IMAGEM_CUBO = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'cubo.png')))
IMAGEM_PLATAFORMA = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'plataforma.png')))

# Configurações do cubo (usar retângulo simples, sem imagem)
CUBO_LARGURA = 50
CUBO_ALTURA = 50
CUBO_X = 100  # posição fixa X do jogador (será sobrescrito para centralizar sobre a plataforma inicial)

pygame.font.init()
FONTE_PONTOS = pygame.font.SysFont('arial', 36)


class Cubo:
    GRAVIDADE = 1.0
    FORCA_PULO = -16
    MAX_VELOCIDADE = 20

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel = 0
        self.largura = CUBO_LARGURA
        self.altura = CUBO_ALTURA
        self.retangulo = pygame.Rect(self.x, self.y, self.largura, self.altura)
        self.em_sobre = False  # indica se o cubo está sobre uma plataforma

        # pré-escalar imagem do cubo ao tamanho do retângulo
        self.img = pygame.transform.scale(IMAGEM_CUBO, (self.largura, self.altura))

    def pular(self):
        if self.em_sobre:
            self.vel = self.FORCA_PULO
            self.em_sobre = False

    def mover(self):
        self.vel += self.GRAVIDADE
        if self.vel > self.MAX_VELOCIDADE:
            self.vel = self.MAX_VELOCIDADE
        self.y += self.vel
        self.retangulo.topleft = (round(self.x), round(self.y))

    def desenhar(self, tela):
        tela.blit(self.img, (round(self.x), round(self.y)))
        # opção: desenhar retângulo de debug (colisão)
        # pygame.draw.rect(tela, (255,0,0), self.retangulo, 1)

    def colidir_com(self, plataforma):
        return self.retangulo.colliderect(plataforma.ret)


class Plataforma:
    VELOCIDADE = 5

    def __init__(self, x, y, largura=120, altura=20):
        self.x = x
        self.y = y
        self.largura = largura
        self.altura = altura
        self.ret = pygame.Rect(round(self.x), self.y, self.largura, self.altura)
        self.passou = False  # não usado para score neste layout

        # pré-escalar imagem da plataforma ao tamanho desejado
        self.img = pygame.transform.scale(IMAGEM_PLATAFORMA, (self.largura, self.altura))

    def mover(self):
        self.x -= self.VELOCIDADE
        self.ret.topleft = (round(self.x), self.y)

    def desenhar(self, tela):
        tela.blit(self.img, (round(self.x), self.y))
        # opção: desenhar retângulo de debug (colisão)
        # pygame.draw.rect(tela, (0,0,0), self.ret, 1)


class Chao:
    VELOCIDADE = 5
    LARGURA = IMAGEM_CHAO.get_width()
    IMAGEM = IMAGEM_CHAO

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.LARGURA

    def mover(self):
        self.x1 -= self.VELOCIDADE
        self.x2 -= self.VELOCIDADE

        if self.x1 + self.LARGURA < 0:
            self.x1 = self.x2 + self.LARGURA
        if self.x2 + self.LARGURA < 0:
            self.x2 = self.x1 + self.LARGURA

    def desenhar(self, tela):
        tela.blit(self.IMAGEM, (self.x1, self.y))
        tela.blit(self.IMAGEM, (self.x2, self.y))


class Fundo:
    VELOCIDADE = 2
    LARGURA = IMAGEM_BACKGROUND.get_width()
    ALTURA = IMAGEM_BACKGROUND.get_height()

    def __init__(self):
        self.x1 = 0
        self.x2 = self.LARGURA

    def mover(self):
        self.x1 -= self.VELOCIDADE
        self.x2 -= self.VELOCIDADE

        if self.x1 + self.LARGURA < 0:
            self.x1 = self.x2 + self.LARGURA
        if self.x2 + self.LARGURA < 0:
            self.x2 = self.x1 + self.LARGURA

    def desenhar(self, tela):
        tela.blit(IMAGEM_BACKGROUND, (self.x1, 0))
        tela.blit(IMAGEM_BACKGROUND, (self.x2, 0))


def desenhar_tela(tela, cubos, plataformas, chao, fundo, pontos, tempo_inicio, pontos_max=0):
    fundo.desenhar(tela)
    for cubo in cubos:
        cubo.desenhar(tela)
    for p in plataformas:
        p.desenhar(tela)

    pontos_texto = FONTE_PONTOS.render(f"Pontuação: {pontos}", 1, (255, 255, 255))
    pontos_maior_texto = FONTE_PONTOS.render(f"Máximo: {pontos_max}", 1, (255, 255, 255))
    # variáveis para calcular as posições dos textos de pontos
    x_pontos = TELA_LARGURA - 10 - pontos_texto.get_width()
    y_pontos = 10
    tela.blit(pontos_texto, (x_pontos, y_pontos))
    espaco = 6
    y_pontos_maior = y_pontos + pontos_texto.get_height() + espaco
    tela.blit(pontos_maior_texto, (TELA_LARGURA - 10 - pontos_maior_texto.get_width(), y_pontos_maior))

    if aiJogando:
        gen_text = FONTE_PONTOS.render(f"Geração: {geracao}", 1, (255, 255, 255))
        tela.blit(gen_text, (10, 10))

    chao.desenhar(tela)
    pygame.display.update()


def criar_plataformas_iniciais():
    plataformas = []
    x = 200  # aproximar plataformas iniciais
    for i in range(4):
        plataformas.append(Plataforma(x=x, y=random.randrange(450, 600), largura=random.randrange(100, 160)))
        x += random.randrange(200, 300)
    return plataformas


def posicionar_cubos_sobre_plataforma_inicial(cubos, plataformas):
    if not plataformas:
        return
    plataforma_inicial = plataformas[0]
    # centralizar cubo horizontalmente sobre a plataforma inicial
    alvo_x = plataforma_inicial.x + (plataforma_inicial.largura - CUBO_LARGURA) // 2
    # garantir que o cubo esteja dentro da tela (clamp)
    alvo_x = max(0, min(alvo_x, TELA_LARGURA - CUBO_LARGURA))
    for cubo in cubos:
        cubo.x = alvo_x
        cubo.y = plataforma_inicial.y - cubo.altura
        cubo.retangulo.topleft = (cubo.x, round(cubo.y))
        cubo.vel = 0
        cubo.em_sobre = True


def main(genomas, config):
    global geracao
    geracao += 1
    if aiJogando:
        redes = []
        lista_genomas = []
        cubos = []
        for _, genoma in genomas:
            rede = neat.nn.FeedForwardNetwork.create(genoma, config)
            redes.append(rede)
            genoma.fitness = 0
            lista_genomas.append(genoma)
            cubos.append(Cubo(CUBO_X, 0))
    else:
        cubos = [Cubo(CUBO_X, 0)]
        lista_genomas = []
        redes = []

    chao = Chao(730)
    fundo = Fundo()
    plataformas = criar_plataformas_iniciais()

    # posicionar cubos corretamente sobre a primeira plataforma (centralizados)
    posicionar_cubos_sobre_plataforma_inicial(cubos, plataformas)

    tela = pygame.display.set_mode((TELA_LARGURA, TELA_ALTURA))
    relogio = pygame.time.Clock()

    pontos = 0
    tempo_inicio = time.time()
    ultimo_seg = 0  # para contar por segundos inteiros

    rodando = True
    while rodando:
        relogio.tick(30)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
                pygame.quit()
                quit()
            if not aiJogando:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_SPACE:
                        for cubo in cubos:
                            cubo.pular()

        if len(cubos) == 0:
            pontos = 0
            ultimo_seg = 0
            tempo_inicio = time.time()
            plataformas = criar_plataformas_iniciais()
            if not aiJogando:
                cubos = [Cubo(CUBO_X, 0)]
                posicionar_cubos_sobre_plataforma_inicial(cubos, plataformas)
            else:
                rodando = False
                break

        # garantir que sempre haja uma "plataforma inicial" visível sob o cubo quando necessário:
        # se a primeira plataforma saiu da tela (x + largura < 0), recomputar plataformas iniciais
        if plataformas and (plataformas[0].x + plataformas[0].largura) < 0:
            plataformas = criar_plataformas_iniciais()
            posicionar_cubos_sobre_plataforma_inicial(cubos, plataformas)

        # escolher índice da plataforma mais próxima à frente do cubo
        indice_plataforma = 0
        if len(plataformas) > 1 and cubos and cubos[0].x > (plataformas[0].x + plataformas[0].largura):
            indice_plataforma = 1

        # mover cubos e IA — iterar de trás para frente para remoções seguras
        for i in range(len(cubos) - 1, -1, -1):
            cubo = cubos[i]
            cubo.mover()

            # resetar flag de estar sobre plataforma; será atualizada ao checar colisões
            cubo.em_sobre = False

            # colisão com chão (perde)
            if cubo.y + cubo.altura > chao.y:
                cubos.pop(i)
                if aiJogando:
                    lista_genomas[i].fitness -= 1
                    lista_genomas.pop(i)
                    redes.pop(i)
                continue

            # colisão com teto
            if cubo.y < 0:
                cubos.pop(i)
                if aiJogando:
                    lista_genomas.pop(i)
                    redes.pop(i)
                continue

            # colisão com plataformas (se estiver descendo ou tocando)
            for p in plataformas:
                if cubo.colidir_com(p):
                    # somente encaixa se vinha de cima (ou estiver muito próximo)
                    if cubo.vel >= 0 and (cubo.y + cubo.altura - cubo.vel) <= p.y + 5:
                        cubo.y = p.y - cubo.altura
                        cubo.vel = 0
                        cubo.retangulo.topleft = (cubo.x, round(cubo.y))
                        cubo.em_sobre = True
                    else:
                        pass

            if aiJogando:
                # inputs: y do cubo, distância X até a plataforma alvo, diferença de altura (cubo.y - plataforma.y), e se está sobre plataforma (0/1)
                if plataformas:
                    alvo = plataformas[indice_plataforma]
                    sobre_flag = 1.0 if cubo.em_sobre else 0.0
                    entrada = (cubo.y, (alvo.x - cubo.x), (cubo.y - alvo.y), sobre_flag)
                else:
                    entrada = (cubo.y, TELA_LARGURA, 0.0, 0.0)
                lista_genomas[i].fitness += 0.01  # pequena recompensa por sobreviver
                output = redes[i].activate(entrada)
                # saída > 0.5 => pular (a função pular já verifica em_sobre)
                if output[0] > 0.5:
                    cubo.pular()

        # mover plataformas e gerar novas quando saírem da tela
        remover = []
        for p in plataformas:
            p.mover()
            if p.x + p.largura < 0:
                remover.append(p)

        if len(remover) > 0:
            for r in remover:
                plataformas.remove(r)
            ultimo_x = plataformas[-1].x if len(plataformas) > 0 else TELA_LARGURA
            novas_x = ultimo_x + random.randrange(200, 250)
            plataformas.append(Plataforma(novas_x, random.randrange(520, 640), largura=random.randrange(80, 140)))

        # mover chão (fundo em movimento)
        chao.mover()
        fundo.mover()

        # atualizar pontuação por tempo (1 ponto por segundo vivo)
        segundos = int(time.time() - tempo_inicio)
        if segundos > ultimo_seg:
            pontos += (segundos - ultimo_seg)
            ultimo_seg = segundos
            if aiJogando:
                for genoma in lista_genomas:
                    genoma.fitness += 1

        global max_pontos
        if pontos > max_pontos:
            max_pontos = pontos
        desenhar_tela(tela, cubos, plataformas, chao, fundo, pontos, tempo_inicio, pontos_max=max_pontos)


def rodar(caminhoConfig):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, caminhoConfig)
    populacao = neat.Population(config)
    populacao.add_reporter(neat.StdOutReporter(True))
    populacao.add_reporter(neat.StatisticsReporter())
    if aiJogando:
        populacao.run(main, 50)
    else:
        main(None, None)


if __name__ == '__main__':
    caminho = os.path.dirname(__file__)
    caminhoConfig = os.path.join(caminho, "config.txt")
    rodar(caminhoConfig)
