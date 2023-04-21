#!/usr/bin/env python3

import math


class Luottokerros:
    '''Luotettavuuskerros.

    Luottokerros mahdollistaa luotettavan tiedonsiirron toteuttamisen.

    Luottokerros sisältää sekä lähettämisessä että vastaanottamisessa
    tarvittavia metodeita ja CRC 8 -algoritmin toteutuksen.
    Polynomina on x**8 + x**3 + x**2 + x + 1, 
    bittimuodossa 100000111.
    '''

    def __init__(self, soketti, puskurin_koko):
        self.soketti = soketti
        self.puskurin_koko = puskurin_koko
        self.rek = 0  # Siirtorekisterin sisältö.

        # Luotettavan tiedonsiirron toteutukseen liittyviä:
        self.vanhin = 0  
        self.ikkuna = 4  
        self.max = 9  # Sekvenssinumeroiden lukumäärä. Suurin sekvenssinumero
                      # on siis self.max - 1. Tässä voisi olla 256, mutta
                      # käytetään pienempää numeroa harjoituksen vuoksi,
                      # jotta nähdään, miten modulo-aritmetiikka toimii.
                      # Jotta selective repeat toimii, on oltava
                      # ikkuna <= max / 2.


    #############################
    # Muut kuin CRC 8 -metodit. #
    #############################
        
    def laheta(self, lahteva, vastott):
        '''Tavujonomuotoisen datan lähetys.'''
        self.soketti.sendto(lahteva, (vastott[0], vastott[1]))        
    

    def laheta_mjono(self, sekvno, lahteva, vastott):
        '''Paketoi merkkijonomuotoisen datan oikeaan kehysrakenteeseen
        ja lähettää paketin.
        '''
        lahteva = self.valm_paketti(sekvno, lahteva)
        self.laheta(lahteva, vastott)

        
    def valm_paketti(self, sekvno, lahteva):
        '''Valmistelee paketin: lahteva koodataan ja muodostetaan
        kehysrakenteen muotoinen paketti: itse viesti keskelle,
        alkuun sekvenssinumero, loppuun tarkistussumma.
        '''
        # Kasataan paketti: keskelle itse viesti, alkuun sekvenssinumero,
        # loppuun tarkistussumma.
        #
        # Käytännön ongelma on kuitenkin, että jos sekvenssinumero on 0,
        # niin se häviää, kun tavujono muunnetaan kokonaisluvuksi.
        # Se pitää siis lisätä pakettiin uudestaan. Toisaalta pitää
        # varoa, ettei pakettiin lisätä kahta ykköstä.
        #
        # Muodostetaan sekvenssinumerollinen paketti ja lasketaan
        # siitä tarkistussumma:
        lahteva = lahteva.encode('utf8')
        nro = sekvno.to_bytes(length=1, byteorder='big')        
        lahteva_numerollinen = nro + lahteva
        tark = self.laske_tark(lahteva_numerollinen)
        #
        # Sitten liitetään numero, itse viesti ja sekvenssinumerollisesta
        # paketista laskettu tarkistussumma yhteen.
        lahteva = nro + lahteva + tark
        # Välitetään paketti.
        return lahteva


    def pura(self, paketti):
        '''Palauttaa sekvenssinumeron ja datakentän dekoodattuina.'''
        sekvno = paketti[0]  # Kokonaisluku, ei tarvitse enää dekoodata.
        data = paketti[1:-1]  # Tavujono, pitää dekoodata.
        data = data.decode('utf8', errors='ignore')
        return (sekvno, data)


    def onko_ikkunassa(self, alaraja, ylaraja, maksimi, luku):
        '''Palauttaa tiedon siitä, onko annettu luku ikkunan sisällä (vähintään
        alaraja, aidosti pienempi kuin ylaraja), kun modulo maksimi 
        -aritmetiikka otetaan huomioon.'''
        # Periaatteessa vertailuoperaatio on ylärajalle
        #   luku < ylaraja
        # ja alarajalle
        #   luku >= alaraja,
        # mutta modulo-aritmetiikka on otettava huomioon.
        if alaraja <= ylaraja and luku >= alaraja:
            return luku < ylaraja
        elif alaraja <= ylaraja and luku < alaraja:
            return (luku + maksimi < ylaraja and
                    luku + maksimi >= alaraja)
        elif alaraja > ylaraja and luku >= alaraja:
            return luku < ylaraja + maksimi
        else:  # alaraja > ylaraja and luku < alaraja
            return (luku < ylaraja and
                    luku + maksimi >= alaraja)

        
    def tulosta_ikkuna(self):
        '''Tulostaa vastaanotto-/lähetysikkunan.'''
        akkuna = []
        for i in range(self.vanhin, self.vanhin+self.ikkuna):
            akkuna.append(i % self.max)
        print('(Ikkuna on nyt {}.)'.format(akkuna))
        
        
    ##################
    # CRC 8 -metodit #
    ##################

    def tarkasta(self, data, testaus=False):
        '''Suorittaa CRC 8 -tarkastuksen vastaanotetulle datalle.'''
        data = int.from_bytes(data, byteorder='big')
        self.crc8(data, testaus)
        return self.rek == 0
        
        
    def laske_tark(self, data, testaus=False):
        '''Palauttaa CRC 8 -tarkistussumman tavujonona.'''
        data = int.from_bytes(data, byteorder='big')
        data = data << 8  # Kahdeksan nollaa perään.
        self.crc8(data, testaus)  # Lasketaan tarkistussumma.
        return self.rek.to_bytes(length=1, byteorder='big')
        

    def crc8(self, data, testaus=False):
        '''CRC 8 -algoritmin toteutus kokonaislukumuotoiselle datalle.'''
        self.rek = 0

        # Annetaan jokainen bitti erikseen siirtorekisterille.
        pituus = data.bit_length()
        for i in range(pituus, 0, -1):
            bitti = ((1 << i-1) & data) >> i-1  # Bitti kohdassa i-1.
            self.siirtorek(bitti, testaus)
    

    def siirtorek(self, bitti, testaus):
        '''Suorittaa yhden siirtorekisterin askeleen.'''
        if testaus:
            print('Rekisteri ensin: {}\ntuleva bitti: {}'.\
                  format(bin(self.rek), bitti))

        # Bitit.
        bitti7 = (self.rek & 0b10000000) >> 7  # Bitti kohdassa 7.
        bitti1 = (self.rek & 0b10) >> 1  # Bitti kohdassa 1.
        bitti0 = self.rek & 0b1  # Bitti kohdassa 0.

        # Uudet arvot.
        bitti2 = bitti7 ^ bitti1
        bitti1 = bitti7 ^ bitti0
        bitti0 = bitti7 ^ bitti
        uudet = (bitti2 << 2) | (bitti1 << 1) | bitti0  # Yhdistelmä.

        # Laitetaan uudet arvot rekisteriin.
        self.rek = self.rek << 1  # Siirretään bittejä yksi vasemmalle.
        self.rek = self.rek & 0b11111000  # Nollataan vanhat.
        self.rek = self.rek | uudet  # Uudet arvot tilalle.

        if testaus:
            print('Rekisteri jälkeen: {}\n'.format(bin(self.rek)))
        
    
