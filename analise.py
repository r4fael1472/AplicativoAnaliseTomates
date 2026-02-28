
import cv2
import numpy as np
import math

class AnaliseTomate:
    def __init__(self):
        self.baixo_vermelho1 = np.array([0, 70, 40]) #DEFINE OS LIMITES INFERIORES DO HSV
        self.alto_vermelho1 = np.array([10, 255, 255]) #DEFINE OS LIMITES SUPERIORES DO HSV
        self.baixo_vermelho2 = np.array([160, 70, 40]) #DEFINE OS LIMITES INFERIORES DO HSV
        self.alto_vermelho2 = np.array([179, 255, 255]) #DEFINE OS LIMITES SUPERIORES DO HSV

        self.kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        self.kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))

    def segmentacao(self, img):
        blur = cv2.GaussianBlur(img, (7, 7), 0)
        hsv_img = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV) #CONVERTE A IMAGEM DE BGR PARA HSV

        mascara1 = cv2.inRange(hsv_img, self.baixo_vermelho1, self.alto_vermelho1) #FAZ UMA VARREDURA NA MATRIZ MARCANDO OS PIXELS DENTRO DO LIMITE COMO BRANCOS E OS FORA COMO PRETOS
        mascara2 = cv2.inRange(hsv_img, self.baixo_vermelho2, self.alto_vermelho2) #FAZ UMA VARREDURA NA MATRIZ MARCANDO OS PIXELS DENTRO DO LIMITE COMO BRANCOS E OS FORA COMO PRETOS
        mascara = mascara1 + mascara2

        #OPERAÇÕES MORFOLÓGICAS (POLIMENTO)
        kernel_dilatacao = np.ones((3, 3), np.uint8) # DILATAÇÃO SUAVE NO KERNEL
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21,21)) #CRIAÇÃO DO KERNEL
        mascara_limpa = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel) #APLICAR OPENING PARA REMOVER RUÍDO DO FUNDO
        mascara_expandida = cv2.dilate(mascara_limpa, kernel_dilatacao, iterations=2) # EXPANSÃO PARA OBTER BORDA PERDIDA
        mascara_final = cv2.morphologyEx(mascara_expandida, cv2.MORPH_CLOSE, kernel) #APLICAR CLOSING PARA TAPAR BURACOS DENTRO DO TOMATE

        #img_recortada = cv2.bitwise_and(img, img, mask=mascara_final) #COMPARA A IMAGEM ORIGINAL COM A MASCARA CRIADA
        #cv2.imshow("Verificacao", img_recortada) #JANELA DE EXIBIÇÃO DA IMAGEM
        #cv2.waitKey(0) #MANTÉM A JANELA ABERTA ATÉ QUE UMA TECLA SEJA PRECIONADA
        #cv2.destroyAllWindows() #GARANTE QUE AS JANELAS NÃO FIQUEM TRAVADAS NO SISTEMA
        return mascara_final

    def buscarContornos(self, img, mascara):
        contornos, hierarquia = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) #RETR_EXTERNAL (FOCO NA BORDA EXTERNA), CHAIN_APPROX_SIMPLE (SALVA APENAS OS PONTOS ESSENCIAIS DA BORDA)
        maior_contorno = max(contornos, key=cv2.contourArea) #BUSCA O MAIOR CONTORNO OBTIDO
        (x, y), raio_px = cv2.minEnclosingCircle(maior_contorno) #MENOR CÍRCULO QUE CONSEGUE COLORIR O CONTORNO COMPLETO
        x, y, w_px, h_px = cv2.boundingRect(maior_contorno)
        #cnt = cv2.drawContours(img, contornos, -1, (0, 255, 0), 2) #VERIFICAR SE O TOMATE ESTÁ SENDO "ENXERGADO" POR COMPLETO
        cnt = cv2.rectangle(img, (x, y), (x + w_px, y + h_px), (255, 0, 0), 2)

        return maior_contorno, x, y, w_px, h_px

    def calibracao(self, diametro_real_referencia_mm, diametro_px_referencia):
        ppm = diametro_px_referencia / diametro_real_referencia_mm #PIXELS POR MM
        return ppm

    def propFisicas(self, mascara, x, y, w_px, h_px, ppm):
        largura_cm = (w_px / ppm) / 10
        altura_cm = (h_px / ppm) / 10

        D1 = largura_cm
        D2 = largura_cm
        H = altura_cm

        # PROPRIEDADES FÍSICAS AGRONÔMICAS
        Dg = (H * D1 * D2) ** (1/3)
        Da = (H * D1 * D2) / 3
        Es = Dg / H
        As = math.pi * (Dg ** 2)

        # CÁLCULO DO VOLUME
        volume_total = 0
        altura_pixel_cm = (1 / ppm) / 10 # Altura de cada "fatia" (1 pixel) em cm

        for linha in range(y, y + h_px - 1):
            # encontrar onde o tomate começa e termina nesta linha horizontal
            pixels_atual = np.where(mascara[linha, x:x+w_px] == 255)[0]
            pixels_prox = np.where(mascara[linha+1, x:x+w_px] == 255)[0]

            # Se houver tomate nas duas linhas, calculamos o disco
            if len(pixels_atual) > 0 and len(pixels_prox) > 0:
                # O diâmetro do disco é a distância do primeiro ao último pixel branco
                diam_px_atual = pixels_atual[-1] - pixels_atual[0]
                diam_px_prox = pixels_prox[-1] - pixels_prox[0]

                # Converte os diâmetros da fatia para cm
                diam_cm_atual = (diam_px_atual / ppm) / 10
                diam_cm_prox = (diam_px_prox / ppm) / 10

                # Áreas dos círculos do disco atual e do próximo
                area1 = math.pi * ((diam_cm_atual / 2) ** 2)
                area2 = math.pi * ((diam_cm_prox / 2) ** 2)

                # Média da área vezes a altura da fatia (Integração)
                area_media = (area1 + area2) / 2
                volume_total += area_media * altura_pixel_cm

        return {
            "Largura_cm": largura_cm,
            "Altura_cm": altura_cm,
            "Diam_Geometrico": Dg,
            "Diam_Aritmetico": Da,
            "Esfericidade": Es,
            "Area_Superficial": As,
            "Volume_cm3": volume_total
        }





