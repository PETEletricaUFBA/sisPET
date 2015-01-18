#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
    SisPET - Sistema de Inscrição do PET Eng. Elétrica @Universidade Federal do Paraná {eletrica.ufpr.br/pet/}
    autor: Wendeurick Silverio
    repositório original: https://github.com/wsilverio/sisPET
    licença: CC BY - http://creativecommons.org/licenses/
'''

'''
    A FAZER:

        - if __name__ == "__main__"

        - Verificar a lista "A Fazer" do projeto inscriPET

        - Implementar timeout para a leitura do codigo de barras:
            o argumento timeout = X (X: inteiro),
            descrito na documentação não funciona

        - Acentuacao e caracteres invalidos na planilha "Lista de curso"
            ao obter o título dos cursos, caso haja algum caracter
            'inválido' (ã, é, ì, ô, ü, ç), a funcao remove_acentos retorna algo como:
            # UnicodeEncodeError: 'ascii' codec can't encode character u'\xf3' in position 15: ordinal not in range(128)

        - Corrigir o bug do /dev/videoX:
            se o programa for interrompido de forma inesperada,
            o dispositivo /dev/videoX (X: 0, 1, 2, ...) fica
            inacessível

        - Janela do leitor (camera):
            logo que o programa é inicializado
            no modo PC, a janela do leitor é acionada por
            scanner.visible = True

        - Inscrever a pessoa corretamente no curso desejado:
            caso a planilha seja alterada durante a inscrição
            corre o risco de ser cadastrada em um curso diferente

        - Enviar as informações das atividades no e-mail

        - Enxugar a classe Adafruit_CharLCD: ficar somente com o necessário

        - Teste de conexao a internet nos passos "críticos"
            tratar com try/except

        - Teste com dongle usb

        - Try configurar camera

        - script instala dependencias
            criar um script em shell para instalar as dependencias

        Implementar:
        - Prazo para pagamento
            - Expira em X dias, ex. 2
                - Se não pagar limpa a linha da inscrição
                - Envia e-mail informando
            - Lista de espera
            - Quando uma inscrição expirar, enviar e-mail para o próximo na lista de espera

'''

# planilhas, sistema, email, conexão (timeout), scanner
import gspread, os, smtplib, socket, zbar
# função remove_acentos()
from unicodedata import normalize
# delay
from time import sleep
# thread LCD funcao scroll()
from multiprocessing import Process, Queue
# thread WDT-RESET funcao reset()
from threading import Timer
# função teste_de_conexao()
from urllib2 import urlopen
# data e hora
from datetime import datetime
# função enviar_email()
from email.mime.text import MIMEText
# dados do 'usuario' PET.py
from PET import Sis_M, Sis_S, P_M, KEY_BD, KEY_CURSOS

# retorna alguns logs para no modo debug
debug = False

def abrir_planilha_cursos():
    prints("abrir_planilha_cursos")

    teste_de_conexao(True)

    global cliente, planilha_cursos, banco_de_dados, menu, msg
    msg.put(["Abrindo", "Planilhas cursos"])
    try:
        cliente = gspread.login(Sis_M, Sis_S)
    except:
        msg.put(["Erro", "Erro ao fazer login"])
        menu = INICIO
        tecla = ler_teclas()
    else:
        try:
            planilha_cursos = cliente.open_by_key(KEY_CURSOS).get_worksheet(0)
        except:
            print("Erro ao abrir planilha dos cursos. Key = ", KEY_CURSOS)
            msg.put(["Erro", "Erro ao abrir planilha dos cursos"])
            menu = INICIO
            tecla = ler_teclas()
        try:
            banco_de_dados = cliente.open_by_key(KEY_BD).get_worksheet(0)
        except:
            print("Erro ao abrir banco de dados. Key = ", KEY_BD)
            msg.put(["Erro", "Erro ao abrir banco de dados"])
            menu = INICIO
            tecla = ler_teclas()
    msg.put(["Verificando", "Cursos"])
    verifica_cursos()


def verifica_cursos():  #https://docs.python.org/2/library/sched.html#module-sched
    prints("verifica_cursos")

    teste_de_conexao()

    global CURSOS, menu, msg
    CURSOS = []  # inicializa como lista

    i = 4
    while True:
        try:
            titulo = planilha_cursos.cell(i, 1).value  # obtém o título do curso (coluna 1)
        except:
            print "Erro ao verificar cursos"
            msg.put(["Erro", "Erro ao verificar cursos"])
            menu = INICIO
            tecla = ler_teclas()
        else:
            if not titulo:
                break
            else:
                CURSOS.append(titulo)
                i += 1

                #Timer(180, verifica_cursos, ()).start() # chama a função verifica_cursos() a cada 3 min (180 s)


def ler_teclas():
    prints("ler_teclas")
    global isRasp, wdt

    wdt.cancel()
    sleep(0.01) # wdt.is_alive()
    wdt = Timer(intervalo, reset) # wdt 3min
    wdt.start()

    _tecla = -1

    if isRasp == True:
        global BOTAO_ESQUERDA, BOTAO_DIREITA, BOTAO_ENTER, BOTAO_ESC, GPIO
        debouncing = 0.05
        while (_tecla == -1) and wdt.is_alive():
            if GPIO.input(BOTAO_ESQUERDA):
                print "Esquerda"
                _tecla = ESQ
                sleep(debouncing)
                while GPIO.input(BOTAO_ESQUERDA): pass
            elif GPIO.input(BOTAO_DIREITA):
                print "Direita"
                _tecla = DIR
                sleep(debouncing)
                while GPIO.input(BOTAO_DIREITA): pass
            elif GPIO.input(BOTAO_ENTER):
                print "Enter"
                _tecla = ENTER
                sleep(debouncing)
                while GPIO.input(BOTAO_ENTER): pass
            elif GPIO.input(BOTAO_ESC):
                print "Esc"
                _tecla = ESC
                sleep(debouncing)
                while GPIO.input(BOTAO_ESC): pass
            sleep(debouncing)

    else:
        while (_tecla == -1):
            tc = str(raw_input("Tecla: ")).lower()
            if tc == 'a': # esc
                _tecla = 2
            elif tc == 's': # esquerda
                _tecla = 0
            elif tc == 'd': # direita
                _tecla = 1
            elif tc == 'f': # enter
                _tecla = 3

    wdt.cancel()
    sleep(0.01)
    wdt = Timer(intervalo, reset) # wdt 3min
    wdt.start()

    #print "TECLA: ", _tecla

    return _tecla


def constrain(var, _min, _max):
    prints("constrain")
    if var < _min:
        var = _max
    elif var > _max:
        var = _min
    # return max(min(_max, var), _min)
    return var


def configura_scanner():
    prints("configura_scanner")
    global scanner, isRasp, msg
    msg.put(["Configurando", "Camera"])
    # cria um "Processor" do zbar
    scanner = zbar.Processor()
    scanner.parse_config('enable')

    # Processor em video'i'
    disp = "/dev/video1"
    scanner.init(disp)

    if isRasp:
        scanner.visible = False
    else:
        scanner.visible = True

    # zbar.X11DisplayError: ERROR: zbar processor in _zbar_processor_open():\n'
    # X11 display error: unable to open X display\n'

    # zbar.UnsupportedError  zbar.SystemError ?
    # visualização desabilitada ------------------------------


def ler_codigo_barras():
    prints("ler_codigo_barras")
    ##### ARRUMA: LER APENAS O 1º CÓD BAR
    scanner.process_one()
    for codigo in scanner.results:
        return str(codigo.data)


def configura_Rpi():
    prints("configura_Rpi")
    global isRasp, lcd, GPIO
    global BOTAO_ESQUERDA, BOTAO_DIREITA, BOTAO_ENTER, BOTAO_ESC
    isRasp = True
    '''
    Botoes conectados nos pinos:
    BCM 4 = BOARD pin 7
    BCM 17 = BOARD pin 11
    BCM 21 = BOARD pin 13
    BCM 22 = BOARD pin 15
    '''
    BOTAO_ESQUERDA = 21
    BOTAO_DIREITA = 17
    BOTAO_ENTER = 4
    BOTAO_ESC = 22

    try:
        # raspberry pi
        import RPi.GPIO as GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        # LCD
        from Adafruit_CharLCD import Adafruit_CharLCD
        lcd = Adafruit_CharLCD()
        lcd.begin(16, 2)
        # I/O botoes
        GPIO.setup(BOTAO_ESQUERDA, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(BOTAO_DIREITA, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(BOTAO_ENTER, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(BOTAO_ESC, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    except RuntimeError: # caso o programa na esteja sendo executado em um RPi
        isRasp = False


def scroll(m):
    prints("scroll")
    global isRasp

    if isRasp == True:
        texto = ["", ""]
        i = j = imax = jmax = 0  # posicao da "sub-string" das linhas de cima e de baixo, respectivamente
        cont = 0

        while m.empty(): pass

        while True:
            if not m.empty():
                texto = m.get()

                texto[0] = remove_acentos(texto[0])
                texto[1] = remove_acentos(texto[1])

                if (len(texto[0]) <= 16):
                    lcd.home()
                    lcd.message(texto[0].center(16))
                else:
                    texto[0] = " " * 16 + texto[0] + " " * 16
                    i = 0
                    imax = len(texto[0]) - 16

                if (len(texto[1]) <= 16):
                    lcd.setCursor(0, 1)
                    lcd.message(texto[1].center(16))
                else:
                    texto[1] = " " * 16 + texto[1] + " " * 16
                    j = 0
                    jmax = len(texto[1]) - 16

            if (len(texto[0]) > 16) and not (cont % 2):  # i
                lcd.home()
                sub_string = texto[0][i:i + 16]
                lcd.message(sub_string)
                i += 1
                if (i >= imax): i = 0

            if (len(texto[1]) > 16):  # j
                lcd.setCursor(0, 1)
                sub_string = texto[1][j:j + 16]
                lcd.message(sub_string)
                j += 1
                if (j >= jmax): j = 0

            sleep(0.1)
            cont += 1

    else:
        texto = ["", ""]

        while m.empty(): pass

        while True:
            if not m.empty():
                texto = m.get()

                texto[0] = remove_acentos(texto[0])
                texto[1] = remove_acentos(texto[1])
                print texto[0] + "\n" + texto[1]


def remove_acentos(txt):
    # prints("remove_acentos")
    # Substitui os caracteres por seus equivalentes "sem acento"
    return normalize('NFKD', txt.decode('utf-8')).encode('ASCII', 'ignore')


def reset():
    prints("reset")
    global menu
    menu = INICIO
    teste_de_conexao(True)


def prints(funcao):
    global menu
    if debug:
        print "\n--------------\n" + funcao + "()"
        if menu == INICIO:
            print "menu: INICIO\n" + "--------------\n"
        elif menu == NAVEGA_CURSOS:
            print "menu: NAVEGA_CURSOS\n" + "--------------\n"
        elif menu == INFORMACOES_CURSO:
            print "menu: INFORMACOES_CURSO\n" + "--------------\n"
        elif menu == LER_CARTEIRINHA:
            print "menu: LER_CARTEIRINHA\n" + "--------------\n"
        elif menu == INSCREVER:
            print "menu: INSCREVER\n" + "--------------\n"
        else:
            print "menu: ERRO{" + menu + "}\n--------------\n"


def envia_email(dados):

    teste_de_conexao(True)

    global wdt
    wdt.cancel()

    # dados: [hora, nome, grr, curso, periodo, email, fone, curso]

    nome = dados[1].split(' ')[0]  # obtém o primeiro nome
    destinatario = dados[5]
    atividade = dados[7]

    # corpo do email
    # enviar data e hora das atividades
    msg = MIMEText("Olá %s,\n"
                   "\nVocê se inscreveu para: %s."

                   "\nEm caso de atividade custeada, verifique o pagamento com o PET.\n\n"

                   "\nEsta é uma mensagem automática.\n"
                   "\nGrupo PET Engenharia Elétrica"
                   "\nUniversidade Federal do Paraná"
                   "\n(41) 3361-3225"
                   "\nwww.eletrica.ufpr.br/pet" % (nome, atividade))

    msg['Subject'] = 'sisPET - %s' % atividade
    msg['From'] = P_M
    msg['To'] = destinatario

    # servidor SMTP do GMAIL
    #print("Identificando servidor SMTP")
    mailServer = smtplib.SMTP('smtp.gmail.com', 587)
    # identificação de cliente
    #print("Identificando cliente")
    mailServer.ehlo()
    # criptografia tls
    #print("Criando conexão criptografada")
    mailServer.starttls()
    # identificação com conexão criptografada
    #print("Identificando conexão criptografada")
    mailServer.ehlo()

    try:
        print("Efetuando login")
        mailServer.login(Sis_M.replace('@gmail.com', ''), Sis_S)  # login com o nome de usuário
        print("Enviando email...")
        mailServer.sendmail(P_M, destinatario, msg.as_string())
        print("\nEmail enviado para %s" % destinatario)
    except:
        print("Erro ao enviar email")

    wdt = Timer(intervalo, reset) # wdt 3min
    mailServer.close()


def teste_de_conexao(erro = False):
    prints("teste_de_conexao")
    socket.setdefaulttimeout(4)
    try :
        r = urlopen("http://ufpr.br")
        #print "conexão ok"
    except:
        print "erro conexão"
        if erro == True:
            global msg
            msg.put(["Erro", "Sem conexão com a internet"])
        sleep(1)
        exit()
        teste_de_conexao()


#-- def constantes --#
# MENU:
INICIO = 0
NAVEGA_CURSOS = 1
INFORMACOES_CURSO = 2
LER_CARTEIRINHA = 3
INSCREVER = 4

# TECLAS:
ESQ = 0
DIR = 1
ESC = 2
ENTER = 3

#-- início do programa --#
os.system('clear') # limpa o console
print "*** sisPET ***"

menu = INICIO

configura_Rpi()

msg = Queue()
p = Process(target=scroll, args=(msg,))
p.start()

configura_scanner()
abrir_planilha_cursos()

# GLOBAIS
indice = 0
tecla = -1
i = 0

intervalo = 180 # 3 min
wdt = Timer(intervalo, reset) # wdt 3min

try:
    while True:
        #print "while true"
        if menu == INICIO:
            prints("if menu == INICIO")

            msg.put(["sisPET", "Pressione qualquer tecla"])

            tecla = -1
            while tecla == -1:
                tecla = ler_teclas()

            menu = NAVEGA_CURSOS
            indice = 0
            msg.put(["Lista de cursos", "Aguarde"])
            verifica_cursos()

        elif menu == NAVEGA_CURSOS:
            prints("elif menu == NAVEGA_CURSOS")
            if len(CURSOS) > 0:
                msg.put(["Disponíveis:%d/%d" %(indice+1, len(CURSOS)), str(CURSOS[indice])]) # arrumar nenhum disponivel
            else:
                msg.put(["Erro", "Nenhuma atividade disponivel"])
                delay(5)
                menu = INICIO
                continue # retorna ao loop principal

            tecla = ler_teclas()

            if tecla == -1:
                menu = INICIO
                continue # retorna ao loop principal
            elif tecla == ESQ:
                indice -= 1
            elif tecla == DIR:
                indice += 1
            elif tecla == ESC:
                menu = INICIO
            elif tecla == ENTER:
                menu = INFORMACOES_CURSO

            indice = constrain(indice, 0, len(CURSOS) - 1)

        elif menu == INFORMACOES_CURSO:
            prints("elif menu == INFORMACOES_CURSO")

            teste_de_conexao(True)

            INFOS = planilha_cursos.range('A' + str(indice + 4) + ':I' + str(indice + 4))

            #print INFOS

            for celula in INFOS:
                celula.value = celula.value.encode('utf-8')

            titulo = str(INFOS[0].value)
            vagas =  INFOS[3].value
            periodo = "De " + INFOS[4].value[0:5] + " a " + INFOS[5].value[0:5]
            dias = INFOS[6].value.upper() + ": das " + INFOS[7].value[0:5] + " às " + INFOS[8].value[0:5]

            msg.put([(str(titulo)[0:16-2]+"..") if len(titulo) > 16 else str(titulo), "vagas: " + str(vagas) + " - " + str(periodo) + " - " + str(dias)])

            tecla = ler_teclas()

            if tecla == -1:
                menu = INICIO
                continue # retorna ao loop principal
            elif tecla == ESQ:
                menu = NAVEGA_CURSOS
                indice -= 1
                # verifica_cursos()
            elif tecla == DIR:
                menu = NAVEGA_CURSOS
                indice += 1
                # verifica_cursos()
            elif tecla == ESC:
                menu = NAVEGA_CURSOS
                indice = 0
                verifica_cursos()
            elif tecla == ENTER:
                menu = LER_CARTEIRINHA

            indice = constrain(indice, 0, len(CURSOS) - 1)

        elif menu == LER_CARTEIRINHA:
            prints("elif menu == LER_CARTEIRINHA")
            global COD, isRasp
            COD = ""
            while True:
                msg.put(["Carteirinha", "Posicione o código de barras em frente à camera"])
                #wdt.cancel()
                sleep(0.05) # ??? a msg demorava a aparecer quando a funcao ler_codigo_barras() era chamada logo adiante
                COD = ler_codigo_barras()  # código de barras # TENTAR UM TIMEOUT
                #print "retornou"
                #wdt = Timer(intervalo, reset) # wdt 3min
                #wdt.start()
                if COD.isdigit() and len(COD) == 12:
                    print "Carteirinha: %s" % COD
                    menu = INSCREVER
                    break
                else:
                    #print COD
                    msg.put(["Erro de leitura", "Tente novamente"])
                    sleep(2)

            if menu != INSCREVER:
                tecla = ler_teclas()

                if tecla == -1:
                    menu = INICIO
                    continue # retorna ao loop principal
                elif tecla == ESC:
                    menu = INFORMACOES_CURSO

        elif menu == INSCREVER:
            prints("elif menu == INSCREVER")
            try:
                global DADOS
                teste_de_conexao(True)

                aluno = banco_de_dados.find(COD)
                DADOS = banco_de_dados.range('C' + str(aluno.row) + ':H' + str(aluno.row))

                for i in xrange(len(DADOS)):
                    DADOS[i] = DADOS[i].value

            except gspread.exceptions.CellNotFound:
                msg.put(["Erro", "Aluno não cadastrado. Dirija-se à sala do PET."])
                tecla = ler_teclas()
                menu = INICIO
                continue # retorna ao menu principal

            msg.put(["Confirma?", str(DADOS[0])]) # nome do aluno

            tecla = ler_teclas()

            if tecla == -1:
                menu = INICIO
                continue # retorna ao loop principal
            elif tecla != ENTER:
                msg.put(["Erro de identificação", "Digija-se à sala do PET"])
                sleep(10)
                menu = INICIO
                continue # retorna ao loop principal
            else:
                msg.put(["Processando", "Aguarde"])

            url = planilha_cursos.cell(indice + 4, 10).value  # 10 = coluna J
            planilha_inscricao = cliente.open_by_url(url).get_worksheet(0)

            try:
                ja_cadastrado = planilha_inscricao.find(DADOS[1])  # busca pelo GRR
                msg.put(["Erro", "GRR já cadastrado nesta atividade"])
                tecla = ler_teclas()
                menu = INICIO
                continue # volta para o loop principal

            except gspread.exceptions.CellNotFound:
                i = 2  # índice que correrá a planilha. começa em 2 porque a primeira linha é o cabeçalho
                while True:
                    if not planilha_inscricao.cell(i, 1).value:  # celula == None
                        break  # 'i' contém o índice da linha em branco
                    i += 1  # percorre a planilha linha a linha

            if menu != NAVEGA_CURSOS: # caso não tenha dado erro
                msg.put(["Cadastrando", "Aguarde"])
                t = datetime.now()
                HORA = str(str(t.day) + '/' + str(t.month) + '/' + str(t.year) +
                        ' ' + str(t.hour) + ':' + str(t.minute) + ':' + str(t.second))

                DADOS.insert(0, HORA)

                i = 2
                while True:
                    if not planilha_inscricao.cell(i, 1).value:  # celula == None
                        break
                    i += 1

                celulas_atualizar = planilha_inscricao.range('A' + str(i) + ':G' + str(i))

                i = 0
                for cell in celulas_atualizar:
                    cell.value = DADOS[i]
                    i += 1

                planilha_inscricao.update_cells(celulas_atualizar)

                sleep(3)

                msg.put(["Obrigado", "Valores atualizados"])

                DADOS.append(str(CURSOS[indice])) # adiciona o nome do curso aos dados, para enviar o email

                envia_email(DADOS)
                menu = INICIO
                sleep(5)

# Pycharm
except KeyboardInterrupt:
    sleep(0.01)
    wdt.cancel()
    sleep(0.01)
    wdt.cancel()
    sleep(0.01)
    exit()