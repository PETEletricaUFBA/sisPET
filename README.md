### sisPET  
 
#### Sistema de inscrição via carteirinha do estudante - [PET Elétrica UFPR](http://www.eletrica.ufpr.br/pet)
  
 **Licença:** [Atribuição CC BY](http://creativecommons.org/licenses/by/4.0/)  
 
 obs: este foi meu primeiro projeto feito em Python, então ainda há muito o que consertar.
      
**Dependências:**
 * Testado com Python 2.7.6
 * [Google Spreadsheets Python API](https://github.com/burnash/gspread)
 * [ZBar bar code reader](http://zbar.sourceforge.net/)
 * Banco de dados gerado com o projeto [inscriPET](https://github.com/wsilverio/inscriPET/)
 * Webcam
 * LCD 16x2:
 	* [Adafruit_CharLCD](https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code/tree/master/Adafruit_CharLCD)
 	* Informações: [link](https://learn.adafruit.com/drive-a-16x2-lcd-directly-with-a-raspberry-pi/python-code)
 * [Raspberry Pi](http://www.raspberrypi.org/)
 	* Testado com o [modelo B](http://www.raspberrypi.org/products/model-b/), versão 256MB RAM
 	* Teclas (resistor pulldown):
 		* Tecla Esqueda: BCM 21 (BOARD pin 13)
 		* Tecla Direita: BCM 17 (BOARD pin 11)
 		* Tecla Enter:   BCM 4 (BOARD pin 7)
 		* Tecla ESC:     BCM 22 (BOARD pin 15)

#### Como usar:
 * Substituir os dados do arquivo PET.py
 * Verificar o caminho da webcam:
  
 ```console
$ ls /dev/video*
```  
 * Substituir o endereço da webcam (padrão "/dev/video0") no comando **scanner.init()**,  função **configura_scanner()**.
 * Executar o programa:  
  
 ```console
$ python sisPET.py  
```
